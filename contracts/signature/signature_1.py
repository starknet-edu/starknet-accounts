import os
import asyncio
import sys
import json

sys.path.append('./')

from utils import deploy_testnet, print_n_wait, mission_statement, transfer_gas
from starknet_py.contract import Contract
from starknet_py.net.client import Client
from starkware.starknet.public.abi import get_selector_from_name
from starkware.crypto.signature.signature import private_to_stark_key, sign
from starkware.crypto.signature.fast_pedersen_hash import pedersen_hash

# VALIDATOR_ADDRESS = int(os.getenv("VALIDATOR_ADDRESS"), 16)
# WALLET_ADDRESS = int(os.getenv("WALLET_ADDRESS"), 16)
devnet="http://localhost:5000"
max_fee=2500000000000000

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
    client = Client(net=devnet, chain="testnet")

    account_address = await deploy_testnet(client, data['SIGNATURE_1'])
    contract = await Contract.from_address(account_address, client)

    await transfer_gas(client, data['HELLO_ADDRESS'], account_address)

    #
    # MISSION 3
    #
    hash = pedersen_hash(INPUT_1, INPUT_2)
    hash_final = pedersen_hash(hash, account_address)
    signature = sign(hash_final, data['PRIVATE_KEY'])

    prepared = contract.functions["__execute__"].prepare(
        contract_address=data['EVALUATOR_ADDRESS'],
        selector=get_selector_from_name("validate_signature_1"),
        calldata_len=3,
        calldata=[INPUT_1, INPUT_2, data['HELLO_ADDRESS']])
    
    #
    # MISSION 4
    #
    invocation = await prepared.invoke(signature=signature, max_fee=max_fee)

    await print_n_wait(client, invocation)


asyncio.run(main())
