import os
import pytest
import sys

sys.path.append('../contracts')
from utils import deploy_testnet, invoke_tx_hash

from starkware.starknet.testing.starknet import Starknet
from starkware.starknet.testing.contract import StarknetContract
from starkware.starknet.public.abi import get_selector_from_name
from starkware.crypto.signature.signature import sign
from starkware.python.utils import from_bytes
from starkware.crypto.signature.fast_pedersen_hash import pedersen_hash
from starkware.starknet.core.os.transaction_hash.transaction_hash import TransactionHashPrefix, calculate_transaction_hash_common

# The path to the contract source code.
SIGNATURE_1_FILE = os.path.join("../contracts/signature", "signature_1.cairo")
SIGNATURE_2_FILE = os.path.join("../contracts/signature", "signature_2.cairo")
SIGNATURE_3_FILE = os.path.join("../contracts/signature", "signature_3.cairo")
VALIDATOR_FILE = os.path.join("../contracts/validator", "validator.cairo")
ACT_FILE = os.path.join("../contracts/validator", "ACT.cairo")

DUMMY_ACCOUNT = 0x03fe5102616ee1529380b0fac1694c5cc796d8779c119653b3f41b263d4c4961
PRIVATE_KEY = 28269553036454149273332760011886696253239742350009903329945699224417844975
PUBLIC_KEY = 1397467974901608740509397132501478376338248400622004458128166743350896051882
INPUT_1 = 0
INPUT_2 = 0

@pytest.fixture
async def starknet() -> Starknet:
    return await Starknet.empty()

@pytest.fixture
async def validator(starknet: Starknet) -> StarknetContract:
    return await starknet.deploy(
        source=VALIDATOR_FILE,
        constructor_calldata=[],
    )

@pytest.fixture
async def signature_1(starknet: Starknet) -> StarknetContract:
    return await starknet.deploy(
        source=SIGNATURE_1_FILE,
        constructor_calldata=[],
    )

@pytest.fixture
async def signature_2(starknet: Starknet) -> StarknetContract:
    return await starknet.deploy(
        source=SIGNATURE_2_FILE,
        constructor_calldata=[],
    )

@pytest.fixture
async def signature_3(starknet: Starknet) -> StarknetContract:
    return await starknet.deploy(
        source=SIGNATURE_3_FILE,
        constructor_calldata=[],
    )

@pytest.mark.asyncio
async def test_signature_1(
    validator: StarknetContract,
    signature_1: StarknetContract,
):


@pytest.mark.asyncio
async def test_signature_2(
    validator: StarknetContract,
    signature_2: StarknetContract,
):


@pytest.mark.asyncio
async def test_signature_3(
    validator: StarknetContract,
    signature_3: StarknetContract,
):

