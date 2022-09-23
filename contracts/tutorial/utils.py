import os
import sys
import json
import random
import requests
import argparse

sys.path.append('./')

from pathlib import Path
from console import green, green_bold, cyan, red, yellow
from starknet_py.contract import Contract
from starknet_py.net import AccountClient, KeyPair
from starkware.crypto.signature.signature import sign
from starknet_py.net.client import Client, InvokeFunction
from starknet_py.net.gateway_client import GatewayClient
from starknet_py.net.models import StarknetChainId
from starkware.python.utils import from_bytes
from starkware.starknet.public.abi import get_selector_from_name
from starkware.starknet.core.os.transaction_hash.transaction_hash import TransactionHashPrefix, calculate_transaction_hash_common

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNT_FILE = os.path.join(ROOT_DIR, '../account.json')
CONFIG_FILE = os.path.join(ROOT_DIR, '../config.json')
TESTNET_ID = from_bytes(b"SN_GOERLI")
PAYDAY = get_selector_from_name("payday")
SUBMIT_TX = get_selector_from_name("submit")

with open(CONFIG_FILE, "r") as f:
  data = json.load(f)

parser = argparse.ArgumentParser()
parser.add_argument('--testnet', action='store_true')
args = parser.parse_args()

def invoke_tx_hash(addr, calldata, nonce, selector=0):
    exec_selector = get_selector_from_name("__execute__")
    return calculate_transaction_hash_common(
        tx_hash_prefix=TransactionHashPrefix.INVOKE,
        version=data['VERSION'],
        contract_address=addr,
        entry_point_selector=selector,
        calldata=calldata,
        max_fee=data['MAX_FEE'],
        chain_id=TESTNET_ID,
        additional_data=[nonce],
    )

async def print_n_wait(client, sent_tx_response):
    try:
        await client.wait_for_tx(sent_tx_response.transaction_hash)
    except Exception as e:
        red.print(f"Transaction Hash: 0x{hex(sent_tx_response.transaction_hash)}")
        red.print("Invocation error:")
        red.print(f"{e}")
        red.print("")

    res = await client.get_transaction_receipt(sent_tx_response.transaction_hash)

    if "ACCEPT" in str(res.status):
        green.print(f"Transaction Hash: 0x{hex(sent_tx_response.transaction_hash)}")
        green.print(f"Tx Results: {res.status}")
        for ev in res.events:
            if ev.keys[0] == SUBMIT_TX:
                return ev.data
            if ev.keys[0] == PAYDAY:
                green_bold.print(f"Payday Results: PAYDAY!!!\n")
                return ev.data
        yellow.print("Payday Results: no payday\n")

    else:
        red.print(f"Tx Results: {res.status}")
    
async def contract_cache_check(client, contract):
    with open(ACCOUNT_FILE) as outfile:
        acc_data = json.load(outfile)

    if contract in acc_data[client.net]:
        cached_addr = int(acc_data[client.net][contract], 16)
        cached = await Contract.from_address(cached_addr, client, True)
        return True, cached, cached_addr

    return False, "", ""

def contract_cache(env, contract, addr):
    acc_data = dict()
    with open(ACCOUNT_FILE) as json_file:
        acc_data = json.load(json_file)
    
    with open(ACCOUNT_FILE, 'w') as outfile:
        acc_data[env][contract] = "0x{:02x}".format(addr)
        json.dump(acc_data, outfile, sort_keys=True, indent=4)

async def compile_deploy(client, contract="", args=[], salt=0, account=False):
    hit, cached, cached_addr = await contract_cache_check(client, contract)
    if hit and "multisig" not in contract:
        if account:
            acc = AccountClient(
                client=client,
                address=cached_addr,
                key_pair=KeyPair(0, 0),
                chain=StarknetChainId.TESTNET,
                supported_tx_version=1,
            )
            return acc, cached_addr
        else:
            return cached, cached_addr
    
    if account:
        os.system("starknet-compile --account_contract {}.cairo --output {}_compiled.json".format(contract, contract, contract))

        rand = random.randint(0, data['PRIVATE_KEY'])
        compiled = Path("{}_compiled.json".format(contract)).read_text()

        deployment_result = await Contract.deploy(
            client, compiled_contract=compiled, constructor_args=args, salt=rand
        )
        os.system("rm {}_compiled.json".format(contract))

        cyan.print(f"Deployment Initialized: 0x{hex(deployment_result.hash)}")
        cyan.print("\tWaiting for successful deployment...")
        cyan.print("\tPatience is bitter, but its fruit is sweet...\n")

        res = await deployment_result.wait_for_acceptance()
        acc = AccountClient(
            client=client,
            address=res.deployed_contract.address,
            key_pair=KeyPair(0, 0),
            chain=StarknetChainId.TESTNET,
            supported_tx_version=1,
        )

        contract_cache(client.net, contract, res.deployed_contract.address)
        return acc, res.deployed_contract.address

    else:
        deployment_result = await Contract.deploy(
            client=client,
            compilation_source=[contract + ".cairo"],
            constructor_args=args,
            salt=salt
        )

        res = await deployment_result.wait_for_acceptance()
        
        contract_cache(client.net, contract, res.deployed_contract.address)
        return res.deployed_contract, res.deployed_contract.address

