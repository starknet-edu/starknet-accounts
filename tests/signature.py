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

PRIVATE_KEY = 28269553036454149273332760011886696253239742350009903329945699224417844975
PUBLIC_KEY = 1397467974901608740509397132501478376338248400622004458128166743350896051882
INPUT_1 = 2938
INPUT_2 = 4337

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
async def signature_1_contract(starknet: Starknet) -> StarknetContract:
    return await starknet.deploy(
        source=SIGNATURE_1_FILE,
        constructor_calldata=[],
    )

@pytest.fixture
async def signature_2_contract(starknet: Starknet) -> StarknetContract:
    return await starknet.deploy(
        source=SIGNATURE_2_FILE,
        constructor_calldata=[PUBLIC_KEY],
    )

@pytest.fixture
async def signature_3_contract(starknet: Starknet) -> StarknetContract:
    return await starknet.deploy(
        source=SIGNATURE_3_FILE,
        constructor_calldata=[PUBLIC_KEY],
    )

@pytest.mark.asyncio
async def test_signature_1(
    validator_contract: StarknetContract,
    signature_1_contract: StarknetContract,
):
    hash = pedersen_hash(INPUT_1, INPUT_2)
    hash_final = pedersen_hash(hash, signature_1_contract.contract_address)
    signature = sign(hash_final, PRIVATE_KEY)

    selector = get_selector_from_name("validate_signature_1")
    exec_info = await signature_1_contract.__execute__(
        contract_address=validator_contract.contract_address,
        selector=selector,
        calldata=[INPUT_1, INPUT_2],
    ).invoke(signature=signature)
    assert exec_info.result.retdata[0] == 1

@pytest.mark.asyncio
async def test_signature_2(
    validator_contract: StarknetContract,
    signature_2_contract: StarknetContract,
):
    selector = get_selector_from_name("validate_signature_2")
    calldata=[validator_contract.contract_address, selector, 1, 1]

    hash = invoke_tx_hash(signature_2_contract.contract_address, calldata)
    signature = sign(hash, PRIVATE_KEY)

    exec_info_1 = await signature_2_contract.__execute__(
        contract_address=validator_contract.contract_address,
        selector=selector,
        calldata=[hash, 1],
    ).invoke(signature=signature)
    assert exec_info_1.result.retdata[0] == 0

    exec_info_2 = await signature_2_contract.__execute__(
        contract_address=validator_contract.contract_address,
        selector=selector,
        calldata=[hash, 2],
    ).invoke(signature=signature)
    assert exec_info_2.result.retdata[0] == 1

@pytest.mark.asyncio
async def test_signature_3(
    validator_contract: StarknetContract,
    signature_3_contract: StarknetContract,
):
    nonce_info = await signature_3_contract.get_nonce().call()
    assert nonce_info.result.res == 0
    nonce = nonce_info.result.res

    selector = get_selector_from_name("validate_signature_3")
    calldata=[validator_contract.contract_address, selector, 1, nonce]

    hash = invoke_tx_hash(signature_3_contract.contract_address, calldata)
    hash_final = pedersen_hash(hash, nonce)

    signature = sign(hash_final, PRIVATE_KEY)

    exec_info = await signature_3_contract.__execute__(
        contract_address=validator_contract.contract_address,
        selector=selector,
        calldata=[nonce],
    ).invoke(signature=signature)
    assert exec_info.result.retdata[0] == 1
