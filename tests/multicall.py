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
async def multicall_contract(starknet: Starknet) -> StarknetContract:
    return await starknet.deploy(
        source=MULTICALL_FILE,
        constructor_calldata=[],
    )

@pytest.mark.asyncio
async def test_multicall(
    validator_contract: StarknetContract,
    multicall_contract: StarknetContract,
):
    selector = get_selector_from_name("validate_multicall")
    call_array=[
        multicall_contract.AccountCallArray(validator_contract.contract_address, selector, 0, 0),
        multicall_contract.AccountCallArray(validator_contract.contract_address, selector, 0, 0),
        multicall_contract.AccountCallArray(validator_contract.contract_address, selector, 0, 0),
    ]
    calldata=[len(call_array), validator_contract.contract_address, selector, 0, 0, validator_contract.contract_address, selector, 0, 0, validator_contract.contract_address, selector, 0, 0, 0]

    hash = invoke_tx_hash(multicall_contract.contract_address, calldata)
    signature = sign(hash, PRIVATE_KEY)

    exec_info = await multicall_contract.__execute__(
        call_array=call_array,
        calldata=[],
    ).invoke(signature=signature)
    assert exec_info.result.response[0] == 0
    assert exec_info.result.response[1] == 0
    assert exec_info.result.response[2] == 1
