import os
import json
import pytest

from utils import invoke_tx_hash
from starkware.starknet.testing.starknet import Starknet
from starkware.starknet.testing.contract import StarknetContract
from starkware.starknet.public.abi import get_selector_from_name
from starkware.crypto.signature.signature import sign
from starkware.crypto.signature.signature import private_to_stark_key

with open("../contracts/config.json", "r") as f:
  data = json.load(f)

# The path to the contract source code.
MULTISIG_FILE = os.path.join("../contracts/multisig", "multisig.cairo")
SIGNATURE_BASIC_FILE = os.path.join("../contracts/multisig", "signature_basic.cairo")

priv_1 = data['PRIVATE_KEY'] + 1
pub_1 = private_to_stark_key(priv_1)

priv_2 = data['PRIVATE_KEY'] + 2
pub_2 = private_to_stark_key(priv_2)

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
async def signer_1(starknet: Starknet) -> StarknetContract:
    return await starknet.deploy(
        source=SIGNATURE_BASIC_FILE,
        constructor_calldata=[data['PUBLIC_KEY']],
    )


@pytest.fixture
async def signer_2(starknet: Starknet) -> StarknetContract:
    return await starknet.deploy(
        source=SIGNATURE_BASIC_FILE,
        constructor_calldata=[pub_1],
    )

@pytest.fixture
async def signer_3(starknet: Starknet) -> StarknetContract:
    return await starknet.deploy(
        source=SIGNATURE_BASIC_FILE,
        constructor_calldata=[pub_2],
    )

@pytest.mark.asyncio
async def test_multicall(
    starknet: Starknet,
    signer_1: StarknetContract,
    signer_2: StarknetContract,
    signer_3: StarknetContract,
    evaluator: StarknetContract,
):
    multisig_contract = await starknet.deploy(
        source=MULTISIG_FILE,
        constructor_calldata=[
            3,
            signer_1.contract_address,
            signer_2.contract_address,
            signer_3.contract_address
        ],
    )
    
    #
    # submit initial multicall transaction
    #
    validator_selector = get_selector_from_name("validate_multisig")
    submit_selector = get_selector_from_name("submit_tx")
    submit_event_selector = get_selector_from_name("submit")

    nonce_info = await signer_1.get_nonce().call()
    nonce = nonce_info.result.res

    inner_calldata=[evaluator.contract_address, validator_selector, 2, 1, data['DUMMY_ACCOUNT']]
    outer_calldata=[multisig_contract.contract_address, submit_selector, nonce, len(inner_calldata), *inner_calldata]

    hash = invoke_tx_hash(data, signer_1.contract_address, outer_calldata)
    signature = sign(hash, data['PRIVATE_KEY'])

    exec_info_1 = await signer_1.__execute__(
        contract_address=multisig_contract.contract_address,
        selector=submit_selector,
        nonce=nonce,
        calldata=inner_calldata,
    ).invoke(signature=signature)

    submit_event = exec_info_1.raw_events[0]
    tx_index = submit_event.data[1]
    assert submit_event.keys[0] == submit_event_selector

    #
    # first transaction confirmation
    #
    confirm_selector = get_selector_from_name("confirm_tx")
    confirm_event_selector = get_selector_from_name("confirm")

    nonce_2_info = await signer_2.get_nonce().call()
    nonce_2 = nonce_2_info.result.res

    calldata_2=[multisig_contract.contract_address, confirm_selector, nonce_2, 1, tx_index]
    hash_2 = invoke_tx_hash(data, signer_2.contract_address, calldata_2)
    signature_2 = sign(hash_2, priv_1)

    exec_info_2 = await signer_2.__execute__(
        contract_address=multisig_contract.contract_address,
        selector=confirm_selector,
        nonce=nonce_2,
        calldata=[tx_index],
    ).invoke(signature=signature_2)

    confirm_event = exec_info_2.raw_events[0]
    assert confirm_event.keys[0] == confirm_event_selector

    #
    # second transaction confirmation
    #
    nonce_3_info = await signer_3.get_nonce().call()
    nonce_3 = nonce_3_info.result.res

    calldata_3=[multisig_contract.contract_address, confirm_selector, nonce_3, 1, tx_index]
    hash_3 = invoke_tx_hash(data, signer_3.contract_address, calldata_3)
    signature_3 = sign(hash_3, priv_2)

    exec_info_3 = await signer_3.__execute__(
        contract_address=multisig_contract.contract_address,
        selector=confirm_selector,
        nonce=nonce_3,
        calldata=[tx_index],
    ).invoke(signature=signature_3)

    confirm_event_final = exec_info_3.raw_events[0]
    assert confirm_event_final.keys[0] == confirm_event_selector

    #
    # enough transactions to execute
    #
    execute_selector = get_selector_from_name("__execute__")
    execute_event_selector = get_selector_from_name("execute")
    exec_calldata=[multisig_contract.contract_address, execute_selector, nonce+1, 1, tx_index]

    exec_hash = invoke_tx_hash(data, signer_1.contract_address, exec_calldata)
    exec_signature = sign(exec_hash, data['PRIVATE_KEY'])

    exec_info = await signer_1.__execute__(
        contract_address=multisig_contract.contract_address,
        selector=execute_selector,
        nonce=nonce+1,
        calldata=[tx_index],
    ).invoke(signature=exec_signature)

    exec_event = exec_info.raw_events[0]
    assert exec_event.keys[0] == execute_event_selector
