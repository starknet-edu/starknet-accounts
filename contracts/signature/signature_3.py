import os
import sys
import json
import asyncio

sys.path.append('./')

from utils import deploy_testnet, invoke_tx_hash, print_n_wait, mission_statement, transfer_gas
from starknet_py.contract import Contract
from starknet_py.net.client import Client
from starkware.starknet.public.abi import get_selector_from_name
from starkware.crypto.signature.signature import private_to_stark_key, sign
from starkware.crypto.signature.fast_pedersen_hash import pedersen_hash

devnet="http://localhost:5000"
max_fee=2500000000000000

with open("./hints.json", "r") as f:
  data = json.load(f)

async def main():
    mission_statement()
    print("\t 1) implement account contract interface 'get_nonce'")
    print("\t 2) implement account contract interface 'get_signer'")
    print("\t 3) deploy account contract")
    print("\t 4) sign calldata")
    print("\t 5) invoke check\u001b[0m\n")

    #
    # MISSION 3
    #
    private_key = data['PRIVATE_KEY']
    stark_key = private_to_stark_key(private_key)

    # client = Client("testnet")
    client = Client(net=devnet, chain="testnet")

    account_address = await deploy_testnet(client, data['SIGNATURE_3'], [stark_key])
    contract = await Contract.from_address(account_address, client)

    #
    # MISSION 4
    #
    (nonce, ) = await contract.functions["get_nonce"].call()
    selector = get_selector_from_name("validate_signature_3")
    calldata = [data['EVALUATOR_ADDRESS'], selector, 2, nonce, data['HELLO_ADDRESS']]

    hash = invoke_tx_hash(account_address, calldata)
    hash_final = pedersen_hash(hash, nonce)
    signature = sign(hash_final, private_key)

    prepared = contract.functions["__execute__"].prepare(
        contract_address=data['EVALUATOR_ADDRESS'],
        selector=selector,
        calldata_len=2,
        calldata=[nonce, data['HELLO_ADDRESS']])
    
    #
    # MISSION 5
    #
    invocation = await prepared.invoke(signature=signature, max_fee=max_fee)

    await print_n_wait(client, invocation)


asyncio.run(main())
