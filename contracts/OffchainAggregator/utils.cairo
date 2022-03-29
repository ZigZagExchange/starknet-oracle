%lang starknet

from starkware.cairo.common.cairo_builtins import HashBuiltin, SignatureBuiltin
from starkware.starknet.common.syscalls import get_caller_address, get_contract_address
from starkware.cairo.common.alloc import alloc
from starkware.cairo.common.signature import verify_ecdsa_signature
from starkware.cairo.common.hash import hash2
from starkware.cairo.common.math import assert_not_zero, assert_le, assert_lt, unsigned_div_rem
from starkware.cairo.common.pow import pow
from starkware.cairo.common.hash_state import (
    hash_init, hash_finalize, hash_update, hash_update_single)

from contracts.utils.AccessControlls import only_owner

const maxNumOracles = 31

# ## ==================================================================================
# ## CONFIG FUNCTIONS
func check_config_valid{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        _numSigners : felt, _numTransmitters : felt, _threshold : felt):
    alloc_locals
    assert_le(_numSigners, maxNumOracles)
    assert_lt(0, _threshold)
    assert _numSigners = _numTransmitters
    assert_lt(3 * _threshold, _numSigners)
    return ()
end

@view
func config_digest_from_config_data_deprecated{
        syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        _contractAddress : felt, _configCount : felt, _signers_len : felt, _signers : felt*,
        _transmitters_len : felt, _transmitters : felt*, _threshold : felt,
        _encodedConfigVersion : felt, _encodedConfig : felt) -> (digest : felt):
    alloc_locals

    let (hash : felt) = hash2{hash_ptr=pedersen_ptr}(_contractAddress, _configCount)
    let (hash : felt) = hash2{hash_ptr=pedersen_ptr}(hash, _configCount)
    let (hash : felt) = hash_array_deprecated(_signers_len, _signers, hash)
    let (hash : felt) = hash_array_deprecated(_transmitters_len, _transmitters, hash)
    let (hash : felt) = hash2{hash_ptr=pedersen_ptr}(hash, _threshold)
    let (hash : felt) = hash2{hash_ptr=pedersen_ptr}(hash, _encodedConfigVersion)
    let (digest : felt) = hash2{hash_ptr=pedersen_ptr}(hash, _encodedConfig)

    return (digest)
end

func hash_array_deprecated{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        arr_len : felt, arr : felt*, hash : felt) -> (hash : felt):
    alloc_locals
    if arr_len == 0:
        return (hash)
    end

    let (hash : felt) = hash2{hash_ptr=pedersen_ptr}(hash, arr[0])

    return hash_array_deprecated(arr_len - 1, &arr[1], hash)
end

@view
func config_digest_from_config_data{
        syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        _contractAddress : felt, _configCount : felt, _signers_len : felt, _signers : felt*,
        _transmitters_len : felt, _transmitters : felt*, _threshold : felt,
        _encodedConfigVersion : felt, _encodedConfig : felt) -> (res : felt):
    let hash_ptr = pedersen_ptr
    with hash_ptr:
        let (hash_state_ptr) = hash_init()
        let (hash_state_ptr) = hash_update_single(hash_state_ptr, _contractAddress)
        let (hash_state_ptr) = hash_update_single(hash_state_ptr, _configCount)
        let (hash_state_ptr) = hash_update(hash_state_ptr, _signers, _signers_len)
        let (hash_state_ptr) = hash_update(hash_state_ptr, _transmitters, _transmitters_len)
        let (hash_state_ptr) = hash_update_single(hash_state_ptr, _threshold)
        let (hash_state_ptr) = hash_update_single(hash_state_ptr, _encodedConfigVersion)
        let (hash_state_ptr) = hash_update_single(hash_state_ptr, _encodedConfig)

        let (res) = hash_finalize(hash_state_ptr)
        let pedersen_ptr = hash_ptr
        return (res=res)
    end
end

func hash_report{pedersen_ptr : HashBuiltin*}(
        report_context : felt, observer_idxs : felt, observations_len : felt,
        observations : felt*) -> (res : felt):
    let hash_ptr = pedersen_ptr
    with hash_ptr:
        let (hash_state_ptr) = hash_init()

        let (hash_state_ptr) = hash_update_single(hash_state_ptr, report_context)
        let (hash_state_ptr) = hash_update_single(hash_state_ptr, observer_idxs)
        let (hash_state_ptr) = hash_update(hash_state_ptr, observations, observations_len)

        let (res) = hash_finalize(hash_state_ptr)
        let pedersen_ptr = hash_ptr
        return (res=res)
    end
