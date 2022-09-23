%lang starknet

from starkware.cairo.common.cairo_builtins import HashBuiltin
from starkware.starknet.common.syscalls import call_contract
from starkware.cairo.common.hash import hash2
from starkware.cairo.common.alloc import alloc

// ///////////////////
// EXTERNAL FUNCTIONS
// ///////////////////
@external
func __validate__{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    contract_address: felt, selector: felt, calldata_len: felt, calldata: felt*
) {
    return ();
}

@external
func __validate_declare__{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    class_hash: felt
) {
    return ();
}

@external
func __execute__{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    contract_address: felt, selector: felt, calldata_len: felt, calldata: felt*
) -> (retdata_len: felt, retdata: felt*) {
    let (hash) = hash2{hash_ptr=pedersen_ptr}(calldata[0], calldata[1]);
    let (vec: felt*) = alloc();
    assert [vec] = hash;
    assert [vec + 1] = calldata[2];

    let (retdata_len: felt, retdata: felt*) = call_contract(
        contract_address=contract_address, function_selector=selector, calldata_size=2, calldata=vec
    );

    return (retdata_len=retdata_len, retdata=retdata);
}
