import os
import json
import pytest

from hashlib import sha256
from ecdsa import SigningKey, SECP256k1
from starkware.starknet.testing.starknet import Starknet
from starkware.starknet.testing.contract import StarknetContract
from starkware.starknet.public.abi import get_selector_from_name

with open("../contracts/hints.json", "r") as f:
  data = json.load(f)

SHIFT = 86 
BASE = 2 ** SHIFT
MASK = BASE - 1
ABSTRACT_PRIV=data['ABSTRACT_PRIV']

# The path to the contract source code.
ABSTRACTION_FILE = os.path.join("../contracts/abstraction", "abstraction.cairo")

@pytest.fixture
async def starknet() -> Starknet:
    return await Starknet.empty()

@pytest.fixture
async def evaluator(starknet: Starknet) -> StarknetContract:
    return await starknet.deploy(
        source="evaluator_mock.cairo",
        cairo_path=["../contracts"],
        constructor_calldata=[data['PRIVATE_KEY'], data['PUBLIC_KEY'], data['INPUT_1'], data['INPUT_2']],
    )

@pytest.fixture
async def abstraction(starknet: Starknet) -> StarknetContract:
    PUB_X=data['ABSTRACT_PUB_X']
    PUB_Y=data['ABSTRACT_PUB_Y']

    calldata_x = []
    calldata_y = []
    for i in range(3):
        calldata_x.append(PUB_X & MASK)
        PUB_X >>= SHIFT
        
        calldata_y.append(PUB_Y & MASK)
        PUB_Y >>= SHIFT

    return await starknet.deploy(
        source=ABSTRACTION_FILE,
        cairo_path=["../contracts"],
        constructor_calldata=[*calldata_x, *calldata_y],
    )

@pytest.mark.asyncio
async def test_abstraction(
    abstraction: StarknetContract,
    evaluator: StarknetContract,
):
    sk = SigningKey.from_string(ABSTRACT_PRIV.to_bytes(32, 'big'), curve=SECP256k1, hashfunc=sha256)

    signature = sk.sign(b"message")

    m = sha256()
    m.update(b"message")
    hash = int.from_bytes(m.digest(), "big")
    sig_r = int.from_bytes(signature[:32], "big")
    sig_s = int.from_bytes(signature[32:], "big")

    calldata_h=[]
    calldata_r=[]
    calldata_s=[]
    for i in range(3):
        calldata_h.append(hash & MASK)
        hash >>= SHIFT

        calldata_r.append(sig_r & MASK)
        sig_r >>= SHIFT

        calldata_s.append(sig_s & MASK)
        sig_s >>= SHIFT

    nonce_info = await abstraction.get_nonce().call()
    nonce = nonce_info.result.res

    exec_info = await abstraction.__execute__(
        contract_address=evaluator.contract_address,
        selector=get_selector_from_name("validate_abstraction"),
        nonce=nonce,
        calldata=[*calldata_h, *calldata_r, *calldata_s, data['DUMMY_ACCOUNT']],
    ).invoke()

    assert exec_info.result.retdata[0] == 1