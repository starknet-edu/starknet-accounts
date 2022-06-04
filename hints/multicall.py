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
MULTICALL_FILE = os.path.join("../contracts/multicall", "multicall.cairo")
VALIDATOR_FILE = os.path.join("../contracts/validator", "validator.cairo")
ACT_FILE = os.path.join("../contracts/validator", "ACT.cairo")

DUMMY_ACCOUNT = 0x03fe5102616ee1529380b0fac1694c5cc796d8779c119653b3f41b263d4c4961
PRIVATE_KEY = 28269553036454149273332760011886696253239742350009903329945699224417844975
PUBLIC_KEY = 1397467974901608740509397132501478376338248400622004458128166743350896051882
INPUT_1 = 2938
INPUT_2 = 4337

@pytest.fixture
async def starknet() -> Starknet:
    return await Starknet.empty()

@pytest.fixture
async def mock_admin(starknet: Starknet) -> StarknetContract:
    return await starknet.deploy(
        source=MOCK_ADMIN_FILE,
        constructor_calldata=[],
    )

@pytest.fixture
async def validator(starknet: Starknet) -> StarknetContract:
    return await starknet.deploy(
        source=VALIDATOR_FILE,
        constructor_calldata=[PRIVATE_KEY, PUBLIC_KEY, INPUT_1, INPUT_2],
    )

@pytest.fixture
async def multicall(starknet: Starknet) -> StarknetContract:
    return await starknet.deploy(
        source=MULTICALL_FILE,
        constructor_calldata=[],
    )

@pytest.mark.asyncio
async def test_multicall(
    starknet: Starknet,
    validator: StarknetContract,
    multicall: StarknetContract,
):
    ACT = await starknet.deploy(
        source=ACT_FILE,
        constructor_calldata=[validator.contract_address],
    )
    await validator.set_rewards_contract(addr=ACT.contract_address).invoke()

    selector = get_selector_from_name("validate_multicall")
    call_array=[
        multicall.AccountCallArray(validator.contract_address, selector, 0, 1),
        multicall.AccountCallArray(validator.contract_address, selector, 1, 1),
        multicall.AccountCallArray(validator.contract_address, selector, 2, 1),
    ]
    nonce_info = await multicall.get_nonce().call()
    nonce = nonce_info.result.res

    calldata=[nonce, len(call_array), *call_array[0], *call_array[1], *call_array[2], 3, DUMMY_ACCOUNT, DUMMY_ACCOUNT, DUMMY_ACCOUNT]

    hash = invoke_tx_hash(multicall.contract_address, calldata)
    signature = sign(hash, PRIVATE_KEY)

    exec_info = await multicall.__execute__(
        nonce=nonce,
        call_array=call_array,
        calldata=[DUMMY_ACCOUNT, DUMMY_ACCOUNT, DUMMY_ACCOUNT],
    ).invoke(signature=signature)
    assert exec_info.result.response[0] == 0
    assert exec_info.result.response[1] == 0
    assert exec_info.result.response[2] == 1

    balance = await ACT.balanceOf(account=DUMMY_ACCOUNT).call()
    assert balance.result.balance.low == 500000000000000000000
