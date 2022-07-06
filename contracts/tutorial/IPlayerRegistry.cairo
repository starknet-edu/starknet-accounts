%lang starknet

####################
# INTERFACE
####################
@contract_interface
namespace IPlayerRegistry:
    func check_validated_exercise(account : felt, workshop : felt, exercise : felt) -> (
        has_validated : felt
    ):
    end

    func is_exercise_or_admin(account : felt) -> (permission : felt):
    end

    func get_next_player_rank() -> (rank : felt):
    end

    func get_players_registry(rank : felt) -> (account : felt):
    end

    func get_player_ranks(account : felt) -> (rank : felt):
    end

    func set_exercise_or_admin(account : felt, permission : felt):
    end

    func set_exercises_or_admins(accounts_len : felt, accounts : felt*):
    end

    func validate_exercise(account : felt, workshop : felt, exercise : felt):
    end
end
