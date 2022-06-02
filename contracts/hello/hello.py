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


async def main():
    mission_statement()
    print("\t 1) deploy an account contract with an '__execute__' entrypoint")
    print("\t 2) fetch the 'random' storage_variable from the validator contract")
    print("\t 3) pass 'random' via calldata to your account contract\u001b[0m\n")

    client = Client("testnet")
    account_address = await deploy_testnet("hello", [])
    contract = await Contract.from_address(account_address, client)
    validator_contract = await Contract.from_address(VALIDATOR_ADDRESS, client)

    selector = get_selector_from_name("validate_hello")
    (random, ) = await validator_contract.functions["get_random"].call()

    prepared = contract.functions["__execute__"].prepare(
        contract_address=VALIDATOR_ADDRESS,
        selector=selector,
        calldata_len=1,
        calldata=[random])
    invocation = await prepared.invoke(max_fee=0)

    await print_n_wait(client, invocation)


asyncio.run(main())
