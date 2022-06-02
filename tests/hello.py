import os
import pytest
from starkware.starknet.testing.starknet import Starknet
from starkware.starknet.testing.contract import StarknetContract
from starkware.starknet.public.abi import get_selector_from_name
from starkware.starkware_utils.error_handling import StarkException

# The path to the contract source code.
CONTRACT_FILE = os.path.join("../contracts/hello", "hello.cairo")
VALIDATOR_FILE = os.path.join("../contracts/validator", "validator.cairo")

@pytest.fixture
async def starknet() -> Starknet:
    return await Starknet.empty()

@pytest.fixture
async def validator_contract(starknet: Starknet) -> StarknetContract:
    return await starknet.deploy(
        source=VALIDATOR_FILE,
        constructor_calldata=[1, 1, 1, 1],
    )

@pytest.fixture
async def hello_contract(starknet: Starknet) -> StarknetContract:
    return await starknet.deploy(
        source=CONTRACT_FILE,
        constructor_calldata=[],
    )

@pytest.mark.asyncio
async def test_hello(
    validator_contract: StarknetContract,
    hello_contract: StarknetContract,
):
    rand_exec_info = await validator_contract.get_random().call()
    selector = get_selector_from_name("validate_hello")
    exec_info = await hello_contract.__execute__(
        contract_address=validator_contract.contract_address,
        selector=selector,
        calldata=[rand_exec_info.result.rand],
    ).invoke()
    assert exec_info.result.retdata[0] == 1

    with pytest.raises(StarkException, match="ASSERT_EQ instruction failed"):
        selector = get_selector_from_name("validate_hello")
        exec_info = await hello_contract.__execute__(
            contract_address=validator_contract.contract_address,
            selector=selector,
            calldata=[0],
        ).invoke()
