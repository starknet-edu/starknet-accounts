from starkware.python.utils import from_bytes
from starkware.starknet.public.abi import get_selector_from_name
from starkware.starknet.core.os.transaction_hash.transaction_hash import TransactionHashPrefix, calculate_transaction_hash_common

def invoke_tx_hash(data, addr, calldata):
    exec_selector = get_selector_from_name("__execute__")
    return calculate_transaction_hash_common(
        tx_hash_prefix=TransactionHashPrefix.INVOKE,
        version=data['VERSION'],
        contract_address=addr,
        entry_point_selector=exec_selector,
        calldata=calldata,
        max_fee=0,
        chain_id=from_bytes(b"SN_GOERLI"),
        additional_data=[],
    )
    