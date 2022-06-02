import os
import asyncio
import sys
import random

sys.path.append('../')
from utils import deploy_testnet, invoke_tx_hash, print_n_wait, mission_statement

from starknet_py.contract import Contract
from starknet_py.net.client import Client
from starkware.starknet.public.abi import get_selector_from_name
from starkware.crypto.signature.signature import private_to_stark_key, sign

VALIDATOR_ADDRESS = int(os.getenv("VALIDATOR_ADDRESS"), 16)


async def main():
    mission_statement()
    print("\t 1) deploy account contract with an '__execute__' entrypoint")
    print("\t 2) store the public signing key for the stark curve in the account")
    print("\t 3) implement the OpenZeppelin interface for 'is_valid_signature'")
    print("\t 4) sign the calldata")
    print("\t 5) populate the tx_info 'signature' field w/ this signature\n")
    print("\t 6) invoke the validator via your account contract\u001b[0m\n")

    private_key = 0x100000000000000000000000000000000000000000000000000000DEADBEEF
    stark_key = private_to_stark_key(private_key)

    client = Client("testnet")
    account_address = await deploy_testnet("signature_2", [stark_key])
    contract = await Contract.from_address(account_address, client)
    validator_contract = await Contract.from_address(VALIDATOR_ADDRESS, client)

    selector = get_selector_from_name("validate_signature_2")
    calldata = [VALIDATOR_ADDRESS, selector, 1, 1]

    hash = invoke_tx_hash(account_address, calldata)
    signature = sign(hash, private_key)

    prepared1 = contract.functions["__execute__"].prepare(
        contract_address=VALIDATOR_ADDRESS,
        selector=selector,
        calldata_len=3,
        calldata=[hash, random.randint(0, private_key)])
    invocation1 = await prepared1.invoke(signature=signature, max_fee=0)

    print("Transaction Hash: ", invocation1.hash)
    print("\tHe that can have patience can have what he will....\n")
    await invocation1.wait_for_acceptance()

    (dupe, ) = await validator_contract.functions["get_dupe_nonce"].call(
        tx_hash=hash)

    if dupe == 2:
        print("\033[92mDupe Nonce: {}\033[0m\n".format(dupe))
        return
    else:
        print("\033[91mDupe Nonce: {}\033[0m\n".format(dupe))

    prepared2 = contract.functions["__execute__"].prepare(
        contract_address=VALIDATOR_ADDRESS,
        selector=selector,
        calldata_len=3,
        calldata=[hash, random.randint(0, private_key)])
    invocation2 = await prepared2.invoke(signature=signature, max_fee=0)

    print("Transaction Hash: ", invocation2.hash)
    print("\tHe that can have patience can have what he will....\n")
    await invocation2.wait_for_acceptance()

    (dupe, ) = await validator_contract.functions["get_dupe_nonce"].call(
        tx_hash=hash)

    if dupe == 2:
        print("\033[92mDupe Nonce: {}\033[0m\n".format(dupe))
    else:
        print("\033[91mDupe Nonce: {}\033[0m\n".format(dupe))


asyncio.run(main())
