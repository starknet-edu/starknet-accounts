%lang starknet

from starkware.cairo.common.cairo_builtins import HashBuiltin
from starkware.starknet.common.syscalls import call_contract
from starkware.cairo.common.signature import verify_ecdsa_signature
from starkware.cairo.common.alloc import alloc

####################
# STORAGE VARIABLES
####################
@storage_var
func public_key() -> (res : felt):
end

#
# ACTION_ITEM 1: implement '@storage_var' account_nonce()
#
@storage_var
#
# <CODE>
#

####################
# CONSTRUCTOR
####################
@constructor
func constructor{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(pub_key : felt):
    public_key.write(pub_key)
    return ()
end

####################
# GETTERS
####################
#
# MISSION 1
#
@view
func get_nonce{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (res : felt):
    let (res) = account_nonce.read()
    return (res)
end

#
# MISSION 2
#
@view
func get_signer{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
    res : felt
):
    let (res) = public_key.read()
    return (res)
end

####################
# EXTERNAL FUNCTIONS
####################
@external
func __execute__{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
    contract_address : felt, selector : felt, calldata_len : felt, calldata : felt*
) -> (retdata_len : felt, retdata : felt*):
    let (_current_nonce) = account_nonce.read()
    assert _current_nonce = calldata[0]

    #
    # ACTION ITEM 2: increment `account_nonce` for each transaction signature
    #

    #
    # <CODE>
    #

    let (vec : felt*) = alloc()
    assert [vec] = _current_nonce + 1
    assert [vec + 1] = calldata[1]

    let (retdata_len : felt, retdata : felt*) = call_contract(
        contract_address=contract_address, function_selector=selector, calldata_size=2, calldata=vec
    )

    return (retdata_len=retdata_len, retdata=retdata)
end
