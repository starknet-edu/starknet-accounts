import sys
import json
import asyncio

sys.path.append('./')

from utils import deploy_account, print_n_wait, mission_statement, fund_account, get_evaluator
from hashlib import sha256
from ecdsa import SigningKey, SECP256k1
from starknet_py.net.client import Client
from starkware.starknet.public.abi import get_selector_from_name

SHIFT = 86
BASE = 2**SHIFT
MASK = BASE - 1

with open("./hints.json", "r") as f:
  data = json.load(f)

async def main():
    mission_statement()
    print("\t 1) implement a contract to verify signatures using secp256k1")
    print("\t 2) deploy account contract with formatted public key")
    print("\t 3) obtain sha256 hash of data")
    print("\t 4) format hash and signature with appropriate bitwidths")
    print("\t 5) invoke the verifier function\u001b[0m\n")

    ABSTRACT_PRIV = data['ABSTRACT_PRIV']
    PUB_X = data['ABSTRACT_PUB_X']
    PUB_Y = data['ABSTRACT_PUB_Y']

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

    # client = Client("testnet")
    client = Client(net=data['DEVNET_URL'], chain="testnet")

    abstraction, abstraction_addr = await deploy_account(client=client, contract_path=data['ABSTRACTION'], constructor_args=calldata)

    await fund_account(abstraction_addr)

    _, evaluator_address = await get_evaluator(client)

    #
    # MISSION 3
    #
    sk = SigningKey.from_string(ABSTRACT_PRIV.to_bytes(32, 'big'), curve=SECP256k1, hashfunc=sha256)

    msg_data = b"Patience is bitter, but its fruit is sweet..."
    signature = sk.sign(msg_data)

    m = sha256()
    m.update(msg_data)
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

    calldata = [*bigHash, *bigR, *bigS, data['DEVNET_ACCOUNT']['ADDRESS']]

    #
    # MISSION 5
    #
    (nonce, ) = await abstraction.functions["get_nonce"].call()
    prepared = abstraction.functions["__execute__"].prepare(
        contract_address=evaluator_address,
        selector=get_selector_from_name("validate_abstraction"),
        nonce=nonce,
        calldata_len=len(calldata),
        calldata=calldata)

    abFee = int((data['MAX_FEE']*135)/10)
    invocation = await prepared.invoke(max_fee=abFee)

    await print_n_wait(client, invocation)

asyncio.run(main())
