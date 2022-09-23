%lang starknet

from starkware.cairo.common.uint256 import Uint256

@contract_interface
namespace ITutorial {
    func distribute_points(to: felt, amount: Uint256) {
    }

    func remove_points(to: felt, amount: Uint256) {
    }

    func set_teacher(account: felt, permission: felt) {
    }

    func is_teacher_or_exercise(account: felt) -> (permission: felt) {
    }

    func set_teachers_temp(accounts_len: felt, accounts: felt*) {
    }

    func set_teacher_temp(account: felt) {
    }
}
