%lang starknet
%builtins pedersen range_check ecdsa

from starkware.cairo.common.cairo_builtins import HashBuiltin, SignatureBuiltin
from starkware.starknet.common.syscalls import (
    get_caller_address, get_contract_address, get_tx_signature, get_tx_info, TxInfo)
from starkware.cairo.common.alloc import alloc
from starkware.cairo.common.hash import hash2
from starkware.cairo.common.registers import get_fp_and_pc
from starkware.cairo.common.uint256 import Uint256
from starkware.cairo.common.signature import verify_ecdsa_signature
from starkware.cairo.common.math import unsigned_div_rem, assert_le, split_int
from starkware.cairo.common.math_cmp import is_le
from starkware.cairo.common.pow import pow
# from starkware.starknet.common.syscalls import get_tx_info, TxInfo) v- 0.8.0

from contracts.libraries.Math64x61 import (
    Math64x61_to64x61, Math64x61_from64x61, Math64x61_mul, Math64x61_div, Math64x61_pow)
from contracts.libraries.Hexadecimals import decimal_to_hex_array, hex64_to_array
from contracts.OffchainAggregator.utils import hash_report

@event
func sig_event(sig_len : felt, sig : felt*):
end

@storage_var
func s_signers(idx : felt) -> (res : felt):
end

@view
func test_verify_sig{
        syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr,
        ecdsa_ptr : SignatureBuiltin*}(hash : felt, sig : (felt, felt), public_key : felt) -> ():
    alloc_locals

    with_attr error_message("==== (INVALID SIGNATURE FOR THE GIVEN MESSAGE HASH) ===="):
        verify_ecdsa_signature(
            message=hash, public_key=public_key, signature_r=sig[0], signature_s=sig[1])
    end

    return ()
end

@view
func test_verify_all_sigs{
        syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr,
        ecdsa_ptr : SignatureBuiltin*}(
        rrc : felt, robs : felt, obs_len : felt, obs : felt*, r_sigs_len : felt, r_sigs : felt*,
        s_sigs_len : felt, s_sigs : felt*, public_keys_len : felt, public_keys : felt*) -> ():
    alloc_locals

    let (hash : felt) = hash2{hash_ptr=pedersen_ptr}(rrc, robs)
    let (hash : felt) = hash_array(obs_len, obs, hash)

    test_verify_all_sigs_inner(
        hash, r_sigs_len, r_sigs, s_sigs_len, s_sigs, public_keys_len, public_keys)

    return ()
end

