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
from cairo_examples.secp.bigint import BigInt3
from cairo_examples.secp.secp import verify_ecdsa
from cairo_examples.secp.secp_ec import EcPoint

####################
# CONSTS
####################
const HELLO = 0x48454c4c4f
const SIGNATURE_1 = 0x5349474e41545552455f31
const SIGNATURE_2 = 0x5349474e41545552455f32
const SIGNATURE_3 = 0x5349474e41545552455f33
const MULTICALL = 0x4d554c544943414c4c
const MULTISIG = 0x4d554c5449534947
const ABSTRACTION = 0x4142535452414354494f4e

####################
# INTERFACES
####################
@contract_interface
namespace IAccountSig:
    func get_nonce() -> (res : felt):
    end

    func get_signer() -> (res : felt):
    end

    func is_valid_signature(hash : felt, signature_len : felt, signature : felt*):
    end
end

@contract_interface
namespace IMultiSig:
    func get_confirmations(tx_index : felt) -> (res : felt):
    end
    
    func get_num_owners() -> (res : felt):
    end
    
    func get_owners() -> (signers_len : felt, signers : felt*):
    end

    func get_owner_confirmed(tx_index : felt, owner : felt) -> (res : felt):
    end
end

@contract_interface
namespace IAccountAbstraction:
    func get_public_key() -> (pub_key : EcPoint):
    end
    func is_valid_signature(hash : BigInt3, sig_r : BigInt3, sig_s : BigInt3):
    end
end

####################
# STORAGE VARIABLES
####################
@storage_var
func completions(address : felt, contract : felt) -> (completed : felt):
end

@storage_var
func private() -> (res : felt):
end

@storage_var
func public() -> (res : felt):
end

@storage_var
func secret_1() -> (res : felt):
end

@storage_var
func secret_2() -> (res : felt):
end

@storage_var
func random() -> (res : felt):
end

@storage_var
func dupe_nonce(tx_hash : felt) -> (value : felt):
end

@storage_var
func multicall_counter(tx_meta : felt) -> (value : felt):
end

####################
# EVENTS
####################
@event
func payday(address : felt, contract : felt):
end

####################
# CONSTRUCTOR
####################
@constructor
func constructor{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
    priv, pub, s1, s2 : felt
):
    let (block_num) = get_block_number()

    private.write(priv)
    public.write(pub)
    secret_1.write(s1)
    secret_2.write(s2)
    random.write(block_num)

    return ()
end

####################
# GETTER FUNCTIONS
####################
@view
func get_public{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
    pub : felt
):
    let (pub) = public.read()
    return (pub)
end

@view
func get_random{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
    rand : felt
):
    let (rand) = random.read()
    return (rand)
end

@view
func get_dupe_nonce{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
    tx_hash : felt
) -> (value : felt):
    let (value) = dupe_nonce.read(tx_hash)
    return (value)
end

@view
func get_multicall_count{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
    tx_meta : felt
) -> (value : felt):
    let (value) = multicall_counter.read(tx_meta)
    return (value)
end

@view
func get_completions{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
    address : felt, contract : felt
) -> (completed : felt):
    let (completed) = completions.read(address, contract)
    return (completed)
end

####################
# INTERNAL FUNCTIONS
####################
func _is_valid_signature{
    syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr, ecdsa_ptr : SignatureBuiltin*
}(hash : felt, signature_len : felt, signature : felt*) -> ():
    let (_public_key) = public.read()

    let sig_r = signature[0]
    let sig_s = signature[1]

    verify_ecdsa_signature(
        message=hash, public_key=_public_key, signature_r=sig_r, signature_s=sig_s
    )

    return ()
end

func _is_valid_abstraction{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
    hash : BigInt3, public_key : EcPoint, sig_r : BigInt3, sig_s : BigInt3
) -> ():
    alloc_locals

    verify_ecdsa(public_key_pt=public_key, msg_hash=hash, r=sig_r, s=sig_s)

    return ()
end

func _validate_signer_count{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
    addr : felt, tx_index : felt, agg : felt, signers_len : felt, signers : felt*
) -> (res : felt):
    if agg == signers_len:
        return (0)
    end

    let (rest) = _validate_signer_count(addr, tx_index, agg+1, signers_len, signers)
    let (confirmed) = IMultiSig.get_owner_confirmed(contract_address=addr, tx_index=tx_index, owner=signers[agg])

    return (confirmed + rest)
end

####################
# EXTERNAL FUNCTIONS
####################
@external
func validate_hello{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
    input : felt, address : felt
) -> (success : felt):
    let (caller) = get_caller_address()
    assert_not_zero(caller)

    let (tx_info) = get_tx_info()
    assert caller = tx_info.account_contract_address
    assert tx_info.signature_len = 0

    let (rand) = random.read()
    assert input = rand

    completions.write(address, HELLO, 1)
    payday.emit(address, HELLO)
    return (TRUE)
end

