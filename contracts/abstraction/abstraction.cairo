%lang starknet

from starkware.cairo.common.cairo_builtins import HashBuiltin, SignatureBuiltin
from starkware.starknet.common.syscalls import call_contract, get_tx_info
from starkware.cairo.common.signature import verify_ecdsa_signature
from starkware.cairo.common.alloc import alloc
from cairo_examples.secp.bigint import BigInt3
from cairo_examples.secp.secp import verify_ecdsa
from cairo_examples.secp.secp_ec import EcPoint

####################
# STORAGE VARIABLES
####################
@storage_var
func public_key() -> (public_key_pt : EcPoint):
end

####################
# CONSTRUCTOR
####################
@constructor
func constructor{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
    pub_key : EcPoint
):
    public_key.write(pub_key)
    return ()
end

####################
# GETTERS
####################
@view
func is_valid_signature{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
    hash : BigInt3, sig_r : BigInt3, sig_s : BigInt3
) -> ():
    alloc_locals
    let (_public_key_pt : EcPoint) = public_key.read()

    verify_ecdsa(public_key_pt=_public_key_pt, msg_hash=hash, r=sig_r, s=sig_s)

    return ()
end

@view
func get_public_key{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (pub_key : EcPoint):
    let (pub_key) = public_key.read()
    return (pub_key)
end

####################
# EXTERNAL FUNCTIONS
####################
@external
func __execute__{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
    contract_address : felt, selector : felt, calldata_len : felt, calldata : felt*
) -> (retdata_len : felt, retdata : felt*):
    let (retdata_len : felt, retdata : felt*) = call_contract(
        contract_address=contract_address,
        function_selector=selector,
        calldata_size=calldata_len,
        calldata=calldata,
    )

    return (retdata_len=retdata_len, retdata=retdata)
end
