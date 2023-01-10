%lang starknet

from starkware.cairo.common.cairo_builtins import HashBuiltin, SignatureBuiltin, BitwiseBuiltin
from starkware.cairo.common.signature import verify_ecdsa_signature
from starkware.cairo.common.cairo_secp.signature import verify_eth_signature_uint256
from starkware.starknet.common.syscalls import (
    get_caller_address,
    get_contract_address,
    get_tx_info,
    get_block_number,
    get_block_timestamp,
)

from starkware.cairo.common.math import assert_not_equal, assert_not_zero, split_felt
from starkware.cairo.common.hash import hash2
from starkware.cairo.common.alloc import alloc
from starkware.cairo.common.bool import TRUE, FALSE
from starkware.cairo.common.registers import get_fp_and_pc
from starkware.cairo.common.uint256 import Uint256

from contracts.tutorial.tutorial import (
    ex_initializer,
    validate_and_reward,
    teacher_accounts,
    assign_rank_to_player,
    max_rank,
)

// ///////////////////
// CONSTS
// ///////////////////
const WORKSHIP_ID = 5;
const HELLO = 'HELLO';
const SIGNATURE_1 = 'SIGNATURE_1';
const SIGNATURE_2 = 'SIGNATURE_2';
const SIGNATURE_3 = 'SIGNATURE_3';
const MULTICALL = 'MULTICALL';
const MULTISIG = 'MULTISIG';
const ABSTRACTION = 'ABSTRACTION';
const REWARDS_BASE = 1000000000000000000;
const ETHEREUM_ADDRESS = 0x1a642f0e3c3af545e7acbd38b07251b3990914f1;

// ///////////////////
// INTERFACES
// ///////////////////
@contract_interface
namespace IAccountSig {
    func get_public_key() -> (public_key: felt) {
    }

    func is_valid_signature(hash: felt, signature_len: felt, signature: felt*) {
    }
}

@contract_interface
namespace IMultiSig {
    func get_confirmations(tx_index: felt) -> (res: felt) {
    }

    func get_num_owners() -> (res: felt) {
    }

    func get_owners() -> (signers_len: felt, signers: felt*) {
    }

    func get_owner_confirmed(tx_index: felt, owner: felt) -> (res: felt) {
    }
}

// ///////////////////
// STORAGE VARIABLES
// ///////////////////
@storage_var
func private() -> (res: felt) {
}

@storage_var
func public() -> (res: felt) {
}

@storage_var
func secret_1() -> (res: felt) {
}

@storage_var
func secret_2() -> (res: felt) {
}

@storage_var
func random() -> (res: felt) {
}

@storage_var
func ethereum_address() -> (res: felt) {
}

@storage_var
func multicall_counter(tx_meta: felt) -> (value: felt) {
}

// ///////////////////
// EVENTS
// ///////////////////
@event
func payday(address: felt, contract: felt) {
}

// ///////////////////
// CONSTRUCTOR
// ///////////////////
@constructor
func constructor{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    priv, pub, s1, s2, _tutorial_erc20_address, _players_registry, _first_teacher: felt
) {
    ex_initializer(_tutorial_erc20_address, _players_registry, WORKSHIP_ID);
    teacher_accounts.write(_first_teacher, 1);
    max_rank.write(100);

    let (block_num) = get_block_number();
    private.write(priv);
    public.write(pub);
    secret_1.write(s1);
    secret_2.write(s2);
    random.write(block_num);

    return ();
}

