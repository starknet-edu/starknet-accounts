%lang starknet
from starkware.cairo.common.cairo_builtins import HashBuiltin
from starkware.starknet.common.syscalls import get_caller_address

@storage_var
func variable() -> (res: felt) {
}

@storage_var
func owner() -> (res: felt) {
}

@view
func state_var{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() -> (
    var: felt, own: felt
) {
    let (var) = variable.read();
    let (own) = owner.read();
    return (var=var, own=own);
}

@view
func deployer{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() -> (res: felt) {
    let (res) = owner.read();
    return (res=res);
}

@constructor
func constructor{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(state_var: felt) {
    let (caller) = get_caller_address();
    owner.write(caller);
    variable.write(state_var);
    return ();
}
