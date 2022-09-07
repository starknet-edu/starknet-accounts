%lang starknet

from starkware.cairo.common.cairo_builtins import HashBuiltin, SignatureBuiltin
from starkware.starknet.common.syscalls import call_contract, get_tx_info
from starkware.cairo.common.signature import verify_ecdsa_signature
from starkware.cairo.common.math import assert_not_zero

//###################
// STORAGE VARIABLES
//###################
@storage_var
func public_key() -> (res: felt) {
}

@storage_var
func account_nonce() -> (res: felt) {
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
@view
func get_nonce{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() -> (res: felt) {
    let (res) = account_nonce.read();
    return (res,);
}

@view
func get_signer{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() -> (res: felt) {
    let (res) = public_key.read();
    return (res,);
}

@view
func is_valid_signature{
    syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr, ecdsa_ptr: SignatureBuiltin*
}(hash: felt, signature_len: felt, signature: felt*) -> () {
    let (_public_key) = public_key.read();

    let sig_r = signature[0];
    let sig_s = signature[1];

    verify_ecdsa_signature(
        message=hash, public_key=_public_key, signature_r=sig_r, signature_s=sig_s
    );

    return ();
}

//###################
// EXTERNAL FUNCTIONS
//###################
@external
func __execute__{
    syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr, ecdsa_ptr: SignatureBuiltin*
}(contract_address: felt, selector: felt, nonce: felt, calldata_len: felt, calldata: felt*) -> (
    retdata_len: felt, retdata: felt*
) {
    let (tx_info) = get_tx_info();
    assert_not_zero(tx_info.signature_len);

    is_valid_signature(tx_info.transaction_hash, tx_info.signature_len, tx_info.signature);

    let (curr_nonce) = account_nonce.read();
    assert curr_nonce = nonce;
    account_nonce.write(curr_nonce + 1);

    let (retdata_len: felt, retdata: felt*) = call_contract(
        contract_address=contract_address,
        function_selector=selector,
        calldata_size=calldata_len,
        calldata=calldata,
    );

    return (retdata_len=retdata_len, retdata=retdata);
}
