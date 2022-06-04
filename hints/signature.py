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
INPUT_1 = 2938
INPUT_2 = 4337

@pytest.fixture
async def starknet() -> Starknet:
    return await Starknet.empty()

@pytest.fixture
async def validator(starknet: Starknet) -> StarknetContract:
    return await starknet.deploy(
        source=VALIDATOR_FILE,
        constructor_calldata=[PRIVATE_KEY, PUBLIC_KEY, INPUT_1, INPUT_2],
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
        constructor_calldata=[PUBLIC_KEY],
    )

@pytest.fixture
async def signature_3(starknet: Starknet) -> StarknetContract:
    return await starknet.deploy(
        source=SIGNATURE_3_FILE,
        constructor_calldata=[PUBLIC_KEY],
    )

@pytest.mark.asyncio
async def test_signature_1(
    starknet: Starknet,
    validator: StarknetContract,
    signature_1: StarknetContract,
):
    ACT = await starknet.deploy(
        source=ACT_FILE,
        constructor_calldata=[validator.contract_address],
    )
    await validator.set_rewards_contract(addr=ACT.contract_address).invoke()

    hash = pedersen_hash(INPUT_1, INPUT_2)
    hash_final = pedersen_hash(hash, signature_1.contract_address)
    signature = sign(hash_final, PRIVATE_KEY)

    selector = get_selector_from_name("validate_signature_1")
    exec_info = await signature_1.__execute__(
        contract_address=validator.contract_address,
        selector=selector,
        calldata=[INPUT_1, INPUT_2, DUMMY_ACCOUNT],
    ).invoke(signature=signature)
    assert exec_info.result.retdata[0] == 1

    balance = await ACT.balanceOf(account=DUMMY_ACCOUNT).call()
    assert balance.result.balance.low == 100000000000000000000

@pytest.mark.asyncio
async def test_signature_2(
    starknet: Starknet,
    validator: StarknetContract,
    signature_2: StarknetContract,
):
    ACT = await starknet.deploy(
        source=ACT_FILE,
        constructor_calldata=[validator.contract_address],
    )
    await validator.set_rewards_contract(addr=ACT.contract_address).invoke()

    selector = get_selector_from_name("validate_signature_2")
    calldata=[validator.contract_address, selector, 2, 1, DUMMY_ACCOUNT]

    hash = invoke_tx_hash(signature_2.contract_address, calldata)
    signature = sign(hash, PRIVATE_KEY)

    exec_info_1 = await signature_2.__execute__(
        contract_address=validator.contract_address,
        selector=selector,
        calldata=[hash, 1, DUMMY_ACCOUNT],
    ).invoke(signature=signature)

    assert exec_info_1.result.retdata[0] == 0

    exec_info_2 = await signature_2.__execute__(
        contract_address=validator.contract_address,
        selector=selector,
        calldata=[hash, 2, DUMMY_ACCOUNT],
    ).invoke(signature=signature)
    assert exec_info_2.result.retdata[0] == 1
    
    balance = await ACT.balanceOf(account=DUMMY_ACCOUNT).call()
    assert balance.result.balance.low == 200000000000000000000

@pytest.mark.asyncio
async def test_signature_3(
    starknet: Starknet,
    validator: StarknetContract,
    signature_3: StarknetContract,
):
    ACT = await starknet.deploy(
        source=ACT_FILE,
        constructor_calldata=[validator.contract_address],
    )
    await validator.set_rewards_contract(addr=ACT.contract_address).invoke()

    nonce_info = await signature_3.get_nonce().call()
    assert nonce_info.result.res == 0
    nonce = nonce_info.result.res

    selector = get_selector_from_name("validate_signature_3")
    calldata=[validator.contract_address, selector, 2, nonce, DUMMY_ACCOUNT]

    hash = invoke_tx_hash(signature_3.contract_address, calldata)
    hash_final = pedersen_hash(hash, nonce)

    signature = sign(hash_final, PRIVATE_KEY)

    exec_info = await signature_3.__execute__(
        contract_address=validator.contract_address,
        selector=selector,
        calldata=[nonce, DUMMY_ACCOUNT],
    ).invoke(signature=signature)
    assert exec_info.result.retdata[0] == 1

    balance = await ACT.balanceOf(account=DUMMY_ACCOUNT).call()
    assert balance.result.balance.low == 300000000000000000000
