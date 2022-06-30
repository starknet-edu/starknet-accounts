import os
import json
import argparse

from pathlib import Path
from starknet_py.contract import Contract
from starknet_py.net import AccountClient, KeyPair
from starknet_py.net.networks import TESTNET
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

def mission_statement():
    print("\u001b[34;1m\u001b[4mYour mission:\u001b[0m\u001b[34m")

async def print_n_wait(client: Client, invocation: InvokeFunction):
    print("\u001b[35mTransaction Hash: {}\u001b[0m\n".format(invocation.hash))

    try:
        await invocation.wait_for_acceptance()
    except Exception as e:
        print("\u001b[31mInvocation error:")
        print(e)
        print("\u001b[0m\n")

    res = await client.get_transaction_receipt(invocation.hash)

    if "ACCEPT" in str(res.status):
        print("\u001b[32;1mTx Results: {}\u001b[0m".format(res.status))
        for ev in res.events:
            if ev.keys[0] == SUBMIT_TX and len(res.events) == 1:
                return ev.data
            if ev.keys[0] == PAYDAY:
                print("\u001b[32;1mPayday Results: PAYDAY!!!\u001b[0m\n")
                return ev.data
        print("\u001b[33;1mPayday Results: no payday\n")

    else:
        print("\u001b[31;1mTx Results: {}".format(res.status))
    
    print("\u001b[0m")

async def deploy_account(client, contract_path="", constructor_args=[], additional_data=None):
    data = dict()
    CONTRACT_ADDRESS="{}".format(contract_path)
    if additional_data:
        CONTRACT_ADDRESS="{}_{}".format(CONTRACT_ADDRESS, additional_data)
    if os.getenv('ACCOUNT_CACHE') == "false":
        print("\u001b[35mDisabled local account cache\u001b[0m\n")
    else:
        with open(ACCOUNT_FILE) as json_file:
            data = json.load(json_file)
            if CONTRACT_ADDRESS in data[client.net]:
                print("\u001b[35mFound local contract: {}\u001b[0m\n".format(data[client.net][CONTRACT_ADDRESS]))
                
                cached = await Contract.from_address(int(data[client.net][CONTRACT_ADDRESS], 16), client, True)
                return cached, int(data[client.net][CONTRACT_ADDRESS], 16)

    os.system("starknet-compile --account_contract {}.cairo --output {}_compiled.json".format(contract_path, contract_path, contract_path))

    compiled = Path("{}_compiled.json".format(contract_path)).read_text()
    deployment_result = await Contract.deploy(
        client, compiled_contract=compiled, constructor_args=constructor_args
    )
    os.system("rm {}_compiled.json".format(contract_path))

    if not deployment_result.hash:
        print("\u001b[31mFailed to deploy contract\u001b[0m\n")
        raise ValueError("Failed to deploy contract")
        return "", ""

    print("\u001b[35mDeployment Initialized: ", deployment_result.hash)
    print("\tWaiting for successful deployment...")
    print("\tPatience is bitter, but its fruit is sweet...")

    await client.wait_for_tx(deployment_result.hash)
    res = await client.get_transaction(deployment_result.hash)

    if os.getenv('ACCOUNT_CACHE') != "false":
        data[client.net][CONTRACT_ADDRESS] = "0x{:02x}".format(res.transaction.contract_address)
        with open(ACCOUNT_FILE, 'w') as outfile:
            json.dump(data, outfile, sort_keys=True, indent=4)
        print("\tSuccess - cached in accounts.json")

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
    acc_client, _ = get_account_client()
    gas = await Contract.from_address(data['DEVNET_ETH'], acc_client, True)
    await(
        await gas.functions['transfer'].invoke(toAddr, data['TRANSFER_AMOUNT'], max_fee=data['MAX_FEE'])
    ).wait_for_acceptance()

async def get_evaluator(client):
    _, evaluator, evaluator_address = await contract_cache_check(client, data['EVALUATOR'])
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
