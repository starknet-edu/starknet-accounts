%lang starknet

from starkware.cairo.common.cairo_builtins import HashBuiltin, SignatureBuiltin
from starkware.cairo.common.signature import verify_ecdsa_signature
from starkware.starknet.common.syscalls import (
    get_caller_address,
    get_contract_address,
    get_tx_info,
    get_block_number,
    get_block_timestamp,
)

from starkware.cairo.common.math import assert_not_equal, assert_not_zero
from starkware.cairo.common.hash import hash2
from starkware.cairo.common.alloc import alloc
from starkware.cairo.common.bool import TRUE, FALSE
from starkware.cairo.common.uint256 import Uint256

from tutorial.secp.bigint import BigInt3
from tutorial.secp.secp import verify_ecdsa
from tutorial.secp.secp_ec import EcPoint

//
// CONSTS
//
const WORKSHIP_ID = 0x5;
const HELLO = 0x48454c4c4f;
const SIGNATURE_1 = 0x5349474e41545552455f31;
const SIGNATURE_2 = 0x5349474e41545552455f32;
const SIGNATURE_3 = 0x5349474e41545552455f33;
const MULTICALL = 0x4d554c544943414c4c;
const MULTISIG = 0x4d554c5449534947;
const ABSTRACTION = 0x4142535452414354494f4e;
const REWARDS_BASE = 0x0de0b6b3a7640000;

//
// STRUCTS
//
struct TestSignature {
    hash: felt,
    pub: felt,
    sig_r: felt,
    sig_s: felt,
}

//
// INTERFACES
//
@contract_interface
namespace IAccountSig {
    func get_nonce() -> (res: felt) {
    }

