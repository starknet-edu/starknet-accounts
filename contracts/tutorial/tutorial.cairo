// ######## Ex 00
// # A contract from which other contracts can import functions
%lang starknet

from starkware.cairo.common.cairo_builtins import HashBuiltin
from starkware.cairo.common.uint256 import Uint256
from starkware.cairo.common.math import assert_not_zero
from starkware.starknet.common.syscalls import get_caller_address

from contracts.tutorial.ITutorial import ITutorial
from contracts.tutorial.IPlayerRegistry import IPlayerRegistry

//
// CONSTANTS
//
const ERC20_BASE = 1000000000000000000;

//
// STORAGE VARIABLES
//
@storage_var
func tutorial_erc20_address() -> (tuto_erc20_address_address: felt) {
}

@storage_var
func players_registry() -> (players_registry_address: felt) {
}

@storage_var
func workshop_id() -> (workshop_id: felt) {
}

@storage_var
func teacher_accounts(account: felt) -> (balance: felt) {
}

@storage_var
func max_rank() -> (max_rank: felt) {
}

@storage_var
func next_rank() -> (next_rank: felt) {
}

@storage_var
func random_attributes(rank: felt, column: felt) -> (value: felt) {
}

@storage_var
func assigned_rank(player_address: felt) -> (rank: felt) {
}

//
// GETTERS
//
@view
func get_tutorial_erc20_address{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    ) -> (addr: felt) {
    let (addr) = tutorial_erc20_address.read();
    return (addr,);
}

@view
func get_players_registry{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() -> (
    _players_registry: felt
) {
    let (_players_registry) = players_registry.read();
    return (_players_registry,);
}

@view
func has_validated_exercise{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    account: felt, exercise_id: felt
) -> (has_validated_exercise: felt) {
    let (_players_registry) = players_registry.read();
    let (_workshop_id) = workshop_id.read();
    let (has_validated) = IPlayerRegistry.check_validated_exercise(
        contract_address=_players_registry,
        account=account,
        workshop=_workshop_id,
        exercise=exercise_id,
    );
    return (has_validated,);
}

@view
func get_next_rank{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() -> (
    rank: felt
) {
    let (rank) = next_rank.read();
    return (rank,);
}

@view
func get_assigned_rank{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    player_address: felt
) -> (rank: felt) {
    let (rank) = assigned_rank.read(player_address);
    return (rank,);
}

@view
func is_teacher{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(account: felt) -> (
    permission: felt
) {
    let (permission: felt) = teacher_accounts.read(account);
    return (permission,);
}

//
// LIBRARY FUNCTIONS
//
func ex_initializer{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    _erc20_address: felt, _players_registry: felt, _workshop_id: felt
) {
    tutorial_erc20_address.write(_erc20_address);
    players_registry.write(_players_registry);
    workshop_id.write(_workshop_id);
    return ();
}

func distribute_points{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    to: felt, amount: felt
) {
    let points_to_credit: Uint256 = Uint256(amount * ERC20_BASE, 0);
    let (contract_address) = tutorial_erc20_address.read();
    ITutorial.distribute_points(contract_address=contract_address, to=to, amount=points_to_credit);
    return ();
}

func validate_exercise{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    account: felt, exercise_id
) {
    let (_players_registry) = players_registry.read();
    let (_workshop_id) = workshop_id.read();
    let (has_validated) = IPlayerRegistry.check_validated_exercise(
        contract_address=_players_registry,
        account=account,
        workshop=_workshop_id,
        exercise=exercise_id,
    );
    assert (has_validated) = 0;

    IPlayerRegistry.validate_exercise(
        contract_address=_players_registry,
        account=account,
        workshop=_workshop_id,
        exercise=exercise_id,
    );

    return ();
}

func validate_and_reward{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    sender_address: felt, exercise: felt, points: felt
) {
    let (has_validated) = has_validated_exercise(sender_address, exercise);

    if (has_validated == 0) {
        validate_exercise(sender_address, exercise);
        distribute_points(sender_address, points);
        return ();
    }

    return ();
}

func only_teacher{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() {
    let (caller) = get_caller_address();
    let (permission) = teacher_accounts.read(account=caller);
    assert permission = 1;
    return ();
}

func set_a_random_value{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    values_len: felt, values: felt*, column: felt
) {
    if (values_len == 0) {
        return ();
    }
    set_a_random_value(values_len=values_len - 1, values=values + 1, column=column);
    random_attributes.write(values_len - 1, column, [values]);
    return ();
}

// TODO: max rank and rank in general
func assign_rank_to_player{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    sender_address: felt
) {
    alloc_locals;

    let (rank) = next_rank.read();
    assigned_rank.write(sender_address, rank);

    let new_rank = rank + 1;
    let (max) = max_rank.read();

    if (new_rank == max) {
        next_rank.write(0);
    } else {
        next_rank.write(new_rank);
    }
    return ();
}

//
// EXTERNAL FUNCTIONS
//
@external
func set_teacher{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    account: felt, permission: felt
) {
    only_teacher();

    teacher_accounts.write(account, permission);

    return ();
}

@external
func set_random_values{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    values_len: felt, values: felt*, column: felt
) {
    only_teacher();

    let (max) = max_rank.read();
    assert values_len = max;
    set_a_random_value(values_len, values, column);
    return ();
}