@view
func test_verify_all_sigs_inner{
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

    test_verify_sig(hash, (r_sig, s_sig), pub_key)

    return test_verify_all_sigs_inner(
        hash,
        r_sigs_len - 1,
        &r_sigs[1],
        s_sigs_len - 1,
        &s_sigs[1],
        public_keys_len - 1,
        &public_keys[1])
end

# ========================================================================================================

@external
func set_signers{
        syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr,
        ecdsa_ptr : SignatureBuiltin*}(signers_len : felt, signers : felt*, count : felt) -> ():
    alloc_locals

    if signers_len == 0:
        return ()
    end

    s_signers.write(idx=count, value=signers[0])

    return set_signers(signers_len - 1, &signers[1], count + 1)
end

@view
func test_verify_all_sigs_reordered{
        syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr,
        ecdsa_ptr : SignatureBuiltin*}(
        rrc : felt, robs : felt, obs_len : felt, obs : felt*, r_sigs_len : felt, r_sigs : felt*,
        s_sigs_len : felt, s_sigs : felt*) -> (x):
    alloc_locals

    let (hex_observers_len, hex_observers : felt*) = decimal_to_hex_array(robs, 31)
    let (msg_hash) = hash_report(rrc, robs, obs_len, obs)

    test_verify_all_sigs_reordered_inner(
        msg_hash, r_sigs_len, r_sigs, s_sigs_len, s_sigs, hex_observers_len, hex_observers)

    return (1)
end

@view
func test_verify_all_sigs_reordered_inner{
        syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr,
        ecdsa_ptr : SignatureBuiltin*}(
        hash : felt, r_sigs_len : felt, r_sigs : felt*, s_sigs_len : felt, s_sigs : felt*,
        observer_idxs_len : felt, observer_idxs : felt*) -> ():
    alloc_locals

    if r_sigs_len == 0:
        return ()
    end

    let r_sig = r_sigs[0]
    let s_sig = s_sigs[0]
    tempvar idx = observer_idxs[0] * 16 + observer_idxs[1]

    let (pub_key) = s_signers.read(idx)

    test_verify_sig(hash, (r_sig, s_sig), pub_key)

    return test_verify_all_sigs_reordered_inner(
        hash,
        r_sigs_len - 1,
        &r_sigs[1],
        s_sigs_len - 1,
        &s_sigs[1],
        observer_idxs_len - 2,
        &observer_idxs[2])
end

@view
func get_signer{
        syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr,
        ecdsa_ptr : SignatureBuiltin*}(idx : felt) -> (s):
    alloc_locals

    let (signer) = s_signers.read(idx=idx)

    return (signer)
end

# ======================================================================================

@view
func consume_array{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        new_arr_len : felt, new_arr : felt*, arr_len : felt, arr : felt*) -> (
        new_arr_len, new_arr : felt*):
    if arr_len == 0:
        return (new_arr_len, new_arr)
    end

    assert new_arr[new_arr_len] = arr[0]

    return consume_array(new_arr_len + 1, new_arr, arr_len - 1, &arr[1])
end

@view
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

@view
func test_decimal_to_hex_array{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        num : felt) -> (arr_len : felt, arr : felt*):
    let (arr_len : felt, arr : felt*) = decimal_to_hex_array(num, 32)
    # let (arr_len : felt, arr : felt*) = hex64_to_array(num)

    return (arr_len, arr)
end

# ==========================================================================================================

@view
func sort_array{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        new_arr_len : felt, new_arr : felt*, temp_arr_len : felt, temp_arr : felt*, arr_len : felt,
        arr : felt*) -> (new_arr_len, new_arr : felt*):
    if arr_len == 0:
        return (temp_arr_len, temp_arr)
    end

    let el = arr[0]
    let (r_shift : felt) = find_index(new_arr_len, new_arr, el)
    let idx = new_arr_len - r_shift
    assert temp_arr[temp_arr_len] = idx

    return sort_array(new_arr_len + 1, new_arr, temp_arr_len + 1, temp_arr, arr_len - 1, &arr[1])
end

@view
func find_index{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        arr_len : felt, arr : felt*, el : felt) -> (idx : felt):
    if arr_len == 0:
        return (0)
    end

    let current = arr[0]
    let (condition : felt) = is_le(el, current)

    if condition == 1:
        return (arr_len)
    end

    return find_index(arr_len - 1, &arr[1], el)
end

func insert_in_array{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        arr_len : felt, arr : felt*, index : felt, value : felt) -> (new_arr_len, new_arr : felt*):
    alloc_locals

    let (local empty_arr : felt*) = alloc()

    return insert_in_array_inner(0, empty_arr, arr_len, arr, index, value)
end

func insert_in_array_inner{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        new_arr_len : felt, new_arr : felt*, arr_len : felt, arr : felt*, index : felt,
        value : felt) -> (new_arr_len, new_arr : felt*):
    if arr_len == 0:
        return (new_arr_len, new_arr)
    end

    if new_arr_len == index:
        assert new_arr[new_arr_len] = value
        return insert_in_array_inner(new_arr_len + 1, new_arr, arr_len, arr, index, value)
    end

    assert new_arr[new_arr_len] = arr[0]

    return insert_in_array_inner(new_arr_len + 1, new_arr, arr_len - 1, &arr[1], index, value)
end

# ==========================================================================================================

func hash_array{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        arr_len : felt, arr : felt*, hash : felt) -> (hash : felt):
    alloc_locals
    if arr_len == 0:
        return (hash)
    end

    let (hash : felt) = hash2{hash_ptr=pedersen_ptr}(hash, arr[0])

    return hash_array(arr_len - 1, &arr[1], hash)
end

# ==================================================================================================
# --v 0.8.0
# @view
# func test_get_tx_info{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
#         v, a, f, s_len, s : felt*, t, c):
#     alloc_locals

# let (tx_info : TxInfo*) = get_tx_info()
#     # let (tx_info : TxInfo) = [tx_info_ptr]

# let vesion = tx_info.version
#     let address = tx_info.account_contract_address
#     let max_fee = tx_info.max_fee

# let signature_len = tx_info.signature_len
#     let signature = tx_info.signature

# let transaction_hash = tx_info.transaction_hash
#     let chain_id = tx_info.chain_id

# return (vesion, address, max_fee, signature_len, signature, transaction_hash, chain_id)
# end
