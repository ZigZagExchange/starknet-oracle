%lang starknet
%builtins pedersen range_check

from starkware.cairo.common.cairo_builtins import HashBuiltin
from starkware.starknet.common.syscalls import get_block_number, get_block_timestamp
from starkware.starknet.common.syscalls import get_caller_address
from starkware.cairo.common.registers import get_fp_and_pc
from starkware.cairo.common.alloc import alloc
from starkware.cairo.common.uint256 import (
    Uint256, uint256_add, uint256_sub, uint256_le, uint256_lt, uint256_mul, uint256_check)
from starkware.cairo.common.hash import hash2
from contracts.libraries.Math64x61 import (
    Math64x61_to64x61, Math64x61_from64x61, Math64x61_mul, Math64x61_div, Math64x61_pow)

from contracts.utils.AccessControlls import (
    only_owner, set_access_controlls, get_owner, only_external_oracle, get_external_oracle_address)
from contracts.utils.AggregatorProxyFunctions import (
    initialize_aggregator, _get_aggregator, _get_proposed_agregator, _latest_answer,
    _latest_timestamp, _latest_round_data, _latest_round, _decimals, _propose_new_aggregator,
    _confirm_new_aggregator)
from contracts.structs.Response_struct import Response

# ================================================================
# EVENTS

@event
func round_data_updated(roundId : felt, timestamp : felt, block_number : felt):
end

# ================================================================
# STORAGE VARS

@storage_var
func round_data(identifier : felt, roundId : felt) -> (round_data : Response):
end

@storage_var
func price(identifier : felt) -> (price : Uint256):
end

@storage_var
func round() -> (roundId : felt):
end

@storage_var
func timestamp() -> (timestamp : felt):
end

@storage_var
func block_number() -> (block_number : felt):
end

@storage_var
func decimals() -> (decimals : felt):
end

@storage_var
func indexes_len() -> (idxs_len : felt):
end

@storage_var
func aggregator_proxy() -> (address : felt):
end

# ================================================================
# CONSTRUCTOR

@constructor
func constructor{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        owner_address : felt, moderator_address : felt, external_oracle_address : felt,
        aggregator_address : felt):
    set_access_controlls(
        owner_address=owner_address,
        moderator_address=moderator_address,
        external_oracle_address=external_oracle_address)

    initialize_aggregator(aggregator_address)

    let (decimals_) = _decimals()
    decimals.write(decimals_)
    return ()
end

# ================================================================
# AGGREGATOR FUNCTIONS
@view
func get_aggregator{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        aggregator_address : felt):
    let (aggregator_address) = _get_aggregator()
    return (aggregator_address)
end

@view
func get_proposed_agregator{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        ) -> (aggregator_address : felt):
    let (aggregator_address) = _get_proposed_agregator()
    return (aggregator_address)
end

@external
func propose_new_aggregator{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        new_aggregator_address : felt) -> ():
    _propose_new_aggregator(new_aggregator_address)
    return ()
end

@external
func confirm_new_aggregator{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        new_aggregator_address : felt) -> ():
    _confirm_new_aggregator(new_aggregator_address)
    return ()
end

# ================================================================
# SETTERS

