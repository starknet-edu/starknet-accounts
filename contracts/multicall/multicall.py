import os
import asyncio
import sys

sys.path.append('../')

from utils import deploy_testnet, invoke_tx_hash, mission_statement, print_n_wait
from starknet_py.contract import Contract
from starknet_py.net.client import Client
from starkware.starknet.public.abi import get_selector_from_name
from starkware.crypto.signature.signature import private_to_stark_key, sign
from starkware.crypto.signature.fast_pedersen_hash import pedersen_hash

VALIDATOR_ADDRESS = int(os.getenv("VALIDATOR_ADDRESS"), 16)


async def main():
    mission_statement()
    print("\t 1) deploy account contract")
    print("\t 2) pass an array of contract invocations and calldata")
    print("\t 3) invoke multiple contract in the same block\u001b[0m\n")

    private_key = 0x100000000000000000000000000000000000000000000000000000DEADBEEF
    stark_key = private_to_stark_key(private_key)

    client = Client("testnet")
    account_address = await deploy_testnet("multicall", [stark_key])
    contract = await Contract.from_address(account_address, client)

    selector = get_selector_from_name("validate_multicall")
    call_array = [
        {
            "to": VALIDATOR_ADDRESS,
            "selector": selector,
            "data_offset": 0,
            "data_len": 0
        },
        {
            "to": VALIDATOR_ADDRESS,
            "selector": selector,
            "data_offset": 0,
            "data_len": 0
        },
        {
            "to": VALIDATOR_ADDRESS,
            "selector": selector,
            "data_offset": 0,
            "data_len": 0
        },
    ]
    calldata = [
        len(call_array), VALIDATOR_ADDRESS, selector, 0, 0, VALIDATOR_ADDRESS,
        selector, 0, 0, VALIDATOR_ADDRESS, selector, 0, 0, 0
    ]

    hash = invoke_tx_hash(account_address, calldata)
    signature = sign(hash, private_key)

    prepared = contract.functions["__execute__"].prepare(
        call_array_len=3,
        call_array=call_array,
        calldata_len=0,
        calldata=[],
    )
    invocation = await prepared.invoke(signature=signature, max_fee=0)

    await print_n_wait(client, invocation)


asyncio.run(main())
