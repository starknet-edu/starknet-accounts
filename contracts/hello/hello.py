import os
import asyncio
import sys

sys.path.append('../')

from utils import deploy_testnet, print_n_wait, mission_statement
from starknet_py.contract import Contract
from starknet_py.net.client import Client
from starkware.starknet.public.abi import get_selector_from_name
from starkware.crypto.signature.signature import private_to_stark_key, sign
from starkware.crypto.signature.fast_pedersen_hash import pedersen_hash

VALIDATOR_ADDRESS = int(os.getenv("VALIDATOR_ADDRESS"), 16)
WALLET_ADDRESS = int(os.getenv("WALLET_ADDRESS"), 16)

async def main():
    mission_statement()
    print("\t 1) deploy an account contract with an '__execute__' entrypoint")
    print("\t 2) fetch the 'random' storage_variable from the validator contract")
    print("\t 3) pass 'random' via calldata to your account contract\u001b[0m\n")

    #
    # MISSION 1
    #
    client = Client("testnet")
    account_address = await deploy_testnet("hello", [])
    contract = await Contract.from_address(account_address, client)
    
    #
    # MISSION 2
    #
    validator = await Contract.from_address(VALIDATOR_ADDRESS, client, True)
    (random, ) = await validator.functions["get_random"].call()

    prepared = contract.functions["__execute__"].prepare(
        contract_address=VALIDATOR_ADDRESS,
        selector=get_selector_from_name("validate_hello"),
        calldata_len=2,
        calldata=[random, WALLET_ADDRESS]) # MISSION 3
    invocation = await prepared.invoke(max_fee=0)

    await print_n_wait(client, invocation)

asyncio.run(main())
