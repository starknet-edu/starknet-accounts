import os
import asyncio
import sys

sys.path.append('../')

from utils import mission_statement, deploy_testnet, print_n_wait

from hashlib import sha256
from ecdsa import SigningKey, VerifyingKey, SECP256k1
from starknet_py.contract import Contract
from starknet_py.net.client import Client
from starkware.starknet.public.abi import get_selector_from_name
from starkware.crypto.signature.signature import private_to_stark_key, sign
from starkware.crypto.signature.fast_pedersen_hash import pedersen_hash

SHIFT = 86
BASE = 2**SHIFT
MASK = BASE - 1
VALIDATOR_ADDRESS = int(os.getenv("VALIDATOR_ADDRESS"), 16)


async def main():
    mission_statement()
    print("\t 1) deploy account contract")
    print("\t 2) pass an array of contract invocations as well as calldata")
    print("\t 3) such that multiple contract calls are run in the same transaction\u001b[0m\n")

    ABSTRACT_PRIV = 0x2f7b9db25111c73326215d8b709b246103f674d95eccbbec8780214ffd69c8fc
    PUB_X = 0x95cd669eb2bd5ede97706551fbe2bc210940ec7797da33dee43814e292f93837
    PUB_Y = 0x339d4e13c088c0a26c176b3d0505177a70f50345c874a4d4cca1c8b1f05b72bd

    calldata=[
        {
            "x": {"d0": "", "d1": "", "d2": ""}, 
            "y": {"d0": "", "d1": "", "d2": ""},
        }
    ]
    for i in range(3):
        calldata[0]["x"]["d{}".format(i)] = PUB_X & MASK
        PUB_Y >>= SHIFT
        calldata[0]["y"]["d{}".format(i)] = PUB_Y & MASK
        PUB_X >>= SHIFT

    client = Client("testnet")
    account_address = await deploy_testnet("abstraction", calldata)
    contract = await Contract.from_address(account_address, client)

    sk = SigningKey.from_string(ABSTRACT_PRIV.to_bytes(32, 'big'), curve=SECP256k1, hashfunc=sha256)

    data = b"Patience is bitter, but its fruit is sweet..."
    signature = sk.sign(data)

    m = sha256()
    m.update(data)
    hash = int.from_bytes(m.digest(), "big")
    sig_r = int.from_bytes(signature[:32], "big")
    sig_s = int.from_bytes(signature[32:], "big")

    selector = get_selector_from_name("validate_abstraction")
    bigHash=[]
    bigR=[]
    bigS=[]
    for i in range(3):
        bigHash.append(hash & MASK)
        hash >>= SHIFT
        
        bigR.append(sig_r & MASK)
        sig_r >>= SHIFT

        bigS.append(sig_s & MASK)
        sig_s >>= SHIFT

    calldata = [*bigHash, *bigR, *bigS]

    prepared = contract.functions["__execute__"].prepare(
        contract_address=VALIDATOR_ADDRESS,
        selector=selector,
        calldata_len=len(calldata),
        calldata=calldata
    )
    invocation = await prepared.invoke(max_fee=0)

    await print_n_wait(client, invocation)

asyncio.run(main())
