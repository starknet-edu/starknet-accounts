%lang starknet

from starkware.cairo.common.cairo_builtins import HashBuiltin, SignatureBuiltin, BitwiseBuiltin
from starkware.starknet.common.syscalls import call_contract, get_tx_info
from starkware.cairo.common.alloc import alloc
from starkware.cairo.common.registers import get_fp_and_pc
from starkware.cairo.common.math import split_felt
from starkware.cairo.common.uint256 import Uint256
from starkware.cairo.common.bool import TRUE
from starkware.cairo.common.cairo_secp.signature import verify_eth_signature_uint256

// ///////////////////
// STORAGE VARIABLES
// ///////////////////
@storage_var
func ethereum_address() -> (res: felt) {
}

// ///////////////////
// CONSTRUCTOR
// ///////////////////
@constructor
func constructor{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(pub_key: felt) {
    ethereum_address.write(pub_key);
    return ();
}

func _is_valid_eth_signature{
    syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, bitwise_ptr: BitwiseBuiltin*, range_check_ptr
}(hash: felt, signature_len: felt, signature: felt*) -> (is_valid: felt) {
    alloc_locals;
    let (_public_key) = ethereum_address.read();
    let (__fp__, _) = get_fp_and_pc();

    let sig_v: felt = signature[0];
    let sig_r: Uint256 = Uint256(low=signature[1], high=signature[2]);
    let sig_s: Uint256 = Uint256(low=signature[3], high=signature[4]);
    let (high, low) = split_felt(hash);
    let msg_hash: Uint256 = Uint256(low=low, high=high);

    let (local keccak_ptr: felt*) = alloc();

    with keccak_ptr {
        verify_eth_signature_uint256(
            msg_hash=msg_hash, r=sig_r, s=sig_s, v=sig_v, eth_address=_public_key
        );
    }

    return (is_valid=TRUE);
}

// ///////////////////
// GETTERS
// ///////////////////
@view
func get_public_key{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() -> (
    public_key: felt
) {
    let (_public_key) = ethereum_address.read();
    return (public_key=_public_key);
}

@view
func is_valid_signature{
    syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, bitwise_ptr: BitwiseBuiltin*, range_check_ptr
}(hash: felt, signature_len: felt, signature: felt*) -> () {
    _is_valid_eth_signature(hash, signature_len, signature);

    return ();
}

// ///////////////////
// EXTERNAL FUNCTIONS
// ///////////////////
@external
func __validate__{
    syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, bitwise_ptr: BitwiseBuiltin*, range_check_ptr
}(contract_address: felt, selector: felt, calldata_len: felt, calldata: felt*) {
    let (tx_info) = get_tx_info();
    _is_valid_eth_signature(tx_info.transaction_hash, tx_info.signature_len, tx_info.signature);

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
