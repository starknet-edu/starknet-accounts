%lang starknet

from starkware.cairo.common.cairo_builtins import HashBuiltin, SignatureBuiltin
from starkware.starknet.common.syscalls import call_contract, get_caller_address, get_tx_info
from starkware.cairo.common.math import assert_not_zero, assert_le
from starkware.cairo.common.signature import verify_ecdsa_signature
from starkware.cairo.common.alloc import alloc
from starkware.cairo.common.bool import TRUE, FALSE

// ///////////////////
// STRUCTS
// ///////////////////
struct Transaction {
    contract_address: felt,
    function_selector: felt,
    calldata_len: felt,
}

// ///////////////////
// INTERFACES
// ///////////////////
@contract_interface
namespace IAccount {
    func is_valid_signature(hash: felt, signature_len: felt, signature: felt*) {
    }
}

// ///////////////////
// STORAGE VARIABLES
// ///////////////////
@storage_var
func owners(index: felt) -> (owner: felt) {
}

@storage_var
func owners_map(owner: felt) -> (index: felt) {
}

@storage_var
func num_owners() -> (res: felt) {
}

@storage_var
func curr_tx_index() -> (res: felt) {
}

@storage_var
func tx_confirms(tx_index: felt) -> (num_confirms: felt) {
}

@storage_var
func tx_is_executed(tx_index: felt) -> (is_executed: felt) {
}

@storage_var
func has_confirmed(tx_index: felt, owner: felt) -> (confirmed: felt) {
}

@storage_var
func transactions(tx_index: felt) -> (tx: Transaction) {
}

@storage_var
func transaction_calldata(tx_index: felt, calldata_index: felt) -> (value: felt) {
}

// ///////////////////
// EVENTS
// ///////////////////
@event
func submit(owner: felt, tx_index: felt) {
}

@event
func confirm(owner: felt, tx_index: felt) {
}

@event
func executed(tx_index: felt) {
}

// ///////////////////
// CONSTRUCTOR
// ///////////////////
@constructor
func constructor{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    owners_len: felt, owners: felt*
) {
    assert_le(3, owners_len);
    num_owners.write(owners_len);
    _set_owners(owners_len=owners_len, new_owners=owners);

    return ();
}

// ///////////////////
// GETTERS
// ///////////////////
@view
func get_confirmations{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    tx_index: felt
) -> (res: felt) {
    let (res) = tx_confirms.read(tx_index);
    return (res,);
}

@view
func get_owner_confirmed{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    tx_index: felt, owner: felt
) -> (res: felt) {
    let (res) = has_confirmed.read(tx_index, owner);
    return (res,);
}

@view
func get_num_owners{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() -> (
    res: felt
) {
    let (res) = num_owners.read();
    return (res,);
}

@view
func get_owners{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() -> (
    signers_len: felt, signers: felt*
) {
    alloc_locals;
    let (signers_len) = num_owners.read();

    let (signers) = alloc();
    _get_signers(0, signers_len, signers);
    return (signers_len=signers_len, signers=signers);
}

// ///////////////////
// INTERNAL FUNCTIONS
// ///////////////////
func _require_owner{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() {
    let (caller) = get_caller_address();
    let (index) = owners_map.read(owner=caller);
    with_attr error_message("not owner") {
        assert_not_zero(index);
    }

    return ();
}

func _set_owners{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    owners_len: felt, new_owners: felt*
) {
    if (owners_len == 0) {
        return ();
    }

    owners.write(index=owners_len, value=[new_owners]);
    owners_map.write(owner=[new_owners], value=owners_len);
    _set_owners(owners_len=owners_len - 1, new_owners=new_owners + 1);
    return ();
}

func _spread_calldata{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    tx_index: felt, calldata_index: felt, calldata_len: felt, calldata: felt*
) {
    if (calldata_index == calldata_len) {
        return ();
    }

    transaction_calldata.write(tx_index, calldata_index, calldata[calldata_index]);

    _spread_calldata(tx_index, calldata_index + 1, calldata_len, calldata);
    return ();
}

func _pack_calldata{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    tx_index: felt, calldata_index: felt, calldata_len: felt, calldata: felt*
) {
    if (calldata_index == calldata_len) {
        return ();
    }

    let (calldata_val) = transaction_calldata.read(tx_index, calldata_index);
    assert calldata[calldata_index] = calldata_val;
    _pack_calldata(tx_index, calldata_index + 1, calldata_len, calldata);
    return ();
}

func _get_signers{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    signer_idx: felt, signers_len: felt, signers: felt*
) {
    if (signer_idx == signers_len) {
        return ();
    }

    let (owner) = owners.read(signer_idx + 1);
    assert_not_zero(owner);
    assert signers[signer_idx] = owner;

    _get_signers(signer_idx + 1, signers_len, signers);
    return ();
}

// ///////////////////
// EXTERNAL FUNCTIONS
// ///////////////////
@external
func submit_tx{
    syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr, ecdsa_ptr: SignatureBuiltin*
}(contract_address: felt, function_selector: felt, calldata_len: felt, calldata: felt*) {
    alloc_locals;
    _require_owner();

    let (caller) = get_caller_address();
    let (tx_info) = get_tx_info();
    IAccount.is_valid_signature(
        caller, tx_info.transaction_hash, tx_info.signature_len, tx_info.signature
    );

    let (tx_index) = curr_tx_index.read();
    transactions.write(tx_index, Transaction(contract_address, function_selector, calldata_len));
    _spread_calldata(tx_index, 0, calldata_len, calldata);

    curr_tx_index.write(tx_index + 1);

    submit.emit(caller, tx_index);
    return ();
}

@external
func confirm_tx{
    syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr, ecdsa_ptr: SignatureBuiltin*
}(tx_index: felt) {
    alloc_locals;
    _require_owner();

    let (tx: Transaction) = transactions.read(tx_index);
    assert_not_zero(tx.contract_address);

    let (num_confirmations) = tx_confirms.read(tx_index);
    let (executed) = tx_is_executed.read(tx_index);
    assert executed = FALSE;

    let (caller) = get_caller_address();
    let (tx_info) = get_tx_info();

    IAccount.is_valid_signature(
        caller, tx_info.transaction_hash, tx_info.signature_len, tx_info.signature
    );

    let (confirmed) = has_confirmed.read(tx_index, caller);
    assert confirmed = FALSE;

    tx_confirms.write(tx_index, num_confirmations + 1);
    has_confirmed.write(tx_index, caller, TRUE);

    confirm.emit(caller, tx_index);
    return ();
}

@external
func execute{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    tx_index: felt
) -> (retdata_len: felt, retdata: felt*) {
    alloc_locals;
    _require_owner();

    let (tx: Transaction) = transactions.read(tx_index);
    assert_not_zero(tx.contract_address);

    let (num_confirmations) = tx_confirms.read(tx_index);
    let (exec) = tx_is_executed.read(tx_index);
    assert exec = FALSE;

    let (owners_len) = num_owners.read();
    with_attr error_message("need more confirmations") {
        assert_le(owners_len - 1, num_confirmations);
    }

    tx_is_executed.write(tx_index, TRUE);

    let (calldata) = alloc();
    _pack_calldata(tx_index, 0, tx.calldata_len, calldata);
    assert calldata[tx.calldata_len] = tx_index;

    executed.emit(tx_index);
    let (retdata_len: felt, retdata: felt*) = call_contract(
        contract_address=tx.contract_address,
        function_selector=tx.function_selector,
        calldata_size=tx.calldata_len + 1,
        calldata=calldata,
    );

    return (retdata_len=retdata_len, retdata=retdata);
}