@external
func validate_signature_1{
    syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr, ecdsa_ptr : SignatureBuiltin*
}(input : felt, address : felt) -> (success : felt):
    let (caller) = get_caller_address()
    assert_not_zero(caller)

    let (tx_info) = get_tx_info()
    assert caller = tx_info.account_contract_address
    assert_not_zero(tx_info.signature_len)

    let (pub) = public.read()

    let (s1) = secret_1.read()
    let (s2) = secret_2.read()

    let (hash) = hash2{hash_ptr=pedersen_ptr}(s1, s2)
    assert hash = input

    let (hash_final) = hash2{hash_ptr=pedersen_ptr}(hash, tx_info.account_contract_address)

    verify_ecdsa_signature(
        message=hash_final,
        public_key=pub,
        signature_r=tx_info.signature[0],
        signature_s=tx_info.signature[1],
    )

    completions.write(address, SIGNATURE_1, 1)
    payday.emit(address, SIGNATURE_1)
    return (TRUE)
end

@external
func validate_signature_2{
    syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr, ecdsa_ptr : SignatureBuiltin*
}(tx_hash : felt, sig_r : felt, sig_s : felt, address : felt) -> (success : felt):
    alloc_locals
    let (tx_info) = get_tx_info()
    assert tx_info.signature_len = 2

    let (caller) = get_caller_address()
    assert_not_zero(caller)
    assert caller = tx_info.account_contract_address

    _is_valid_signature(
        hash=tx_hash, signature_len=tx_info.signature_len, signature=tx_info.signature
    )

    let (vec : felt*) = alloc()
    assert [vec] = sig_r
    assert [vec + 1] = sig_s

    IAccountSig.is_valid_signature(
        contract_address=caller, hash=tx_hash, signature_len=2, signature=vec
    )

    let (tx_hash_count) = dupe_nonce.read(tx_hash)
    if tx_hash_count == 0:
        dupe_nonce.write(tx_hash=tx_hash, value=1)
        return (FALSE)
    end

    if tx_hash_count == 1:
        completions.write(address, SIGNATURE_2, 1)
        payday.emit(address, SIGNATURE_2)
        return (TRUE)
    end

    return (FALSE)
end

@external
func validate_signature_3{
    syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr, ecdsa_ptr : SignatureBuiltin*
}(input : felt, address : felt) -> (success : felt):
    alloc_locals
    let (tx_info) = get_tx_info()
    local tx_hash = tx_info.transaction_hash

    let (caller) = get_caller_address()
    assert_not_zero(caller)
    assert caller = tx_info.account_contract_address

    let (curr_nonce) = IAccountSig.get_nonce(contract_address=caller)
    assert curr_nonce = input
    let (hash) = hash2{hash_ptr=pedersen_ptr}(tx_hash, curr_nonce - 1)

    _is_valid_signature(hash=hash, signature_len=tx_info.signature_len, signature=tx_info.signature)

    completions.write(address, SIGNATURE_3, 1)
    payday.emit(address, SIGNATURE_3)
    return (TRUE)
end

@external
func validate_multicall{
    syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr, ecdsa_ptr : SignatureBuiltin*
}(address : felt) -> (success : felt):
    alloc_locals
    let (tx_info) = get_tx_info()
    local tx_hash = tx_info.transaction_hash

    let (caller) = get_caller_address()
    assert_not_zero(caller)
    assert caller = tx_info.account_contract_address

    _is_valid_signature(
        hash=tx_hash, signature_len=tx_info.signature_len, signature=tx_info.signature
    )

    let (ts) = get_block_timestamp()
    let (tx_meta) = hash2{hash_ptr=pedersen_ptr}(tx_hash, ts)

    let (value) = multicall_counter.read(tx_meta)
    if value != 2:
        multicall_counter.write(tx_meta, value + 1)
        return (FALSE)
    end

    if value == 2:
        completions.write(address, MULTICALL, 1)
        payday.emit(address, MULTICALL)
        return (TRUE)
    end

    return (FALSE)
end

@external
func validate_multisig{
    syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr, ecdsa_ptr : SignatureBuiltin*
}(filler : felt, address : felt, input: felt) -> (success : felt):
    alloc_locals
    assert filler = 1
    let (caller) = get_caller_address()
    let (num_confirms) = IMultiSig.get_confirmations(contract_address=caller, tx_index=input)
    let (num_owners) = IMultiSig.get_num_owners(contract_address=caller)
    assert num_confirms = num_owners-1

    let (signers_len, signers) = IMultiSig.get_owners(contract_address=caller)
    let (count) = _validate_signer_count(caller, input, 0, signers_len, signers)
    assert count = signers_len-1

    completions.write(address, MULTISIG, 1)
    payday.emit(address, MULTISIG)
    return (TRUE)
end

@external
func validate_abstraction{
    syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr, ecdsa_ptr : SignatureBuiltin*
}(hash : BigInt3, sig_r : BigInt3, sig_s : BigInt3, address : felt) -> (success : felt):
    alloc_locals
    let (caller) = get_caller_address()
    assert_not_zero(caller)

    let (tx_info) = get_tx_info()
    assert caller = tx_info.account_contract_address

    IAccountAbstraction.is_valid_signature(
        contract_address=caller, hash=hash, sig_r=sig_r, sig_s=sig_s
    )

    let (pub_key) = IAccountAbstraction.get_public_key(contract_address=caller)
    _is_valid_abstraction(hash, pub_key, sig_r, sig_s)

    completions.write(address, ABSTRACTION, 1)
    payday.emit(address, ABSTRACTION)
    return (TRUE)
end
