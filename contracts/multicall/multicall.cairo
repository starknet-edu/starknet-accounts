%lang starknet

from starkware.cairo.common.cairo_builtins import HashBuiltin, SignatureBuiltin
from starkware.starknet.common.syscalls import call_contract, get_tx_info
from starkware.cairo.common.signature import verify_ecdsa_signature
from starkware.cairo.common.registers import get_fp_and_pc
from starkware.cairo.common.memcpy import memcpy
from starkware.cairo.common.alloc import alloc

####################
# STRUCTS
####################
struct Call:
    member to : felt
    member selector : felt
    member calldata_len : felt
    member calldata : felt*
end

struct AccountCallArray:
    member to : felt
    member selector : felt
    member data_offset : felt
    member data_len : felt
end

####################
# STORAGE VARIABLES
####################
@storage_var
func account_nonce() -> (res : felt):
end

####################
# GETTERS
####################
@view
func get_nonce{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (res : felt):
    let (res) = account_nonce.read()
    return (res)
end

####################
# INTERNAL FUNCTIONS
####################
func _from_call_array_to_call{syscall_ptr : felt*}(
    call_array_len : felt, call_array : AccountCallArray*, calldata : felt*, calls : Call*
):
    # if no more calls
    if call_array_len == 0:
        return ()
    end

    # parse the current call
    assert [calls] = Call(
        to=[call_array].to,
        selector=[call_array].selector,
        calldata_len=[call_array].data_len,
        calldata=calldata + [call_array].data_offset
        )
    # parse the remaining calls recursively
    _from_call_array_to_call(
        call_array_len - 1, call_array + AccountCallArray.SIZE, calldata, calls + Call.SIZE
    )
    return ()
end

func _execute_list{syscall_ptr : felt*}(calls_len : felt, calls : Call*, response : felt*) -> (
    response_len : felt
):
    alloc_locals

    # if no more calls
    if calls_len == 0:
        return (0)
    end

    # do the current call
    let this_call : Call = [calls]
    let res = call_contract(
        contract_address=this_call.to,
        function_selector=this_call.selector,
        calldata_size=this_call.calldata_len,
        calldata=this_call.calldata,
    )
    # copy the result in response
    memcpy(response, res.retdata, res.retdata_size)
    # do the next calls recursively
    let (response_len) = _execute_list(
        calls_len - 1, calls + Call.SIZE, response + res.retdata_size
    )
    return (response_len + res.retdata_size)
end

####################
# EXTERNAL FUNCTIONS
####################
@external
func __execute__{
    syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr, ecdsa_ptr : SignatureBuiltin*
}(
    nonce : felt,
    call_array_len : felt,
    call_array : AccountCallArray*,
    calldata_len : felt,
    calldata : felt*,
) -> (response_len : felt, response : felt*):
    alloc_locals
    let (__fp__, _) = get_fp_and_pc()

    let (calls : Call*) = alloc()
    _from_call_array_to_call(call_array_len, call_array, calldata, calls)
    let calls_len = call_array_len

    # execute call
    let (response : felt*) = alloc()
    let (response_len) = _execute_list(calls_len, calls, response)

    return (response_len=response_len, response=response)
end