// ///////////////////
// GETTER FUNCTIONS
// ///////////////////
@view
func get_public{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() -> (pub: felt) {
    let (pub) = public.read();
    return (pub=pub);
}

@view
func get_random{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() -> (rand: felt) {
    let (rand) = random.read();
    return (rand=rand);
}

@view
func get_multicall_count{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    tx_meta: felt
) -> (value: felt) {
    let (value) = multicall_counter.read(tx_meta);
    return (value=value);
}

// ///////////////////
// INTERNAL FUNCTIONS
// ///////////////////
func _is_valid_signature{
    syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr, ecdsa_ptr: SignatureBuiltin*
}(hash: felt, signature_len: felt, signature: felt*) -> () {
    let (_public_key) = public.read();

    let sig_r = signature[0];
    let sig_s = signature[1];

    verify_ecdsa_signature(
        message=hash, public_key=_public_key, signature_r=sig_r, signature_s=sig_s
    );

    return ();
}

func _is_valid_signature_full{
    syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr, ecdsa_ptr: SignatureBuiltin*
}(hash: felt, pub: felt, sig_r: felt, sig_s: felt) -> () {
    let (_public_key) = public.read();
    assert_not_equal(pub, _public_key);

    verify_ecdsa_signature(message=hash, public_key=pub, signature_r=sig_r, signature_s=sig_s);

    return ();
}

func _is_valid_eth_signature{
    syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, bitwise_ptr: BitwiseBuiltin*, range_check_ptr
}(hash: felt, signature_len: felt, signature: felt*) -> (is_valid: felt) {
    alloc_locals;
    let (__fp__, _) = get_fp_and_pc();

    let sig_v: felt = signature[0];
    let sig_r: Uint256 = Uint256(low=signature[1], high=signature[2]);
    let sig_s: Uint256 = Uint256(low=signature[3], high=signature[4]);
    let (high, low) = split_felt(hash);
    let msg_hash: Uint256 = Uint256(low=low, high=high);

    let (local keccak_ptr: felt*) = alloc();

    with keccak_ptr {
        verify_eth_signature_uint256(
            msg_hash=msg_hash, r=sig_r, s=sig_s, v=sig_v, eth_address=ETHEREUM_ADDRESS
        );
    }

    return (is_valid=TRUE);
}

func _validate_signer_count{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    addr: felt, tx_index: felt, agg: felt, signers_len: felt, signers: felt*
) -> (res: felt) {
    if (agg == signers_len) {
        return (0,);
    }

    let (rest) = _validate_signer_count(addr, tx_index, agg + 1, signers_len, signers);
    let (confirmed) = IMultiSig.get_owner_confirmed(
        contract_address=addr, tx_index=tx_index, owner=signers[agg]
    );

    return (res=confirmed + rest);
}

// ///////////////////
// EXTERNAL FUNCTIONS
// ///////////////////
@external
func validate_hello{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    input: felt, address: felt
) -> (success: felt) {
    let (caller) = get_caller_address();
    assert_not_zero(caller);

    let (tx_info) = get_tx_info();
    assert caller = tx_info.account_contract_address;
    assert tx_info.signature_len = 0;

    let (rand) = random.read();
    with_attr error_message("fetched incorrect value") {
        assert input = rand;
    }

    payday.emit(address, HELLO);
    assign_rank_to_player(address);
    validate_and_reward(address, HELLO, 100);

    return (success=TRUE);
}

@external
func validate_signature_1{
    syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr, ecdsa_ptr: SignatureBuiltin*
}(input: felt, address: felt) -> (success: felt) {
    alloc_locals;
    let (caller) = get_caller_address();
    assert_not_zero(caller);

    let (tx_info) = get_tx_info();
    assert caller = tx_info.account_contract_address;
    assert_not_zero(tx_info.signature_len);

    let (pub) = public.read();

    let (s1) = secret_1.read();
    let (s2) = secret_2.read();

    let (hash) = hash2{hash_ptr=pedersen_ptr}(s1, s2);
    assert hash = input;

    let (hash_final) = hash2{hash_ptr=pedersen_ptr}(hash, tx_info.account_contract_address);

    with_attr error_message("could not validate custom hash") {
        verify_ecdsa_signature(
            message=hash_final,
            public_key=pub,
            signature_r=tx_info.signature[0],
            signature_s=tx_info.signature[1],
        );
    }

    payday.emit(address, SIGNATURE_1);
    validate_and_reward(address, SIGNATURE_1, 100);

    return (success=TRUE);
}

@external
func validate_signature_2{
    syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr, ecdsa_ptr: SignatureBuiltin*
}(address: felt) -> (success: felt) {
    alloc_locals;
    let (tx_info) = get_tx_info();
    assert tx_info.signature_len = 2;

    let (caller) = get_caller_address();
    assert_not_zero(caller);
    assert caller = tx_info.account_contract_address;

    let (public_key) = IAccountSig.get_public_key(contract_address=caller);
    assert_not_zero(public_key);

    with_attr error_message("could not validate via account view") {
        IAccountSig.is_valid_signature(
            contract_address=caller,
            hash=tx_info.transaction_hash,
            signature_len=tx_info.signature_len,
            signature=tx_info.signature,
        );
    }

    if (tx_info.nonce == 1) {
        payday.emit(address, SIGNATURE_2);
        validate_and_reward(address, SIGNATURE_2, 200);
        return (success=TRUE);
    }

    return (success=FALSE);
}

@external
func validate_signature_3{
    syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, bitwise_ptr: BitwiseBuiltin*, range_check_ptr
}(address: felt) -> (success: felt) {
    alloc_locals;
    let (tx_info) = get_tx_info();
    let (caller) = get_caller_address();

    assert_not_zero(caller);
    assert caller = tx_info.account_contract_address;

    _is_valid_eth_signature(
        hash=tx_info.transaction_hash,
        signature_len=tx_info.signature_len,
        signature=tx_info.signature,
    );

    payday.emit(address, SIGNATURE_3);
    validate_and_reward(address, SIGNATURE_3, 300);

    return (success=TRUE);
}

@external
func validate_multicall{
    syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr, ecdsa_ptr: SignatureBuiltin*
}(address: felt) -> (success: felt) {
    alloc_locals;
    let (tx_info) = get_tx_info();
    local tx_hash = tx_info.transaction_hash;

    let (caller) = get_caller_address();
    assert_not_zero(caller);
    assert caller = tx_info.account_contract_address;

    _is_valid_signature(
        hash=tx_hash, signature_len=tx_info.signature_len, signature=tx_info.signature
    );

    let (ts) = get_block_timestamp();
    let (tx_meta) = hash2{hash_ptr=pedersen_ptr}(tx_hash, ts);

    let (value) = multicall_counter.read(tx_meta);
    if (value != 2) {
        multicall_counter.write(tx_meta, value + 1);
        return (success=FALSE);
    }

    if (value == 2) {
        payday.emit(address, MULTICALL);
        validate_and_reward(address, MULTICALL, 500);

        return (success=TRUE);
    }

    return (success=FALSE);
}

@external
func validate_multisig{
    syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr, ecdsa_ptr: SignatureBuiltin*
}(filler: felt, address: felt, input: felt) -> (success: felt) {
    alloc_locals;
    assert filler = 1;

    let (caller) = get_caller_address();

    let (num_confirms) = IMultiSig.get_confirmations(contract_address=caller, tx_index=input);
    let (num_owners) = IMultiSig.get_num_owners(contract_address=caller);
    assert num_confirms = num_owners - 1;

    let (signers_len, signers) = IMultiSig.get_owners(contract_address=caller);
    let (count) = _validate_signer_count(caller, input, 0, signers_len, signers);
    assert count = signers_len - 1;

    payday.emit(address, MULTISIG);
    validate_and_reward(address, MULTISIG, 1000);

    return (TRUE,);
}
