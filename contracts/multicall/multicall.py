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
WALLET_ADDRESS = int(os.getenv("WALLET_ADDRESS"), 16)

async def main():
    mission_statement()
    print("\t 1) implement account execution similar to OpenZeppelin w/ AccountCallArray")
    print("\t 2) deploy account contract")
    print("\t 3) format and sign invocations and calldata")
    print("\t 4) invoke multiple contracts in the same block\u001b[0m\n")

    #
    # MISSION 2
    #
    private_key = 0x100000000000000000000000000000000000000000000000000000DEADBEEF
    stark_key = private_to_stark_key(private_key)

    client = Client("testnet")
    account_address = await deploy_testnet("multicall", [stark_key])
    contract = await Contract.from_address(account_address, client)

    #
    # MISSION 3
    #
    selector = get_selector_from_name("validate_multicall")
    call_array = [
        {
            "to": VALIDATOR_ADDRESS,
            "selector": selector,
            "data_offset": 0,
            "data_len": 1
        },
        {
            "to": VALIDATOR_ADDRESS,
            "selector": selector,
            "data_offset": 1,
            "data_len": 1
        },
        {
            "to": VALIDATOR_ADDRESS,
            "selector": selector,
            "data_offset": 2,
            "data_len": 1
        },
    ]
    inner_calldata = [WALLET_ADDRESS, WALLET_ADDRESS, WALLET_ADDRESS]
    
    (nonce, ) = await contract.functions["get_nonce"].call()
    calldata = [nonce, len(call_array), *call_array[0], *call_array[1], *call_array[2], len(inner_calldata), *inner_calldata]

    hash = invoke_tx_hash(account_address, calldata)
    signature = sign(hash, private_key)

    prepared = contract.functions["__execute__"].prepare(
        nonce=nonce,
        call_array_len=len(call_array),
        call_array=call_array,
        calldata_len=len(inner_calldata),
        calldata=inner_calldata,
    )

    #
    # MISSION 4
    #
    invocation = await prepared.invoke(signature=signature, max_fee=0)

    await print_n_wait(client, invocation)


asyncio.run(main())
