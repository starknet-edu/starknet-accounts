%lang starknet

//
// INTERFACE
//
@contract_interface
namespace IPlayerRegistry {
    func check_validated_exercise(account: felt, workshop: felt, exercise: felt) -> (
        has_validated: felt
    ) {
    }

    func is_exercise_or_admin(account: felt) -> (permission: felt) {
    }

    func get_next_player_rank() -> (rank: felt) {
    }

    func get_players_registry(rank: felt) -> (account: felt) {
    }

    func get_player_ranks(account: felt) -> (rank: felt) {
    }

    func set_exercise_or_admin(account: felt, permission: felt) {
    }

    func set_exercises_or_admins(accounts_len: felt, accounts: felt*) {
    }

    func validate_exercise(account: felt, workshop: felt, exercise: felt) {
    }
}
