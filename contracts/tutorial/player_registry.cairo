// ######## Players registry
// # A contract to record all addresses who participated, and which exercises and workshops they completed

%lang starknet

from starkware.cairo.common.cairo_builtins import HashBuiltin
from starkware.starknet.common.syscalls import get_caller_address

//
// STORAGE VARIABLES
//
@storage_var
func player_validated_exercise(account: felt, workshop: felt, exercise: felt) -> (
    has_validated: felt
) {
}

@storage_var
func exercises_and_admins_accounts(account: felt) -> (permission: felt) {
}

@storage_var
func next_player_rank() -> (rank: felt) {
}

@storage_var
func players_registry(rank: felt) -> (account: felt) {
}

@storage_var
func players_ranks(account: felt) -> (rank: felt) {
}

//
// GETTERS
//
@view
func check_validated_exercise{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    account: felt, workshop: felt, exercise: felt
) -> (has_validated: felt) {
    let (has_validated) = player_validated_exercise.read(account, workshop, exercise);
    return (has_validated,);
}

@view
func is_exercise_or_admin{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    account: felt
) -> (permission: felt) {
    let (permission) = exercises_and_admins_accounts.read(account);
    return (permission,);
}

@view
func get_next_player_rank{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() -> (
    rank: felt
) {
    let (rank) = next_player_rank.read();
    return (rank,);
}

@view
func get_players_registry{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    rank: felt
) -> (account: felt) {
    let (account) = players_registry.read(rank);
    return (account,);
}

@view
func get_player_ranks{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    account: felt
) -> (rank: felt) {
    let (rank) = players_ranks.read(account);
    return (rank,);
}

//
// EVENTS
//
@event
func modificate_exercise_or_admin(account: felt, permission: felt) {
}

@event
func new_player(account: felt, rank: felt) {
}

@event
func new_validation(account: felt, workshop: felt, exercise: felt) {
}

//
// CONSTRUCTOR
//
@constructor
func constructor{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    first_admin: felt
) {
    exercises_and_admins_accounts.write(first_admin, 1);
    modificate_exercise_or_admin.emit(account=first_admin, permission=1);
    next_player_rank.write(1);
    return ();
}

func only_exercise_or_admin{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() {
    let (caller) = get_caller_address();
    let (permission) = exercises_and_admins_accounts.read(account=caller);
    assert permission = 1;
    return ();
}

func _set_exercises_or_admins{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    accounts_len: felt, accounts: felt*
) {
    if (accounts_len == 0) {
        return ();
    }

    _set_exercises_or_admins(accounts_len=accounts_len - 1, accounts=accounts + 1);

    exercises_and_admins_accounts.write([accounts], 1);
    modificate_exercise_or_admin.emit(account=[accounts], permission=1);

    return ();
}

//
// EXTERNAL FUNCTIONS
//
@external
func set_exercise_or_admin{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    account: felt, permission: felt
) {
    only_exercise_or_admin();
    exercises_and_admins_accounts.write(account, permission);
    modificate_exercise_or_admin.emit(account=account, permission=permission);

    return ();
}

@external
func set_exercises_or_admins{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    accounts_len: felt, accounts: felt*
) {
    only_exercise_or_admin();
    _set_exercises_or_admins(accounts_len, accounts);
    return ();
}

@external
func validate_exercise{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    account: felt, workshop: felt, exercise: felt
) {
    only_exercise_or_admin();
    let (valid) = player_validated_exercise.read(account, workshop, exercise);
    assert (valid) = 0;

    player_validated_exercise.write(account, workshop, exercise, 1);
    new_validation.emit(account=account, workshop=workshop, exercise=exercise);

    let (player_rank) = players_ranks.read(account);

    if (player_rank == 0) {
        let (curr_player_rank) = next_player_rank.read();
        players_registry.write(curr_player_rank, account);
        players_ranks.write(account, curr_player_rank);

        let new_player_rank = curr_player_rank + 1;
        next_player_rank.write(new_player_rank);
        new_player.emit(account=account, rank=curr_player_rank);

        return ();
    }

    return ();
}
