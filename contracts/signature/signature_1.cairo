%lang starknet

from starkware.cairo.common.cairo_builtins import HashBuiltin
from starkware.starknet.common.syscalls import call_contract
from starkware.cairo.common.hash import hash2
from starkware.cairo.common.alloc import alloc

####################
# EXTERNAL FUNCTIONS
####################
@external
func __execute__{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
    contract_address : felt, selector : felt, calldata_len : felt, calldata : felt*
) -> (retdata_len : felt, retdata : felt*):
    assert calldata_len = 2

    let (hash) = hash2{hash_ptr=pedersen_ptr}(calldata[0], calldata[1])
    let (vec : felt*) = alloc()
    assert [vec] = hash

    let (retdata_len : felt, retdata : felt*) = call_contract(
        contract_address=contract_address, function_selector=selector, calldata_size=1, calldata=vec
    )

    return (retdata_len=retdata_len, retdata=retdata)
end
