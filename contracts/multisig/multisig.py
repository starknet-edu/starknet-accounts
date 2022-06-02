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

    private_key_1 = private_key + 1
    stark_key_1 = private_to_stark_key(private_key_1)

    private_key_2 = private_key + 2
    stark_key_2 = private_to_stark_key(private_key_2)

    client = Client("testnet")
    signer_1_address = await deploy_testnet("signature_basic", [stark_key])
    signer_1_contract = await Contract.from_address(signer_1_address, client)

    signer_2_address = await deploy_testnet("signature_basic", [stark_key_1])
    signer_2_contract = await Contract.from_address(signer_2_address, client)

    signer_3_address = await deploy_testnet("signature_basic", [stark_key_2])
    signer_3_contract = await Contract.from_address(signer_3_address, client)

    multi = await deploy_testnet("multisig", [3, signer_1_address, signer_2_address, signer_3_address])
    multi_contract = await Contract.from_address(multi, client)
    
    validator_selector = get_selector_from_name("validate_multisig")
    submit_selector = get_selector_from_name("submit_tx")
    submit_event_selector = get_selector_from_name("submit")

    inner_calldata=[VALIDATOR_ADDRESS, validator_selector, 1, 1]
    outer_calldata=[multi, submit_selector, len(inner_calldata), *inner_calldata]

    hash = invoke_tx_hash(signer_1_address, outer_calldata)x``
    signature = sign(hash, PRIVATE_KEY)


asyncio.run(main())
