import os
import json
import random
import requests
import argparse

from pathlib import Path
from console import green, green_bold, cyan, red, yellow
from starknet_py.contract import Contract
from starknet_py.net import AccountClient, KeyPair
from starkware.crypto.signature.signature import sign
from starknet_py.net.client import Client, InvokeFunction
from starknet_py.net.models import StarknetChainId
from starkware.python.utils import from_bytes
from starkware.starknet.public.abi import get_selector_from_name
from starkware.starknet.core.os.transaction_hash.transaction_hash import TransactionHashPrefix, calculate_transaction_hash_common

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNT_FILE = os.path.join(ROOT_DIR, 'account.json')
HINTS_FILE = os.path.join(ROOT_DIR, 'hints.json')
TESTNET_ID = from_bytes(b"SN_GOERLI")
PAYDAY = get_selector_from_name("payday")
SUBMIT_TX = get_selector_from_name("submit")

with open(HINTS_FILE, "r") as f:
  data = json.load(f)

def invoke_tx_hash(addr, calldata):
    exec_selector = get_selector_from_name("__execute__")
    return calculate_transaction_hash_common(
        tx_hash_prefix=TransactionHashPrefix.INVOKE,
        version=data['VERSION'],
        contract_address=addr,
        entry_point_selector=exec_selector,
        calldata=calldata,
        max_fee=data['MAX_FEE'],
        chain_id=TESTNET_ID,
        additional_data=[],
    )

async def print_n_wait(client: Client, invocation: InvokeFunction):
    try:
        await invocation.wait_for_acceptance()
    except Exception as e:
        red.print(f"Transaction Hash: {invocation.hash}")
        red.print("Invocation error:")
        red.print(f"{e}")
        red.print("")

    res = await client.get_transaction_receipt(invocation.hash)

    if "ACCEPT" in str(res.status):
        green.print(f"Transaction Hash: {invocation.hash}")
        green.print(f"Tx Results: {res.status}")
        for ev in res.events:
            if ev.keys[0] == SUBMIT_TX and len(res.events) == 1:
                return ev.data
            if ev.keys[0] == PAYDAY:
                green_bold.print(f"Payday Results: PAYDAY!!!\n")
                return ev.data
        yellow.print("Payday Results: no payday\n")

    else:
        red.print(f"Tx Results: {res.status}")
    
async def deploy_account(client, contract_path="", constructor_args=[], additional_data=None):
    cache_data = dict()
    CONTRACT_ADDRESS="{}".format(contract_path)
    if additional_data:
        CONTRACT_ADDRESS="{}_{}".format(CONTRACT_ADDRESS, additional_data)
    if os.getenv('ACCOUNT_CACHE') == "false":
        yellow.print("Disabled local account cache\n")
    else:
        with open(ACCOUNT_FILE) as json_file:
            cache_data = json.load(json_file)
            if CONTRACT_ADDRESS in cache_data[client.net]:
                cyan.print(f"Found local contract: {cache_data[client.net][CONTRACT_ADDRESS]}\n")
                
                cached = await Contract.from_address(int(cache_data[client.net][CONTRACT_ADDRESS], 16), client, True)
                return cached, int(cache_data[client.net][CONTRACT_ADDRESS], 16)

    os.system("starknet-compile --account_contract {}.cairo --output {}_compiled.json".format(contract_path, contract_path, contract_path))

    rand = random.randint(0, data['PRIVATE_KEY'])
    compiled = Path("{}_compiled.json".format(contract_path)).read_text()
    deployment_result = await Contract.deploy(
        client, compiled_contract=compiled, constructor_args=constructor_args, salt=rand
    )
    os.system("rm {}_compiled.json".format(contract_path))

    if not deployment_result.hash:
        print("\u001b[31mFailed to deploy contract\u001b[0m\n")
        raise ValueError("Failed to deploy contract")
        return "", ""

    cyan.print("Deployment Initialized: ", deployment_result.hash)
    cyan.print("\tWaiting for successful deployment...")
    cyan.print("\tPatience is bitter, but its fruit is sweet...")

    await client.wait_for_tx(deployment_result.hash)
    res = await client.get_transaction(deployment_result.hash)

    if os.getenv('ACCOUNT_CACHE') != "false":
        cache_data[client.net][CONTRACT_ADDRESS] = "0x{:02x}".format(res.transaction.contract_address)
        with open(ACCOUNT_FILE, 'w') as outfile:
            json.dump(cache_data, outfile, sort_keys=True, indent=4)
        cyan.print("\tSuccess - cached in accounts.json")

    print("\u001b[0m\n")

    return deployment_result.deployed_contract, res.transaction.contract_address

async def contract_cache_check(client, contract):
    with open(ACCOUNT_FILE) as outfile:
        acc_data = json.load(outfile)

    if contract in acc_data[client.net]:
        cached_addr = int(acc_data[client.net][contract], 16)
        cached = await Contract.from_address(cached_addr, client, True)
        return True, cached, cached_addr

    return False, "", ""

