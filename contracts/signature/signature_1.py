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
    print("\t 1) deploy account contract with an '__execute__' entrypoint")
    print("\t 2) find the first two EIP numbers discussing account abstraction")
    print("\t 3) use the  provided private key to sign the values using the stark curve")
    print("\t 4) populate the tx_info 'signature' field w/ this signature\n")
    print("\t 5) invoke the validator via your account contract\n")

    INPUT_1 = 2938
    INPUT_2 = 4337
    print(
        "First account abstraction EIP: \n\thttps://eips.ethereum.org/EIPS/eip-{}"
        .format(INPUT_1))
    print(
        "Second account abstraction EIP: \n\thttps://eips.ethereum.org/EIPS/eip-{}\u001b[0m\n"
        .format(INPUT_2))

    private_key = 0x100000000000000000000000000000000000000000000000000000DEADBEEF
    stark_key = private_to_stark_key(private_key)

    client = Client("testnet")
    account_address = await deploy_testnet("signature_1", [])
    contract = await Contract.from_address(account_address, client)

    selector = get_selector_from_name("validate_signature_1")

    hash = pedersen_hash(INPUT_1, INPUT_2)
    hash_final = pedersen_hash(hash, account_address)
    signature = sign(hash_final, private_key)

    prepared = contract.functions["__execute__"].prepare(
        contract_address=VALIDATOR_ADDRESS,
        selector=selector,
        calldata_len=2,
        calldata=[INPUT_1, INPUT_2])
    invocation = await prepared.invoke(signature=signature, max_fee=0)

    await print_n_wait(client, invocation)


asyncio.run(main())
