%lang starknet
%builtins pedersen range_check ecdsa

from starkware.cairo.common.registers import get_fp_and_pc
from starkware.starknet.common.syscalls import get_contract_address
from starkware.cairo.common.signature import verify_ecdsa_signature
from starkware.cairo.common.cairo_builtins import HashBuiltin, SignatureBuiltin
from starkware.starknet.common.syscalls import call_contract, get_caller_address, get_tx_signature
from starkware.cairo.common.hash_state import (
    hash_init, hash_finalize, hash_update, hash_update_single)

#
# Structs
#

struct Transmission:
    member sender : felt
    member to : felt
    member selector : felt
    member raw_report_context : felt
    member raw_observers : felt
    member observations_len : felt
    member observations : felt*
    member r_sigs_len : felt
    member r_sigs : felt*
    member s_sigs_len : felt
    member s_sigs : felt*
    member public_keys_len : felt
    member public_keys : felt*
    member nonce : felt
end

#
# Storage
#

@storage_var
func current_nonce() -> (res : felt):
end

@storage_var
func public_key() -> (res : felt):
end

#
# Guards
#

@view
func assert_only_self{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}():
    let (self) = get_contract_address()
    let (caller) = get_caller_address()
    assert self = caller
    return ()
end

#
# Getters
#

@view
func get_public_key{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        res : felt):
    let (res) = public_key.read()
    return (res=res)
end

@view
func get_nonce{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (res : felt):
    let (res) = current_nonce.read()
    return (res=res)
end

#
# Setters
#

@external
func set_public_key{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        new_public_key : felt):
    assert_only_self()
    public_key.write(new_public_key)
    return ()
end

#
# Constructor
#

@constructor
func constructor{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        _public_key : felt):
    public_key.write(_public_key)
    return ()
end

#
# Business logic
#

@view
func is_valid_signature{
        syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr,
        ecdsa_ptr : SignatureBuiltin*}(hash : felt, signature_len : felt, signature : felt*) -> ():
    let (_public_key) = public_key.read()

    # This interface expects a signature pointer and length to make
    # no assumption about signature validation schemes.
    # But this implementation does, and it expects a (sig_r, sig_s) pair.
    let sig_r = signature[0]
    let sig_s = signature[1]

    verify_ecdsa_signature(
        message=hash, public_key=_public_key, signature_r=sig_r, signature_s=sig_s)

    return ()
end

@external
func transmit{
        syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr,
        ecdsa_ptr : SignatureBuiltin*}(
        to : felt, selector : felt, raw_report_context : felt, raw_observers : felt,
        observations_len : felt, observations : felt*, r_sigs_len : felt, r_sigs : felt*,
        s_sigs_len : felt, s_sigs : felt*, public_keys_len : felt, public_keys : felt*,
        nonce : felt) -> (a_len : felt, a : felt*):
    alloc_locals

    let (__fp__, _) = get_fp_and_pc()
    let (_address) = get_contract_address()
    let (_current_nonce) = current_nonce.read()

    # validate nonce
    assert _current_nonce = nonce

    local transmission : Transmission = Transmission(
        _address,
        to,
        selector,
        raw_report_context,
        raw_observers,
        observations_len,
        observations,
        r_sigs_len,
        r_sigs,
        s_sigs_len,
        s_sigs,
        public_keys_len,
        public_keys,
        _current_nonce
        )

    # validate transaction
    let (hash) = hash_message(&transmission)
    let (signature_len, signature) = get_tx_signature()
    # is_valid_signature(hash, signature_len, signature)

    # bump nonce
    current_nonce.write(_current_nonce + 1)

    # Execute a call
    let (res) = OffchainAggregator.transmit(
        to,
        raw_report_context,
        raw_observers,
        observations_len,
        observations,
        r_sigs_len,
        r_sigs,
        s_sigs_len,
        s_sigs,
        public_keys_len,
        public_keys)

    return (signature_len, signature)
end

func hash_message{pedersen_ptr : HashBuiltin*}(transmission : Transmission*) -> (res : felt):
    alloc_locals
    # we need to make `res_calldata` local
    # to prevent the reference from being revoked
    let (local res_calldata) = hash_calldata(transmission)
    let hash_ptr = pedersen_ptr
    with hash_ptr:
        let (hash_state_ptr) = hash_init()
        # first three iterations are 'sender', 'to', and 'selector'
        let (hash_state_ptr) = hash_update_single(hash_state_ptr, transmission.sender)
        let (hash_state_ptr) = hash_update_single(hash_state_ptr, transmission.to)
        let (hash_state_ptr) = hash_update_single(hash_state_ptr, transmission.selector)
        let (hash_state_ptr) = hash_update_single(hash_state_ptr, res_calldata)
        let (hash_state_ptr) = hash_update_single(hash_state_ptr, transmission.nonce)
        let (res) = hash_finalize(hash_state_ptr)
        let pedersen_ptr = hash_ptr
        return (res=res)
    end
end

func hash_calldata{pedersen_ptr : HashBuiltin*}(transmission : Transmission*) -> (res : felt):
    let hash_ptr = pedersen_ptr
    with hash_ptr:
        let (hash_state_ptr) = hash_init()
        let (hash_state_ptr) = hash_update_single(hash_state_ptr, transmission.raw_report_context)
        let (hash_state_ptr) = hash_update_single(hash_state_ptr, transmission.raw_observers)
        let (hash_state_ptr) = hash_update(
            hash_state_ptr, transmission.observations, transmission.observations_len)
        let (hash_state_ptr) = hash_update(
            hash_state_ptr, transmission.r_sigs, transmission.r_sigs_len)
        let (hash_state_ptr) = hash_update(
            hash_state_ptr, transmission.s_sigs, transmission.s_sigs_len)
        let (hash_state_ptr) = hash_update(
            hash_state_ptr, transmission.public_keys, transmission.public_keys_len)

        let (res) = hash_finalize(hash_state_ptr)
        let pedersen_ptr = hash_ptr
        return (res=res)
    end
end

@contract_interface
namespace OffchainAggregator:
    func transmit(
            raw_report_context : felt, raw_observers : felt, observations_len : felt,
            observations : felt*, r_sigs_len : felt, r_sigs : felt*, s_sigs_len : felt,
            s_sigs : felt*, public_keys_len : felt, public_keys : felt*) -> (res):
    end
end
