%lang starknet

from starkware.cairo.common.cairo_builtins import HashBuiltin, SignatureBuiltin
from starkware.starknet.common.syscalls import call_contract, get_tx_info
from starkware.cairo.common.signature import verify_ecdsa_signature
from starkware.cairo.common.registers import get_fp_and_pc
from starkware.cairo.common.memcpy import memcpy
from starkware.cairo.common.alloc import alloc

// ///////////////////
// STRUCTS
// ///////////////////
struct Call {
    to: felt,
    selector: felt,
    calldata_len: felt,
    calldata: felt*,
}

struct AccountCallArray {
    to: felt,
    selector: felt,
    data_offset: felt,
    data_len: felt,
}

// ///////////////////
// INTERNAL FUNCTIONS
// ///////////////////
func _from_call_array_to_call{syscall_ptr: felt*}(
    call_array_len: felt, call_array: AccountCallArray*, calldata: felt*, calls: Call*
) {
    if (call_array_len == 0) {
        return ();
    }

    //
    // ACTION ITEM 1: format the calldata into individual calls
    // - reference: https://github.com/OpenZeppelin/cairo-contracts/blob/main/src/openzeppelin/account/library.cairo
    //
    assert [calls] = Call(
        // CODE HERE
        );
    _from_call_array_to_call(
        call_array_len - 1, call_array + AccountCallArray.SIZE, calldata, calls + Call.SIZE
    );
    return ();
}

func _execute_list{syscall_ptr: felt*}(calls_len: felt, calls: Call*, response: felt*) -> (
    response_len: felt
) {
    alloc_locals;

    if (calls_len == 0) {
        return (0,);
    }

    let this_call: Call = [calls];
    //
    // ACTION ITEM 2: recursively call the contracts
    // - reference: https://github.com/OpenZeppelin/cairo-contracts/blob/main/src/openzeppelin/account/library.cairo
    //
    let res = call_contract(
        // CODE HERE
    );

    memcpy(response, res.retdata, res.retdata_size);
    let (response_len) = _execute_list(
        calls_len - 1, calls + Call.SIZE, response + res.retdata_size
    );
    return (response_len + res.retdata_size,);
}

// ///////////////////
// EXTERNAL FUNCTIONS
// ///////////////////
@external
func __validate__{
    syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, ecdsa_ptr: SignatureBuiltin*, range_check_ptr
}(call_array_len: felt, call_array: AccountCallArray*, calldata_len: felt, calldata: felt*) {
    return ();
}

@external
func __validate_declare__{
    syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, ecdsa_ptr: SignatureBuiltin*, range_check_ptr
}(class_hash: felt) {
    return ();
}

@external
func __execute__{
    syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr, ecdsa_ptr: SignatureBuiltin*
}(
    call_array_len: felt,
    call_array: AccountCallArray*,
    calldata_len: felt,
    calldata: felt*,
) -> (response_len: felt, response: felt*) {
    alloc_locals;

    let (calls: Call*) = alloc();
    _from_call_array_to_call(call_array_len, call_array, calldata, calls);
    let calls_len = call_array_len;

    // execute call
    let (response: felt*) = alloc();
    let (response_len) = _execute_list(calls_len, calls, response);

    return (response_len=response_len, response=response);
}
