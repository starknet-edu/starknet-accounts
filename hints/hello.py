import os
import pytest

from starkware.starknet.testing.starknet import Starknet
from starkware.starknet.testing.contract import StarknetContract
from starkware.starknet.public.abi import get_selector_from_name
from starkware.starkware_utils.error_handling import StarkException

# The path to the contract source code.
CONTRACT_FILE = os.path.join("../contracts/hello", "hello.cairo")
VALIDATOR_FILE = os.path.join("../contracts/validator", "validator.cairo")
ACT_FILE = os.path.join("../contracts/validator", "ACT.cairo")

DUMMY_ACCOUNT = 0x03fe5102616ee1529380b0fac1694c5cc796d8779c119653b3f41b263d4c4961

@pytest.fixture
async def starknet() -> Starknet:
    return await Starknet.empty()

@pytest.fixture
async def validator(starknet: Starknet) -> StarknetContract:
    return await starknet.deploy(
        source=VALIDATOR_FILE,
        constructor_calldata=[1, 1, 1, 1],
    )

@pytest.fixture
async def hello(starknet: Starknet) -> StarknetContract:
    return await starknet.deploy(
        source=CONTRACT_FILE,
        constructor_calldata=[],
    )

@pytest.mark.asyncio
async def test_hello(
    starknet: Starknet,
    validator: StarknetContract,
    hello: StarknetContract
):
    ACT = await starknet.deploy(
        source=ACT_FILE,
        constructor_calldata=[validator.contract_address],
    )
    await validator.set_rewards_contract(addr=ACT.contract_address).invoke()

    rand_info = await validator.get_random().call()
    selector = get_selector_from_name("validate_hello")

    exec_info = await hello.__execute__(
        contract_address=validator.contract_address,
        selector=selector,
        calldata=[rand_info.result.rand, DUMMY_ACCOUNT],
    ).invoke()
    assert exec_info.result.retdata[0] == 1

    balance = await ACT.balanceOf(account=DUMMY_ACCOUNT).call()
    assert balance.result.balance.low == 100000000000000000000