end

# ## ==================================================================================
# ## CHECK FOR DUPLICATES

func check_for_duplicates{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        arr_len : felt, arr : felt*, group_size : felt) -> ():
    alloc_locals

    # Check that arr_len is devisable by group size
    let (local div, local rem) = unsigned_div_rem(arr_len, group_size)
    with_attr error_message("==== (ARRAY SIZE SHOULD BE DEVISABLE BY GROUP SIZE) ===="):
        assert rem = 0
    end

    check_for_duplicates_inner(arr_len, arr, group_size)

    return ()
end

func check_for_duplicates_inner{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        arr_len : felt, arr : felt*, group_size : felt) -> ():
    alloc_locals
    if arr_len == 0:
        return ()
    end

    let new_arr_len = arr_len - group_size
    let new_arr = &arr[group_size]

    let (local current : felt) = get_sum(arr_len, arr, group_size, 0)
    let (check : felt) = comparison_loop(new_arr_len, new_arr, group_size, current)

    with_attr error_message("==== (DUPPLICATES FOUND IN ARRAY) ===="):
        assert check = 1
    end

    return check_for_duplicates_inner(new_arr_len, new_arr, group_size)
end

func comparison_loop{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        arr_len : felt, arr : felt*, group_size : felt, current : felt) -> (res):
    alloc_locals
    if arr_len == 0:
        return (1)
    end

    let (sum : felt) = get_sum(arr_len, arr, group_size, 0)
    if sum == 0:
        return (1)  # TODO: If array ends with all zeros, trim that instead of ignoring it
    end
    if sum == current:
        return (0)
    end

    return comparison_loop(arr_len - group_size, &arr[group_size], group_size, current)
end

func get_sum{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        arr_len : felt, arr : felt*, group_size : felt, sum : felt) -> (sum):
    alloc_locals
    if group_size == 0:
        return (sum)
    end

    let (local multiplier : felt) = pow(16, group_size - 1)
    let a : felt = arr[0] * multiplier

    return get_sum(arr_len - 1, &arr[1], group_size - 1, sum + a)
end

# ## ==================================================================================
# ## VERIFY SIGNATURES FOR THE GIVEN MESSAGE HASH

func verify_sig{
        syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr,
        ecdsa_ptr : SignatureBuiltin*}(hash : felt, sig : (felt, felt), public_key : felt) -> ():
    alloc_locals

    with_attr error_message("==== (INVALID SIGNATURE FOR THE GIVEN MESSAGE HASH) ===="):
        verify_ecdsa_signature(
            message=hash, public_key=public_key, signature_r=sig[0], signature_s=sig[1])
    end

    return ()
end

func verify_all_signatures_deprecated{
        syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr,
        ecdsa_ptr : SignatureBuiltin*}(
        hash : felt, r_sigs_len : felt, r_sigs : felt*, s_sigs_len : felt, s_sigs : felt*,
        public_keys_len : felt, public_keys : felt*) -> ():
    alloc_locals

    if r_sigs_len == 0:
        return ()
    end

    let r_sig = r_sigs[0]
    let s_sig = s_sigs[0]
    let pub_key = public_keys[0]

    verify_sig(hash, (r_sig, s_sig), pub_key)

    return verify_all_signatures_deprecated(
        hash,
        r_sigs_len - 1,
        &r_sigs[1],
        s_sigs_len - 1,
        &s_sigs[1],
        public_keys_len - 1,
        &public_keys[1])
end

# ## ==================================================================================
# ## VERIFY ARRAY IS SORTED

func assert_array_sorted{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        arr_len : felt, arr : felt*) -> ():
    if arr_len == 1:
        return ()
    end

    let current = arr[0]
    let next = arr[1]
    with_attr error_message("==== (ARRAY ELEMENTS ARE NOT SORTED ASCENDINGLY) ===="):
        assert_le(current, next)
    end

    return assert_array_sorted(arr_len - 1, &arr[1])
end