@external
func update_data{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> ():
    alloc_locals
    # only_external_oracle()

    let (timestamp_, block_number_) = _latest_timestamp()
    timestamp.write(timestamp_)
    block_number.write(block_number_)

    let (roundId) = _latest_round()
    round.write(roundId)

    let (local round_data_len : felt, local round_data : Response*) = _latest_round_data()

    indexes_len.write(round_data_len)

    store_round_data(round_data_len, round_data, roundId)

    store_latest_prices(round_data_len, round_data)

    round_data_updated.emit(roundId=roundId, timestamp=timestamp_, block_number=block_number_)
    return ()
end

# ================================================================
# GETTERS

@view
func get_external_oracle{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        address : felt):
    let (_ext_oracle) = get_external_oracle_address()
    return (_ext_oracle)
end

@view
func get_decimals{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        decimals : felt):
    let (_decimals) = decimals.read()
    return (_decimals)
end

@view
func latest_timestamp{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        ts : felt):
    let (timestamp_) = timestamp.read()
    return (timestamp_)
end

@view
func latest_block_number{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        block_number : felt):
    let (block_number_) = block_number.read()
    return (block_number_)
end

@view
func latest_round{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        roundId : felt):
    let (roundId) = round.read()
    return (roundId)
end

@view
func latest_price{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(id : felt) -> (
        price : Uint256):
    alloc_locals

    let (id_hash) = hash2{hash_ptr=pedersen_ptr}(id, 0)
    let (local price_ : Uint256) = price.read(id_hash)

    return (price_)
end

@view
func latest_aggregated_prices{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        ) -> (prices_len : felt, prices : Uint256*):
    alloc_locals

    let (idxs_len) = indexes_len.read()
    let (local empty_arr : Uint256*) = alloc()

    let (_prices_len : felt, _prices : Uint256*) = load_latest_prices(0, empty_arr, idxs_len)

    return (_prices_len, _prices)
end

@view
func latest_round_data{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        id : felt) -> (res : Response):
    alloc_locals

    let (roundId) = round.read()

    let (local response) = get_round_data(id, roundId)
    return (response)
end

@view
func get_round_data{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        id : felt, roundId) -> (res : Response):
    alloc_locals

    let (id_hash) = hash2{hash_ptr=pedersen_ptr}(id, 0)

    let (local response) = round_data.read(identifier=id_hash, roundId=roundId)
    return (response)
end

@view
func get_aggregated_round_data{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        roundId : felt) -> (round_data_len : felt, round_data : Response*):
    alloc_locals

    let (idxs_len) = indexes_len.read()
    let (local empty_arr : Response*) = alloc()

    let (round_data_len, round_data) = load_round_data(0, empty_arr, roundId, idxs_len)

    return (round_data_len, round_data)
end

# ================================================================
# STRUCTURED QUERYS (used for getting non usd prices, e.g BTC/ETH)

@view
func base_to_quote_price{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        baseId : felt, quoteId : felt) -> (res : felt):
    alloc_locals

    let (base_hash) = hash2{hash_ptr=pedersen_ptr}(baseId, 0)
    let (quote_hash) = hash2{hash_ptr=pedersen_ptr}(quoteId, 0)

    let (local base_price : Uint256) = price.read(identifier=base_hash)
    let (local quote_price : Uint256) = price.read(identifier=quote_hash)

    let (res : felt) = fractal_div(base_price.low, quote_price.low)

    return (res)
end

func fractal_div{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        x : felt, y : felt) -> (res : felt):
    alloc_locals
    let (decimals_) = decimals.read()

    let ten : felt = Math64x61_to64x61(10)

    let (multiplier : felt) = Math64x61_pow(ten, decimals_)

    let (x : felt) = Math64x61_to64x61(x)
    let (y : felt) = Math64x61_to64x61(y)

    let (div : felt) = Math64x61_div(x, y)

    let (div_multiplied : felt) = Math64x61_mul(div, multiplier)

    let (res : felt) = Math64x61_from64x61(div_multiplied)

    return (res)
end

# HELPERS ===============================================
# CONSIDER MOVING TO SEPERATE FILE ======================

func store_round_data{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        arr_len : felt, arr : Response*, roundId : felt) -> ():
    if arr_len == 0:
        return ()
    end

    let identifier = arr[0].identifier
    round_data.write(identifier=identifier, roundId=roundId, value=arr[0])

    return store_round_data(arr_len=arr_len - 1, arr=&arr[1], roundId=roundId)
end

func load_round_data{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        _round_data_len : felt, _round_data : Response*, roundId : felt, idxs_len) -> (
        round_data_len : felt, round_data : Response*):
    let (__fp__, _) = get_fp_and_pc()

    if _round_data_len == idxs_len:
        return (_round_data_len, _round_data)
    end

    let (id_hash) = hash2{hash_ptr=pedersen_ptr}(_round_data_len, 0)
    let (res : Response) = round_data.read(identifier=id_hash, roundId=roundId)

    assert _round_data[_round_data_len] = res

    return load_round_data(_round_data_len + 1, _round_data, roundId, idxs_len)
end

func store_latest_prices{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        arr_len : felt, arr : Response*) -> ():
    if arr_len == 0:
        return ()
    end

    let identifier = arr[0].identifier
    let price_ = arr[0].answer
    price.write(identifier=identifier, value=price_)

    return store_latest_prices(arr_len=arr_len - 1, arr=&arr[1])
end

func load_latest_prices{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        _prices_len : felt, _prices : Uint256*, idxs_len : felt) -> (
        prices_len : felt, prices : Uint256*):
    if _prices_len == idxs_len:
        return (_prices_len, _prices)
    end

    let (id_hash) = hash2{hash_ptr=pedersen_ptr}(_prices_len, 0)
    let (price_ : Uint256) = price.read(id_hash)

    assert _prices[_prices_len] = price_

    return load_latest_prices(_prices_len + 1, _prices, idxs_len)
end
