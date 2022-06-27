import os
import sys
import json
import random
import asyncio

sys.path.append('./')

from utils import deploy_testnet, invoke_tx_hash, print_n_wait, mission_statement, transfer_gas
from starknet_py.contract import Contract
from starknet_py.net.client import Client
from starkware.starknet.public.abi import get_selector_from_name
from starkware.crypto.signature.signature import private_to_stark_key, sign

devnet="http://localhost:5000"
max_fee=2500000000000000

with open("./hints.json", "r") as f:
  data = json.load(f)

async def main():
    mission_statement()
    print("\t 1) implement account contract interface 'is_valid_signature'")
    print("\t 2) deploy account contract with an '__execute__' entrypoint init w/ the provided public key")
    print("\t 3) sign the calldata expected by the validator")
    print("\t 4) invoke the validator check with the signature in the tx_info field")
    print("\t 5) call until you hit paydirt\u001b[0m\n")

    #
    # MISSION 2
    #
    # client = Client("testnet")
    client = Client(net=devnet, chain="testnet")

    private_key = data['PRIVATE_KEY']
    stark_key = private_to_stark_key(private_key)
    account_address = await deploy_testnet(client, data['SIGNATURE_2'], [stark_key])
    contract = await Contract.from_address(account_address, client)

    await transfer_gas(client, data['HELLO_ADDRESS'], account_address)

    #
    # MISSION 3
    #
    selector = get_selector_from_name("validate_signature_2")
    calldata = [data['EVALUATOR_ADDRESS'], selector, 2, 1, data['HELLO_ADDRESS']]

    hash = invoke_tx_hash(account_address, calldata)
    signature = sign(hash, private_key)

    prepared1 = contract.functions["__execute__"].prepare(
        contract_address=data['EVALUATOR_ADDRESS'],
        selector=selector,
        calldata_len=3,
        calldata=[hash, random.randint(0, private_key), data['HELLO_ADDRESS']])

    #
    # MISSION 4
    #
    invocation1 = await prepared1.invoke(signature=signature, max_fee=max_fee)

    await print_n_wait(client, invocation1)

    #
    # MISSION 5
    #
    prepared2 = contract.functions["__execute__"].prepare(
        contract_address=data['EVALUATOR_ADDRESS'],
        selector=selector,
        calldata_len=3,
        calldata=[hash, random.randint(0, private_key), data['HELLO_ADDRESS']])
    invocation2 = await prepared2.invoke(signature=signature, max_fee=max_fee)

    await print_n_wait(client, invocation2)

asyncio.run(main())
