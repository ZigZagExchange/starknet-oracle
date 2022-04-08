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
    initialize_aggregator, _get_aggregator, _get_proposed_aggregator, _propose_new_aggregator,
    _confirm_new_aggregator, _latestTransmissionDetails, _transmitters, _latestAnswer,
    _latestTimestamp, _latestRound, _getAnswer, _getTimestamp, _getRoundData, _latestRoundData,
    _description, _decimals)
from contracts.structs.Response_struct import Response

# ================================================================
# EVENTS

# ================================================================
# STORAGE VARS

# ================================================================
# CONSTRUCTOR

@constructor
func constructor{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        owner_address : felt, aggregator_address : felt):
    set_access_controlls(owner_address=owner_address)
    initialize_aggregator(aggregator_address)

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
func get_proposed_aggregator{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        ) -> (aggregator_address : felt):
    let (aggregator_address) = _get_proposed_aggregator()
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
# GETTERS

@view
func decimals{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        decimals : felt):
    let (decimals) = _decimals()
    return (decimals)
end

@view
func latestTransmissionDetails{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        ) -> (
        config_digest : felt, epoch : felt, round : felt, latest_answer : felt,
        latest_timestamp : felt):
    let (config_digest : felt, epoch : felt, round : felt, latest_answer : felt,
        latest_timestamp : felt) = _latestTransmissionDetails()
    return (config_digest, epoch, round, latest_answer, latest_timestamp)
end

@view
func transmitters{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        transmitters_len : felt, transmitters : felt*):
    let (transmitters_len : felt, transmitters : felt*) = _transmitters()
    return (transmitters_len, transmitters)
end

@view
func latestTimestamp{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        res : felt):
    alloc_locals

    let (res : felt) = _latestTimestamp()

    return (res)
end

@view
func latestAnswer{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        res : felt):
    alloc_locals

    let (res : felt) = _latestAnswer()

    return (res)
end

@view
func latestRound{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        res : felt):
    let (res) = _latestRound()

    return (res)
end

@view
func getAnswer{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        roundId : felt) -> (res : felt):
    alloc_locals

    let (answer) = _getAnswer(roundId)

    return (answer)
end

@view
func getTimestamp{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(roundId) -> (
        res : felt):
    let (timestamp) = _getTimestamp(roundId)

    return (timestamp)
end

@view
func getRoundData{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        roundId : felt) -> (res : Response):
    let (res : Response) = _getRoundData(roundId)

    return (res)
end

@view
func latestRoundData{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        res : Response):
    let (res : Response) = _latestRoundData()

    return (res)
end

@view
func description{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        res : felt):
    let (res : felt) = _description()

    return (res)
end
