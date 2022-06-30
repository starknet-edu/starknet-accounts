import os
import json
import pytest

from utils import invoke_tx_hash
from starkware.starknet.testing.starknet import Starknet
from starkware.starknet.testing.contract import StarknetContract
from starkware.starknet.public.abi import get_selector_from_name
from starkware.crypto.signature.signature import sign

with open("../contracts/hints.json", "r") as f:
  data = json.load(f)

# The path to the contract source code.
MULTICALL_FILE = os.path.join("../contracts/multicall", "multicall.cairo")

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
async def multicall(starknet: Starknet) -> StarknetContract:
    return await starknet.deploy(
        source=MULTICALL_FILE,
        constructor_calldata=[],
    )

@pytest.mark.asyncio
async def test_multicall(
    multicall: StarknetContract,
    evaluator: StarknetContract,
):
    selector = get_selector_from_name("validate_multicall")
    call_array=[
        multicall.AccountCallArray(evaluator.contract_address, selector, 0, 1),
        multicall.AccountCallArray(evaluator.contract_address, selector, 1, 1),
        multicall.AccountCallArray(evaluator.contract_address, selector, 2, 1),
    ]
    nonce_info = await multicall.get_nonce().call()
    nonce = nonce_info.result.res

    calldata=[nonce, len(call_array), *call_array[0], *call_array[1], *call_array[2], 3, data['DUMMY_ACCOUNT'], data['DUMMY_ACCOUNT'], data['DUMMY_ACCOUNT']]

    hash = invoke_tx_hash(data, multicall.contract_address, calldata)
    signature = sign(hash, data['PRIVATE_KEY'])

    exec_info = await multicall.__execute__(
        nonce=nonce,
        call_array=call_array,
        calldata=[data['DUMMY_ACCOUNT'], data['DUMMY_ACCOUNT'], data['DUMMY_ACCOUNT']],
    ).invoke(signature=signature)

    assert exec_info.result.response[0] == 0
    assert exec_info.result.response[1] == 0
    assert exec_info.result.response[2] == 1
