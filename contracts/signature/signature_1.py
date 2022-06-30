import os
import asyncio
import sys
import json

sys.path.append('./')

from utils import deploy_testnet, print_n_wait, mission_statement, get_evaluator, devnet_funding
from starknet_py.net.client import Client
from starkware.starknet.public.abi import get_selector_from_name
from starkware.crypto.signature.signature import sign
from starkware.crypto.signature.fast_pedersen_hash import pedersen_hash

with open("./hints.json", "r") as f:
  data = json.load(f)

async def main():
    mission_statement()
    print("\t 1) find the first two EIP numbers discussing account abstraction")
    print("\t 2) deploy account contract with an '__execute__' entrypoint")
    print("\t 3) use the private key to sign the values using the Stark curve")
    print("\t 4) invoke the validator check with the signature in the tx_info field\n")

    #
    # MISSION 1
    #
    INPUT_1 = 2938
    INPUT_2 = 4337
    print(
        "First account abstraction EIP: \n\thttps://eips.ethereum.org/EIPS/eip-{}"
        .format(INPUT_1))
    print(
        "Second account abstraction EIP: \n\thttps://eips.ethereum.org/EIPS/eip-{}\u001b[0m\n"
        .format(INPUT_2))

    #
    # MISSION 2
    #
    # client = Client("testnet")
    client = Client(net=data['DEVNET_URL'], chain="testnet")

    sig1, sig1_addr = await deploy_testnet(client, data['SIGNATURE_1'])

    await devnet_funding(data, sig1_addr)

    _, evaluator_address = await get_evaluator(client, data['EVALUATOR'])
    #
    # MISSION 3
    #
    hash = pedersen_hash(INPUT_1, INPUT_2)
    hash_final = pedersen_hash(hash, sig1_addr)
    signature = sign(hash_final, data['PRIVATE_KEY'])

    prepared = sig1.functions["__execute__"].prepare(
        contract_address=evaluator_address,
        selector=get_selector_from_name("validate_signature_1"),
        calldata_len=3,
        calldata=[INPUT_1, INPUT_2, data['DEVNET_ACCOUNT']['ADDRESS']])
    
    #
    # MISSION 4
    #
    invocation = await prepared.invoke(signature=signature, max_fee=data['MAX_FEE'])

    await print_n_wait(client, invocation)


asyncio.run(main())
