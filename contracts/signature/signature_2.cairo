%lang starknet

from starkware.cairo.common.cairo_builtins import HashBuiltin, SignatureBuiltin
from starkware.starknet.common.syscalls import call_contract, get_tx_info
from starkware.cairo.common.signature import verify_ecdsa_signature

// ///////////////////
// STORAGE VARIABLES
// ///////////////////
@storage_var
func public_key() -> (res: felt) {
}

// ///////////////////
// CONSTRUCTOR
// ///////////////////
@constructor
func constructor{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(pub_key: felt) {
    public_key.write(pub_key);
    return ();
}

func _is_valid_signature{
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

// ///////////////////
// GETTERS
// ///////////////////
@view
func get_public_key{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() -> (
    public_key: felt
) {
    let (_public_key) = public_key.read();
    return (public_key=_public_key);
}

@view
func is_valid_signature{
    syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr, ecdsa_ptr: SignatureBuiltin*
}(hash: felt, signature_len: felt, signature: felt*) -> () {
    _is_valid_signature(hash, signature_len, signature);

    return ();
}

// ///////////////////
// EXTERNAL FUNCTIONS
// ///////////////////
@external
func __validate__{
    syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr, ecdsa_ptr: SignatureBuiltin*
}(contract_address: felt, selector: felt, calldata_len: felt, calldata: felt*) {
    let (tx_info) = get_tx_info();
    _is_valid_signature(tx_info.transaction_hash, tx_info.signature_len, tx_info.signature);

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
    let (retdata_len: felt, retdata: felt*) = call_contract(
        contract_address=contract_address,
        function_selector=selector,
        calldata_size=calldata_len,
        calldata=calldata,
    );

    return (retdata_len=retdata_len, retdata=retdata);
}
