%lang starknet

from starkware.cairo.common.cairo_builtins import HashBuiltin, SignatureBuiltin
from starkware.starknet.common.syscalls import call_contract, get_tx_info
from starkware.cairo.common.signature import verify_ecdsa_signature
from starkware.cairo.common.alloc import alloc
from tutorial.secp.bigint import BigInt3
from tutorial.secp.secp import verify_ecdsa
from tutorial.secp.secp_ec import EcPoint

//###################
// STORAGE VARIABLES
//###################
@storage_var
func public_key() -> (public_key_pt: EcPoint) {
}

@storage_var
func account_nonce() -> (res: felt) {
}

//###################
// CONSTRUCTOR
//###################
@constructor
func constructor{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    pub_key: EcPoint
) {
    public_key.write(pub_key);
    return ();
}

//###################
// GETTERS
//###################
//
// ACTION ITEM 1: implement a secp256 signature verification
// - reference: https://github.com/starkware-libs/cairo-examples/blob/master/secp/secp_example.cairo
//
@view
func is_valid_signature{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    hash: BigInt3, sig_r: BigInt3, sig_s: BigInt3
) -> () {
    alloc_locals;
    let (_public_key_pt: EcPoint) = public_key.read();

    //
    // <CODE>
    //

    return ();
}

@view
func get_nonce{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() -> (res: felt) {
    let (res) = account_nonce.read();
    return (res,);
}

@view
func get_public_key{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() -> (
    pub_key: EcPoint
) {
    let (pub_key) = public_key.read();
    return (pub_key,);
}

//###################
// EXTERNAL FUNCTIONS
//###################
@external
func __execute__{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    contract_address: felt, selector: felt, nonce: felt, calldata_len: felt, calldata: felt*
) -> (retdata_len: felt, retdata: felt*) {
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