    func get_signer() -> (res: felt) {
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

    func get_test_sig() -> (value: TestSignature) {
    }
}

@contract_interface
namespace IAccountAbstraction {
    func get_public_key() -> (pub_key: EcPoint) {
    }
    func is_valid_signature(hash: BigInt3, sig_r: BigInt3, sig_s: BigInt3) {
    }
}

//
// STORAGE VARIABLES
//
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
func dupe_nonce(tx_hash: felt) -> (value: felt) {
}

@storage_var
func multicall_counter(tx_meta: felt) -> (value: felt) {
}

//
// EVENTS
//
@event
func payday(address: felt, contract: felt) {
}

//
// CONSTRUCTOR
//
@constructor
func constructor{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    priv, pub, s1, s2: felt
) {
    let (block_num) = get_block_number();
    private.write(priv);
    public.write(pub);
    secret_1.write(s1);
    secret_2.write(s2);
    random.write(block_num);

    return ();
}

//
// GETTER FUNCTIONS
//
@view
func get_public{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() -> (pub: felt) {
    let (pub) = public.read();
    return (pub,);
}

@view
func get_random{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() -> (rand: felt) {
    let (rand) = random.read();
    return (rand,);
}

@view
func get_dupe_nonce{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    tx_hash: felt
) -> (value: felt) {
    let (value) = dupe_nonce.read(tx_hash);
    return (value,);
}

@view
func get_multicall_count{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    tx_meta: felt
) -> (value: felt) {
    let (value) = multicall_counter.read(tx_meta);
    return (value,);
}

//
// INTERNAL FUNCTIONS
//
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

func _is_valid_abstraction{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(
    hash: BigInt3, public_key: EcPoint, sig_r: BigInt3, sig_s: BigInt3
) -> () {
    alloc_locals;

    verify_ecdsa(public_key_pt=public_key, msg_hash=hash, r=sig_r, s=sig_s);

    return ();
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

    return (confirmed + rest,);
}

//
// EXTERNAL FUNCTIONS
//
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
    assert input = rand;

    payday.emit(address, HELLO);

    return (TRUE,);
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

    verify_ecdsa_signature(
        message=hash_final,
        public_key=pub,
        signature_r=tx_info.signature[0],
        signature_s=tx_info.signature[1],
    );

    payday.emit(address, SIGNATURE_1);

    return (TRUE,);
}

@external
func validate_signature_2{
    syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr, ecdsa_ptr: SignatureBuiltin*
}(tx_hash: felt, sig_r: felt, sig_s: felt, address: felt) -> (success: felt) {
    alloc_locals;
    let (tx_info) = get_tx_info();
    assert tx_info.signature_len = 2;

    let (caller) = get_caller_address();
    assert_not_zero(caller);
    assert caller = tx_info.account_contract_address;

    _is_valid_signature(
        hash=tx_hash, signature_len=tx_info.signature_len, signature=tx_info.signature
    );

    let (vec: felt*) = alloc();
    assert [vec] = sig_r;
    assert [vec + 1] = sig_s;

    IAccountSig.is_valid_signature(
        contract_address=caller, hash=tx_hash, signature_len=2, signature=vec
    );

    let (tx_hash_count) = dupe_nonce.read(tx_hash);
    if (tx_hash_count == 0) {
        dupe_nonce.write(tx_hash=tx_hash, value=1);
        return (FALSE,);
    }

    if (tx_hash_count == 1) {
        payday.emit(address, SIGNATURE_2);

        return (TRUE,);
    }

    return (FALSE,);
}

@external
func validate_signature_3{
    syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr, ecdsa_ptr: SignatureBuiltin*
}(input: felt, address: felt) -> (success: felt) {
    alloc_locals;
    let (tx_info) = get_tx_info();
    local tx_hash = tx_info.transaction_hash;

    let (caller) = get_caller_address();
    assert_not_zero(caller);
    assert caller = tx_info.account_contract_address;

    let (curr_nonce) = IAccountSig.get_nonce(contract_address=caller);
    assert input = curr_nonce;
    let (hash) = hash2{hash_ptr=pedersen_ptr}(tx_hash, curr_nonce - 1);

    _is_valid_signature(
        hash=hash, signature_len=tx_info.signature_len, signature=tx_info.signature
    );

    payday.emit(address, SIGNATURE_3);

    return (TRUE,);
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
        return (FALSE,);
    }

    if (value == 2) {
        payday.emit(address, MULTICALL);

        return (TRUE,);
    }

    return (FALSE,);
}

@external
func validate_multisig{
    syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr, ecdsa_ptr: SignatureBuiltin*
}(filler: felt, address: felt, input: felt) -> (success: felt) {
    alloc_locals;
    assert filler = 1;

    let (caller) = get_caller_address();
    let (test_sig: TestSignature) = IMultiSig.get_test_sig(contract_address=caller);
    _is_valid_signature_full(test_sig.hash, test_sig.pub, test_sig.sig_r, test_sig.sig_s);

    let (num_confirms) = IMultiSig.get_confirmations(contract_address=caller, tx_index=input);
    let (num_owners) = IMultiSig.get_num_owners(contract_address=caller);
    assert num_confirms = num_owners - 1;

    let (signers_len, signers) = IMultiSig.get_owners(contract_address=caller);
    let (count) = _validate_signer_count(caller, input, 0, signers_len, signers);
    assert count = signers_len - 1;

    payday.emit(address, MULTISIG);

    return (TRUE,);
}

@external
func validate_abstraction{
    syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr, ecdsa_ptr: SignatureBuiltin*
}(hash: BigInt3, sig_r: BigInt3, sig_s: BigInt3, address: felt) -> (success: felt) {
    alloc_locals;
    let (caller) = get_caller_address();
    assert_not_zero(caller);

    let (tx_info) = get_tx_info();
    assert caller = tx_info.account_contract_address;

    IAccountAbstraction.is_valid_signature(
        contract_address=caller, hash=hash, sig_r=sig_r, sig_s=sig_s
    );

    let (pub_key) = IAccountAbstraction.get_public_key(contract_address=caller);
    _is_valid_abstraction(hash, pub_key, sig_r, sig_s);

    payday.emit(address, ABSTRACTION);

    return (TRUE,);
}