async def fund_account(toAddr):
    client = get_client()
    account = get_account(client)
    
    if args.testnet:
        bal = await account.get_balance(data['TESTNET_ETH'])
        if bal == 0:
            return ""

        nonce_payload = data['NONCE_PAYLOAD']
        nonce_payload['contract_address'] = "0x{:x}".format(account.address)
        nonce_resp = requests.request("POST", data['GOERLI_URL']+"/feeder_gateway/call_contract", data=json.dumps(nonce_payload, indent=4))
        nonce = int(nonce_resp.json()['result'][0], 16)

        pay = data['FUNDING_PAYLOAD']
        calldata=[1, data['TESTNET_ETH'], get_selector_from_name('transfer'), 0, 3, 3, toAddr, data['TRANSFER_AMOUNT'], 0, nonce]
        exec_selector = get_selector_from_name("__execute__")
        hash = calculate_transaction_hash_common(
            tx_hash_prefix=TransactionHashPrefix.INVOKE,
            version=0,
            contract_address=data['TESTNET_ACCOUNT']['ADDRESS'],
            entry_point_selector=exec_selector,
            calldata=calldata,
            max_fee=data['MAX_FEE'],
            chain_id=TESTNET_ID,
            additional_data=[],
        )
        (sig_r, sig_s) = sign(hash, data['TESTNET_ACCOUNT']['PRIVATE'])
        pay['signature'] = [str(sig_r), str(sig_s)] 
        pay['calldata'] = [str(i) for i in calldata]
        pay['contract_address'] = "0x{:x}".format(data['TESTNET_ACCOUNT']['ADDRESS'])
        pay['max_fee'] = "0x{:x}".format(data['MAX_FEE'])
        
        resp = requests.request("POST", data['GOERLI_URL']+"/gateway/add_transaction", data=json.dumps(pay, indent=4))
        await account.wait_for_tx(resp.json()['transaction_hash'])

        return data['TESTNET_ACCOUNT']['ADDRESS']

    else:
        pay = data['MINT_PAYLOAD']
        pay['address'] = "0x{:x}".format(toAddr)

        requests.post(
            account.net+"/mint",
            headers={'Content-Type': 'application/json'},
            data=json.dumps(pay, indent=4)
        )

        return account.address

async def get_evaluator(client):
    _, evaluator, evaluator_address = await contract_cache_check(client, data['EVALUATOR'])
    if evaluator_address == "": 
        red.print("must have a deployed evaluator to test against:")
        red.print("'python3 evaluator.py'")
        return "", ""
    return evaluator, evaluator_address

def devnet_height_check():
    if args.testnet:
        red.print("evaluator only needs to be deployed to devnet")
        return

    height = data['DEVNET_URL']+"/feeder_gateway/get_block?blockNumber=latest"
    response = requests.request("GET", height).json()

    if 'block_number' in response:
        if response['block_number'] == 0:
            with open(ACCOUNT_FILE) as json_file:
                acc_data = json.load(json_file)

            with open(ACCOUNT_FILE, 'w') as outfile:
                acc_data[data['DEVNET_URL']] = {}
                json.dump(acc_data, outfile, sort_keys=True, indent=4)

def get_client():
    if args.testnet:
        return GatewayClient(net="testnet")
    else:
        return GatewayClient(net=data['DEVNET_URL'])

def get_account(client):
    if args.testnet: 
        return AccountClient(
            client=client,
            address=data['TESTNET_ACCOUNT']['ADDRESS'],
            key_pair=KeyPair(
                public_key=data['TESTNET_ACCOUNT']['PUBLIC'],
                private_key=data['TESTNET_ACCOUNT']['PRIVATE'],
            ),
            chain=StarknetChainId.TESTNET,
        )
        
    else:
        resp = requests.get(data['DEVNET_URL']+"/predeployed_accounts").json()
        account = resp[0]

        return AccountClient(
            client=client,
            address=int(account["address"], 16),
            key_pair=KeyPair(
                public_key=int(account["public_key"], 16),
                private_key=int(account["private_key"], 16),
            ),
            chain=StarknetChainId.TESTNET,
            supported_tx_version=1,
        )

def to_uint(a):
    return (a & ((1 << 128) - 1), a >> 128)