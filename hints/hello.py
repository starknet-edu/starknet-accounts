import os
import json
import pytest

from starkware.starknet.testing.starknet import Starknet
from starkware.starknet.testing.contract import StarknetContract
from starkware.starknet.public.abi import get_selector_from_name

HELLO_FILE = os.path.join("../contracts/hello", "hello.cairo")

with open("../contracts/hints.json", "r") as f:
  data = json.load(f)

@pytest.fixture
async def starknet() -> Starknet:
    return await Starknet.empty()

@pytest.fixture
async def hello(starknet: Starknet) -> StarknetContract:
    return await starknet.deploy(
        source=HELLO_FILE,
        constructor_calldata=[],
    )

@pytest.fixture
async def evaluator(starknet: Starknet) -> StarknetContract:
    return await starknet.deploy(
        source="evaluator_mock.cairo",
        cairo_path=["../contracts"],
        constructor_calldata=[data['PRIVATE_KEY'], data['PUBLIC_KEY'], data['INPUT_1'], data['INPUT_2']],
    )

@pytest.mark.asyncio
async def test_hello(
    hello: StarknetContract,
    evaluator: StarknetContract,
):
    rand_info = await evaluator.get_random().call()

    exec_info = await hello.__execute__(
        contract_address=evaluator.contract_address,
        selector=get_selector_from_name("validate_hello"),
        calldata=[rand_info.result.rand, data['DUMMY_ACCOUNT']],
    ).invoke()

    assert exec_info.result.retdata[0] == 1
