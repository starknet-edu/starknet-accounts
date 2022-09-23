import os
import json
import pytest

from utils import invoke_tx_hash
from starkware.starknet.testing.starknet import Starknet
from starkware.starknet.testing.contract import StarknetContract
from starkware.starknet.public.abi import get_selector_from_name
from starkware.crypto.signature.signature import sign
from starkware.crypto.signature.fast_pedersen_hash import pedersen_hash

with open("../contracts/config.json", "r") as f:
  data = json.load(f)

# The path to the contract source code.
SIGNATURE_1_FILE = os.path.join("../contracts/signature", "signature_1.cairo")
SIGNATURE_2_FILE = os.path.join("../contracts/signature", "signature_2.cairo")
SIGNATURE_3_FILE = os.path.join("../contracts/signature", "signature_3.cairo")

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
async def signature_1(starknet: Starknet) -> StarknetContract:
    return await starknet.deploy(
        source=SIGNATURE_1_FILE,
        constructor_calldata=[],
    )

@pytest.fixture
async def signature_2(starknet: Starknet) -> StarknetContract:
    return await starknet.deploy(
        source=SIGNATURE_2_FILE,
        constructor_calldata=[data['PUBLIC_KEY']],
    )

@pytest.fixture
async def signature_3(starknet: Starknet) -> StarknetContract:
    return await starknet.deploy(
        source=SIGNATURE_3_FILE,
        constructor_calldata=[data['PUBLIC_KEY']],
    )

@pytest.mark.asyncio
async def test_signature_1(
    signature_1: StarknetContract,
    evaluator: StarknetContract,
):
    hash = pedersen_hash(data['INPUT_1'], data['INPUT_2'])
    hash_final = pedersen_hash(hash, signature_1.contract_address)
    signature = sign(hash_final, data['PRIVATE_KEY'])

    exec_info = await signature_1.__execute__(
        contract_address=evaluator.contract_address,
        selector=get_selector_from_name("validate_signature_1"),
        calldata=[data['INPUT_1'], data['INPUT_2'], data['DUMMY_ACCOUNT']],
    ).invoke(signature=signature)

    assert exec_info.result.retdata[0] == 1

@pytest.mark.asyncio
async def test_signature_2(
    signature_2: StarknetContract,
    evaluator: StarknetContract,
):
    selector = get_selector_from_name("validate_signature_2")
    calldata=[evaluator.contract_address, selector, 2, 1, data['DUMMY_ACCOUNT']]

    hash = invoke_tx_hash(data, signature_2.contract_address, calldata)
    signature = sign(hash, data['PRIVATE_KEY'])

    exec_info_1 = await signature_2.__execute__(
        contract_address=evaluator.contract_address,
        selector=selector,
        calldata=[hash, 1, data['DUMMY_ACCOUNT']],
    ).invoke(signature=signature)

    assert exec_info_1.result.retdata[0] == 0

    exec_info_2 = await signature_2.__execute__(
        contract_address=evaluator.contract_address,
        selector=selector,
        calldata=[hash, 2, data['DUMMY_ACCOUNT']],
    ).invoke(signature=signature)

    assert exec_info_2.result.retdata[0] == 1
    

@pytest.mark.asyncio
async def test_signature_3(
    signature_3: StarknetContract,
    evaluator: StarknetContract,
):
    nonce_info = await signature_3.get_nonce().call()
    assert nonce_info.result.res == 0
    nonce = nonce_info.result.res

    selector = get_selector_from_name("validate_signature_3")
    calldata=[evaluator.contract_address, selector, 2, nonce, data['DUMMY_ACCOUNT']]

    hash = invoke_tx_hash(data, signature_3.contract_address, calldata)
    hash_final = pedersen_hash(hash, nonce)

    signature = sign(hash_final, data['PRIVATE_KEY'])

    exec_info = await signature_3.__execute__(
        contract_address=evaluator.contract_address,
        selector=selector,
        calldata=[nonce, data['DUMMY_ACCOUNT']],
    ).invoke(signature=signature)

    assert exec_info.result.retdata[0] == 1

