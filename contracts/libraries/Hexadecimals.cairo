%lang starknet

from starkware.cairo.common.cairo_builtins import HashBuiltin
from starkware.cairo.common.math_cmp import is_le, is_not_zero
from starkware.cairo.common.pow import pow
from starkware.cairo.common.alloc import alloc
from starkware.cairo.common.math import (
    assert_le, assert_lt, sqrt, sign, abs_value, signed_div_rem, unsigned_div_rem, assert_not_zero,
    split_felt)

func decimal_to_hex_array{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        num : felt, bytes : felt) -> (a_len, a : felt*):
    # (new_arr_len : felt, new_arr : felt*):
    alloc_locals

    let (local arr : felt*) = alloc()

    let (high, low) = split_felt(num)

    split_hex_loop(high, low, 16, 0, arr, 0)

    tempvar start = (32 - bytes) * 2
    tempvar stop = 64

    let (arr_len : felt, arr : felt*) = splice_array(64, arr, start, stop)

    return (arr_len, arr)
end

func input_array_to_hex_array{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        arr_len : felt, arr : felt*, new_arr_len : felt, new_arr : felt*) -> (
        new_arr_len : felt, new_arr : felt*):
    alloc_locals

    # arr[0][0] = high ;  arr[0][1] = low
    if arr_len == 0:
        return (new_arr_len, new_arr)
    end

    let (a_len, a : felt*) = decimal_to_hex_array(arr[new_arr_len])

    # TODO: what to do with returned hex arrays
    assert new_arr[new_arr_len] = a_len

    return input_array_to_hex_array(arr_len - 1, &arr[0], new_arr_len + 1, new_arr)
end

# @param num is a tuple containing the high and low part,
# where the high part is the first half of the hex string and low is the second
func hex64_to_array_deprecated{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        num : (felt, felt)) -> (res_len : felt, res : felt*):
    alloc_locals

    let (local arr : felt*) = alloc()

    let high = num[0]
    let low = num[1]

    # assert high and low are below 16**32

    split_hex_loop(high, low, 16, 0, arr, 0)

    return (64, arr)
end

# ==================================================================================================

func split_hex_loop{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        a : felt, b : felt, n : felt, arr_len : felt, arr : felt*, count : felt) -> ():
    alloc_locals
    if n == 0:
        assert arr[count] = a
        assert arr[count + 1] = b
        return ()
    end

    # TODO Change this with functions from cairo.math for splitting
    let (devisor : felt) = pow(16, n)
    let (q1, r1) = unsigned_div_rem(a, devisor)
    let (q2, r2) = unsigned_div_rem(b, devisor)

    let (n_, nr) = unsigned_div_rem(n, 2)

    split_hex_loop(q1, r1, n_, 0, arr, count)
    split_hex_loop(q2, r2, n_, 0, arr, count + 2 * n)

    return ()
end

# ..................................................................................

func splice_array{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        arr_len : felt, arr : felt*, start : felt, stop : felt) -> (
        new_arr_len : felt, new_arr : felt*):
    alloc_locals
    let (local empty_arr : felt*) = alloc()

    return splice_array_inner(arr_len, arr, start, stop, 0, empty_arr)
end

func splice_array_inner{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        arr_len : felt, arr : felt*, start : felt, stop : felt, new_arr_len : felt,
        new_arr : felt*) -> (new_arr_len : felt, new_arr : felt*):
    alloc_locals
    if start == stop:
        return (new_arr_len, new_arr)
    end

    assert new_arr[new_arr_len] = arr[start]

    return splice_array_inner(arr_len, arr, start + 1, stop, new_arr_len + 1, new_arr)
end

# ==================================================================================================

func hex_array_to_decimal{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        arr_len : felt, arr : felt*) -> (res : felt):
    return hex_array_to_decimal_inner(arr_len, arr, 0)
end

func hex_array_to_decimal_inner{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        arr_len : felt, arr : felt*, sum : felt) -> (res : felt):
    alloc_locals

    if arr_len == 0:
        return (sum)
    end

    let (multiplier : felt) = pow(16, arr_len - 1)
    tempvar x = arr[0] * multiplier

    let sum = sum + x

    return hex_array_to_decimal_inner(arr_len - 1, &arr[1], sum)
end
