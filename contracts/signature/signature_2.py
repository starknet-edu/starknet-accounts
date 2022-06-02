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
WALLET_ADDRESS = int(os.getenv("WALLET_ADDRESS"), 16)

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
    client = Client("testnet")
    private_key = 0x100000000000000000000000000000000000000000000000000000DEADBEEF
    stark_key = private_to_stark_key(private_key)
    account_address = await deploy_testnet("signature_2", [stark_key])
    contract = await Contract.from_address(account_address, client)

    #
    # MISSION 3
    #
    validator_contract = await Contract.from_address(VALIDATOR_ADDRESS, client)
    selector = get_selector_from_name("validate_signature_2")
    calldata = [VALIDATOR_ADDRESS, selector, 2, 1, WALLET_ADDRESS]

    hash = invoke_tx_hash(account_address, calldata)
    signature = sign(hash, private_key)

    prepared1 = contract.functions["__execute__"].prepare(
        contract_address=VALIDATOR_ADDRESS,
        selector=selector,
        calldata_len=3,
        calldata=[hash, random.randint(0, private_key), WALLET_ADDRESS])

    #
    # MISSION 4
    #
    invocation1 = await prepared1.invoke(signature=signature, max_fee=0)

    await print_n_wait(client, invocation1)

    #
    # MISSION 5
    #
    prepared2 = contract.functions["__execute__"].prepare(
        contract_address=VALIDATOR_ADDRESS,
        selector=selector,
        calldata_len=3,
        calldata=[hash, random.randint(0, private_key), WALLET_ADDRESS])
    invocation2 = await prepared2.invoke(signature=signature, max_fee=0)

    await print_n_wait(client, invocation2)



asyncio.run(main())