async def compile_deploy(client, contract="", args=[], salt=0):
    hit, cached, cached_addr = await contract_cache_check(client, contract)
    if hit:
        return cached, cached_addr

    compiled = "{}_compiled.json".format(contract)
    os.system("starknet-compile {}.cairo --output {}".format(contract, compiled))
    deployment_result = await Contract.deploy(client=client, compiled_contract=Path(compiled).read_text(), constructor_args=args, salt=salt)
    os.system("rm {}".format(compiled))

    await client.wait_for_tx(deployment_result.hash)
    res = await client.get_transaction(deployment_result.hash)

    contract_cache(client.net, contract, res.transaction.contract_address)

    return deployment_result.deployed_contract, res.transaction.contract_address

async def fund_account(toAddr):
    acc_client, acc_addr = get_account_client()
    if "testnet" in acc_client.net:
        bal = await acc_client.get_balance(data['TESTNET_ETH'])
        if bal < data['TRANSFER_AMOUNT']:
            return ""

        nonce_payload = data['NONCE_PAYLOAD']
        nonce_payload['contract_address'] = "0x{:x}".format(acc_addr)
        nonce_resp = requests.request("POST", data['GOERLI_URL']+"/feeder_gateway/call_contract", data=json.dumps(nonce_payload, indent=4))
        nonce = int(nonce_resp.json()['result'][0], 16)

        pay = data['FUNDING_PAYLOAD']
        calldata=[1, data['TESTNET_ETH'], get_selector_from_name('transfer'), 0, 3, 3, toAddr, data['TRANSFER_AMOUNT'], 0, nonce]
        hash = invoke_tx_hash(data['TESTNET_ACCOUNT']['ADDRESS'], calldata)
        (sig_r, sig_s) = sign(hash, data['TESTNET_ACCOUNT']['PRIVATE'])
        pay['signature'] = [str(sig_r), str(sig_s)] 
        pay['calldata'] = [str(i) for i in calldata]
        pay['contract_address'] = "0x{:x}".format(data['TESTNET_ACCOUNT']['ADDRESS'])
        pay['max_fee'] = "0x{:x}".format(data['MAX_FEE'])
        
        resp = requests.request("POST", data['GOERLI_URL']+"/gateway/add_transaction", data=json.dumps(pay, indent=4))
        await acc_client.wait_for_tx(resp.json()['transaction_hash'])

        return data['TESTNET_ACCOUNT']['ADDRESS']

    else:
        bal = await acc_client.get_balance(data['DEVNET_ETH'])
        if bal < data['TRANSFER_AMOUNT']:
            return ""
            
        eth_contract = await Contract.from_address(data['DEVNET_ETH'], acc_client, False)
        await(
            await eth_contract.functions['transfer'].invoke(toAddr, data['TRANSFER_AMOUNT'], max_fee=data['MAX_FEE'])
        ).wait_for_acceptance()

        return data['DEVNET_ACCOUNT']['ADDRESS']

async def get_evaluator(client):
    _, evaluator, evaluator_address = await contract_cache_check(client, data['EVALUATOR'])
    if evaluator_address == "": 
        red.print("must have a deployed evaluator to test against:")
        red.print("'python3 evaluator.py'")
        return "", ""
    return evaluator, evaluator_address

def contract_cache(env, contract, addr):
    acc_data = dict()
    with open(ACCOUNT_FILE) as json_file:
        acc_data = json.load(json_file)
    
    with open(ACCOUNT_FILE, 'w') as outfile:
        acc_data[env][contract] = "0x{:02x}".format(addr)
        json.dump(acc_data, outfile, sort_keys=True, indent=4)

def get_client():
    parser = argparse.ArgumentParser()
    parser.add_argument('--testnet', action='store_true')
    args = parser.parse_args()

    if args.testnet:
        return Client("testnet")
    else:
        return Client(net=data['DEVNET_URL'], chain="testnet")

def get_account_client():
    parser = argparse.ArgumentParser()
    parser.add_argument('--testnet', action='store_true')
    args = parser.parse_args()

    if args.testnet:
        addr = data['TESTNET_ACCOUNT']['ADDRESS']
        acc_client = AccountClient(
            address=addr,
            key_pair=KeyPair(data['TESTNET_ACCOUNT']['PRIVATE'], data['TESTNET_ACCOUNT']['PUBLIC']),
            net="testnet",
            chain=StarknetChainId.TESTNET)
        
        return acc_client, addr

    else:
        addr = data['DEVNET_ACCOUNT']['ADDRESS']
        acc_client = AccountClient(
            address=addr,
            key_pair=KeyPair(data['DEVNET_ACCOUNT']['PRIVATE'], data['DEVNET_ACCOUNT']['PUBLIC']),
            net=data['DEVNET_URL'],
            chain=StarknetChainId.TESTNET)
        
        return acc_client, addr

def devnet_height_check():
    parser = argparse.ArgumentParser()
    parser.add_argument('--testnet', action='store_true')
    args = parser.parse_args()
    if args.testnet:
        red.print("evaluator only needs to be deployed to devnet")
        return

    height = data['DEVNET_URL']+"/feeder_gateway/get_block?blockNumber=latest"
    response = requests.request("GET", height).json()

    if 'message' in response:
        if 'no blocks so far' in response['message']:
            with open(ACCOUNT_FILE) as json_file:
                acc_data = json.load(json_file)

            with open(ACCOUNT_FILE, 'w') as outfile:
                acc_data[data['DEVNET_URL']] = {}
                json.dump(acc_data, outfile, sort_keys=True, indent=4)
