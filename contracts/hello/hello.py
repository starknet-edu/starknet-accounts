import os
import asyncio
import sys
import json
import requests

sys.path.append('./')

from utils import deploy_testnet, print_n_wait, mission_statement
from starknet_py.contract import Contract
from starknet_py.net.client import Client
from starkware.starknet.public.abi import get_selector_from_name
from starkware.crypto.signature.signature import private_to_stark_key, sign
from starkware.crypto.signature.fast_pedersen_hash import pedersen_hash

devnet="http://localhost:5000"
max_fee=2500000000000000

with open("./hints.json", "r") as f:
  data = json.load(f)

async def deploy_hello(client):
    compiled = "{}_compiled.json".format(data['HELLO'])
    os.system("starknet-compile --account_contract {}.cairo --output {}".format(data['HELLO'], compiled))

    os.system("starknet deploy --contract {} --gateway_url http://localhost:5000 --salt 0x0".format(compiled))
    os.system("rm {}".format(compiled))

    # fund the hello contract
    payload = json.dumps(data['DEVNET_FUNDING'])
    response = requests.request("POST", devnet+"/gateway/add_transaction", data=payload)

    return await Contract.from_address(data['HELLO_ADDRESS'], client, True)

async def main():
    mission_statement()
    print("\t 1) deploy an account contract with an '__execute__' entrypoint")
    print("\t 2) fetch the 'random' storage_variable from the validator contract")
    print("\t 3) pass 'random' via calldata to your account contract\n")

    #
    # MISSION 1
    #
    # client = Client("testnet")
    client = Client(net=devnet, chain="testnet")

    #
    # MISSION 2
    #
    hello = await deploy_hello(client)

    evaluator = await Contract.from_address(data['EVALUATOR_ADDRESS'], client, True)
    (random, ) = await evaluator.functions["get_random"].call()

    prepared = hello.functions["__execute__"].prepare(
        contract_address=data['EVALUATOR_ADDRESS'],
        selector=get_selector_from_name("validate_hello"),
        calldata_len=2,
        calldata=[random, hello.address]) # MISSION 3
    invocation = await prepared.invoke(max_fee=max_fee)

    await print_n_wait(client, invocation)

asyncio.run(main())
