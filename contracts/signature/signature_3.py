import os
import asyncio
import sys

sys.path.append('../')

from utils import deploy_testnet, invoke_tx_hash, print_n_wait, mission_statement
from starknet_py.contract import Contract
from starknet_py.net.client import Client
from starkware.starknet.public.abi import get_selector_from_name
from starkware.crypto.signature.signature import private_to_stark_key, sign
from starkware.crypto.signature.fast_pedersen_hash import pedersen_hash

VALIDATOR_ADDRESS = int(os.getenv("VALIDATOR_ADDRESS"), 16)


async def main():
    mission_statement()
    print("\t 1) deploy account contract")
    print("\t 2) store a public signing key for the stark curve in the account")
    print("\t 3) implement the OpenZeppelin interface for 'get_nonce'")
    print("\t 4) manually sign the calldata and pass the signature in the contract invocation\u001b[0m\n")

    private_key = 0x100000000000000000000000000000000000000000000000000000DEADBEEF
    stark_key = private_to_stark_key(private_key)

    client = Client("testnet")
    account_address = await deploy_testnet("signature_3", [stark_key])
    contract = await Contract.from_address(account_address, client)

    (nonce, ) = await contract.functions["get_nonce"].call()
    selector = get_selector_from_name("validate_signature_3")
    calldata = [VALIDATOR_ADDRESS, selector, 1, nonce]

    hash = invoke_tx_hash(account_address, calldata)
    hash_final = pedersen_hash(hash, nonce)
    signature = sign(hash_final, private_key)

    prepared = contract.functions["__execute__"].prepare(
        contract_address=VALIDATOR_ADDRESS,
        selector=selector,
        calldata_len=1,
        calldata=[nonce])
    invocation = await prepared.invoke(signature=signature, max_fee=0)

    await print_n_wait(client, invocation)


asyncio.run(main())
