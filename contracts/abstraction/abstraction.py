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
WALLET_ADDRESS = int(os.getenv("WALLET_ADDRESS"), 16)

async def main():
    mission_statement()
    print("\t 1) implement a contract to verify signatures using secp256k1")
    print("\t 2) deploy account contract with formatted public key")
    print("\t 3) obtain sha256 hash of data")
    print("\t 4) format hash and signature with appropriate bitwidths")
    print("\t 5) invoke the verifier function\u001b[0m\n")

    ABSTRACT_PRIV = 0x2f7b9db25111c73326215d8b709b246103f674d95eccbbec8780214ffd69c8fc
    PUB_X = 0x95cd669eb2bd5ede97706551fbe2bc210940ec7797da33dee43814e292f93837
    PUB_Y = 0x339d4e13c088c0a26c176b3d0505177a70f50345c874a4d4cca1c8b1f05b72bd

    #
    # MISSION 2
    #
    calldata=[
        {
            "x": {"d0": "", "d1": "", "d2": ""}, 
            "y": {"d0": "", "d1": "", "d2": ""},
        }
    ]
    for i in range(3):
        calldata[0]["x"]["d{}".format(i)] = PUB_X & MASK
        PUB_X >>= SHIFT
        calldata[0]["y"]["d{}".format(i)] = PUB_Y & MASK
        PUB_Y >>= SHIFT

    client = Client("testnet")
    account_address = await deploy_testnet("abstraction", calldata)
    contract = await Contract.from_address(account_address, client)

    #
    # MISSION 3
    #
    sk = SigningKey.from_string(ABSTRACT_PRIV.to_bytes(32, 'big'), curve=SECP256k1, hashfunc=sha256)

    data = b"Patience is bitter, but its fruit is sweet..."
    signature = sk.sign(data)

    m = sha256()
    m.update(data)
    hash = int.from_bytes(m.digest(), "big")
    sig_r = int.from_bytes(signature[:32], "big")
    sig_s = int.from_bytes(signature[32:], "big")

    #
    # MISSION 4
    #
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

    calldata = [*bigHash, *bigR, *bigS, WALLET_ADDRESS]

    #
    # MISSION 5
    #
    (nonce, ) = await contract.functions["get_nonce"].call()
    prepared = contract.functions["__execute__"].prepare(
        contract_address=VALIDATOR_ADDRESS,
        selector=get_selector_from_name("validate_abstraction"),
        nonce=nonce,
        calldata_len=len(calldata),
        calldata=calldata
    )
    invocation = await prepared.invoke(max_fee=0)

    await print_n_wait(client, invocation)

asyncio.run(main())
