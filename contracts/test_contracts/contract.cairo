# Declare this file as a StarkNet contract and set the required
# builtins.
%lang starknet
%builtins pedersen range_check

from starkware.cairo.common.cairo_builtins import HashBuiltin
from starkware.starknet.common.syscalls import get_caller_address
from starkware.cairo.common.alloc import alloc
from contracts.libraries.Math64x61 import (
    Math64x61_to64x61, Math64x61_from64x61, Math64x61_mul, Math64x61_div, Math64x61_pow)
from starkware.starknet.common.syscalls import get_contract_address
from starkware.cairo.common.uint256 import Uint256

@event
func address_event(address):
end

@storage_var
func logged_account() -> (res : felt):
end

@storage_var
func owner() -> (res : felt):
end

@storage_var
func success() -> (res : felt):
end

@constructor
func constructor{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}():
    let (contract_address) = get_contract_address()
    address_event.emit(address=contract_address)
    return ()
end

@view
func test_fractals{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(x : felt) -> (
        res : felt):
    let (res : felt) = Math64x61_to64x61(x)
    let (res2 : felt) = Math64x61_from64x61(res)

    return (res2)
end

@view
func test_fractal_div{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        x : felt, y : felt) -> (res : felt):
    alloc_locals
    let decimals_ = 8

    let ten : felt = Math64x61_to64x61(10)

    let (multiplier : felt) = Math64x61_pow(ten, decimals_)

    let (x : felt) = Math64x61_to64x61(x)
    let (y : felt) = Math64x61_to64x61(y)

    let (x_multiplied : felt) = Math64x61_mul(x, multiplier)

    let (div : felt) = Math64x61_div(x_multiplied, y)

    let (res : felt) = Math64x61_from64x61(div)

    return (res)
end

@external
func log_address{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> ():
    let (contract_address) = get_caller_address()
    logged_account.write(contract_address)
    return ()
end

@view
func read_logged_address{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        address : felt):
    let (contract_address) = logged_account.read()
    return (contract_address)
end

@view
func get_caller{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        res : felt):
    let (caller_address) = get_caller_address()
    return (caller_address)
end

@view
func return_array{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        arr_len : felt, arr : Uint256*):
    alloc_locals

    let (local arr : Uint256*) = alloc()

    let (arr_len : felt, arr : Uint256*) = make_array(0, arr, 1)

    return (arr_len, arr)
end

func make_array{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        _prices_len : felt, _prices : Uint256*, count) -> (prices_len : felt, prices : Uint256*):
    # let (__fp__, _) = get_fp_and_pc()

    if _prices_len == 10:
        return (_prices_len, _prices)
    end

    assert _prices[_prices_len] = Uint256(low=count, high=0)

    return make_array(_prices_len + 1, _prices, count + 1)
end

@external
func set_owner{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        owner_address : felt) -> ():
    owner.write(owner_address)
    return ()
end

@external
func test_access{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> ():
    only_owner_check()

    success.write(1)
    return ()
end

@view
func test_access_func{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        x : felt):
    let (x : felt) = success.read()
    return (x)
end

func only_owner_check{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> ():
    let (contract_address) = get_caller_address()
    let (owner_) = owner.read()

    assert owner_ = contract_address

    return ()
end
