import os
import pytest

from hashlib import sha256
from ecdsa import SigningKey, VerifyingKey, SECP256k1
from starkware.starknet.testing.starknet import Starknet
from starkware.starknet.testing.contract import StarknetContract
from starkware.starknet.public.abi import get_selector_from_name

SHIFT = 86 
BASE = 2 ** SHIFT
MASK = BASE - 1

# The path to the contract source code.
ABSTRACTION_FILE = os.path.join("../contracts/abstraction", "abstraction.cairo")
VALIDATOR_FILE = os.path.join("../contracts/validator", "validator.cairo")

DUMMY_ACCOUNT = 0x03fe5102616ee1529380b0fac1694c5cc796d8779c119653b3f41b263d4c4961
PRIVATE_KEY = 28269553036454149273332760011886696253239742350009903329945699224417844975
PUBLIC_KEY = 1397467974901608740509397132501478376338248400622004458128166743350896051882
INPUT_1 = 2938
INPUT_2 = 4337

ABSTRACT_PRIV=0x2f7b9db25111c73326215d8b709b246103f674d95eccbbec8780214ffd69c8fc

@pytest.fixture
async def starknet() -> Starknet:
    return await Starknet.empty()

@pytest.fixture
async def validator_contract(starknet: Starknet) -> StarknetContract:
    return await starknet.deploy(
        source=VALIDATOR_FILE,
        constructor_calldata=[PRIVATE_KEY, PUBLIC_KEY, INPUT_1, INPUT_2],
    )

@pytest.fixture
async def abstraction_contract(starknet: Starknet) -> StarknetContract:
    PUB_X=0x95cd669eb2bd5ede97706551fbe2bc210940ec7797da33dee43814e292f93837
    PUB_Y=0x339d4e13c088c0a26c176b3d0505177a70f50345c874a4d4cca1c8b1f05b72bd

    calldata = []
    calldata.append(PUB_X & MASK)
    PUB_X >>= SHIFT
    
    calldata.append(PUB_X & MASK)
    PUB_X >>= SHIFT

    calldata.append(PUB_X & MASK)
    PUB_X >>= SHIFT

    calldata.append(PUB_Y & MASK)
    PUB_Y >>= SHIFT
    
    calldata.append(PUB_Y & MASK)
    PUB_Y >>= SHIFT

    calldata.append(PUB_Y & MASK)
    PUB_Y >>= SHIFT

    return await starknet.deploy(
        source=ABSTRACTION_FILE,
        constructor_calldata=calldata,
    )

@pytest.mark.asyncio
async def test_abstraction(
    validator_contract: StarknetContract,
    abstraction_contract: StarknetContract,
):
    sk = SigningKey.from_string(ABSTRACT_PRIV.to_bytes(32, 'big'), curve=SECP256k1, hashfunc=sha256)

    signature = sk.sign(b"message")

    m = sha256()
    m.update(b"message")
    hash = int.from_bytes(m.digest(), "big")
    sig_r = int.from_bytes(signature[:32], "big")
    sig_s = int.from_bytes(signature[32:], "big")

    selector = get_selector_from_name("validate_abstraction")
    calldata=[]
    calldata.append(hash & MASK)
    hash >>= SHIFT
    
    calldata.append(hash & MASK)
    hash >>= SHIFT

    calldata.append(hash & MASK)
    hash >>= SHIFT

    calldata.append(sig_r & MASK)
    sig_r >>= SHIFT
    
    calldata.append(sig_r & MASK)
    sig_r >>= SHIFT

    calldata.append(sig_r & MASK)
    sig_r >>= SHIFT

    calldata.append(sig_s & MASK)
    sig_s >>= SHIFT
    
    calldata.append(sig_s & MASK)
    sig_s >>= SHIFT

    calldata.append(sig_s & MASK)
    sig_s >>= SHIFT

    calldata.append(DUMMY_ACCOUNT)

    nonce_info = await abstraction_contract.get_nonce().call()
    nonce = nonce_info.result.res

    exec_info = await abstraction_contract.__execute__(
        contract_address=validator_contract.contract_address,
        selector=selector,
        nonce=nonce,
        calldata=calldata,
    ).invoke()
    assert exec_info.result.retdata[0] == 1
