%lang starknet

from starkware.cairo.common.cairo_builtins import HashBuiltin
from starkware.cairo.common.uint256 import Uint256
from starkware.cairo.common.alloc import alloc
from starkware.cairo.common.registers import get_fp_and_pc
from starkware.cairo.common.math import (
    assert_in_range, assert_le, assert_nn_le, assert_lt, assert_not_zero)

from contracts.structs.Response_struct import Response
from contracts.interfaces.DataSourceInterface import IDataSource

# STORAGE VARS ==================================================

@storage_var
func data_source() -> (data_source_address : felt):
end

@storage_var
func indexes_len() -> (len : felt):
end

# CONSTRUCTOR ==================================================

@constructor
func constructor{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        data_source_address : felt):
    data_source.write(data_source_address)

    let (idxs_len : felt) = IDataSource.get_indexes_len(contract_address=data_source_address)
    indexes_len.write(idxs_len)
    return ()
end

# GETTERS ==================================================

@view
func decimals{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        decimals : felt):
    let (data_source_address) = data_source.read()

    let (decimals : felt) = IDataSource.get_decimals(contract_address=data_source_address)
    return (decimals)
end

@view
func latest_answer{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        id : felt) -> (identifier : felt, answer : Uint256):
    let (data_source_address) = data_source.read()

    let (identifier : felt, price : Uint256) = IDataSource.read_price(
        contract_address=data_source_address, id=id)
    return (identifier, price)
end

@view
func latest_timestamp{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        timestamp : felt, block_number : felt):
    let (data_source_address) = data_source.read()

    let (timestamp : felt, block_number : felt) = IDataSource.get_timestamp(
        contract_address=data_source_address)
    return (timestamp, block_number)
end

@view
func latest_round{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        roundId : felt):
    let (data_source_address) = data_source.read()

    let (roundId : felt) = IDataSource.get_round(contract_address=data_source_address)
    return (roundId)
end

@view
func aggregated_round_data{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        a_len : felt, a : Response*):
    alloc_locals

    let (local empty_arr : Response*) = alloc()

    let (local res_array_len, local res_array) = get_response_array(0, empty_arr)

    return (res_array_len, res_array)
end

# HELPERS ==================================================

func round_data{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(id : felt) -> (
        res : Response):
    let (roundId) = latest_round()
    let (identifier, price : Uint256) = latest_answer(id)
    let (timestamp, block_number) = latest_timestamp()
    let (data_source_address) = data_source.read()

    assert_not_zero(roundId)
    assert_not_zero(identifier)
    assert_not_zero(timestamp)
    assert_not_zero(block_number)
    assert_not_zero(data_source_address)

    assert_not_zero(price.low + price.high)

    let response = Response(
        roundId=roundId,
        identifier=identifier,
        answer=price,
        timestamp=timestamp,
        block_number=block_number,
        transmitter=data_source_address)

    return (response)
end

func get_response_array{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        a_len : felt, a : Response*) -> (a_len : felt, a : Response*):
    let (__fp__, _) = get_fp_and_pc()
    let (idxs_len) = indexes_len.read()
    if a_len == idxs_len:
        return (a_len, a)
    end

    let (res : Response) = round_data(a_len)

    assert a[a_len] = res

    return get_response_array(a_len=a_len + 1, a=a)
end

# TESTING FUNCTIONS  ========================================

@view
func read_data_source{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        data_source : felt):
    let (data_source_address) = data_source.read()

    return (data_source_address)
end

@view
func read_indexes_len{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        idxs_len : felt):
    let (idxs_len) = indexes_len.read()

    return (idxs_len)
end
