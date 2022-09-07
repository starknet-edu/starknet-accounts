%lang starknet

from starkware.cairo.common.cairo_builtins import HashBuiltin, SignatureBuiltin
from starkware.starknet.common.syscalls import call_contract, get_tx_info
from starkware.cairo.common.signature import verify_ecdsa_signature
from starkware.cairo.common.alloc import alloc

//###################
// STORAGE VARIABLES
//###################
@storage_var
func public_key() -> (res: felt) {
}

//###################
// CONSTRUCTOR
//###################
@constructor
func constructor{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(pub_key: felt) {
    public_key.write(pub_key);
    return ();
}

//###################
// GETTERS
//###################
//
// ACTION ITEM 1: verify the provided signature with std library `verify_ecdsa_signature`
// - reference: https://github.com/starkware-libs/cairo-lang/blob/master/src/starkware/cairo/common/signature.cairo
//
@view
func is_valid_signature{
    syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr, ecdsa_ptr: SignatureBuiltin*
}(hash: felt, signature_len: felt, signature: felt*) -> () {
    let (_public_key) = public_key.read();

    //
    // <CODE>
    //

    return ();
}

//###################
// EXTERNAL FUNCTIONS
//###################
@external
func __execute__{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    contract_address: felt, selector: felt, calldata_len: felt, calldata: felt*
) -> (retdata_len: felt, retdata: felt*) {
    let (tx_info) = get_tx_info();

    let (vec: felt*) = alloc();
    assert [vec] = calldata[0];
    assert [vec + 1] = tx_info.signature[0];
    assert [vec + 2] = tx_info.signature[1];
    assert [vec + 3] = calldata[2];

    let (retdata_len: felt, retdata: felt*) = call_contract(
        contract_address=contract_address, function_selector=selector, calldata_size=4, calldata=vec
    );

    return (retdata_len=retdata_len, retdata=retdata);
}
