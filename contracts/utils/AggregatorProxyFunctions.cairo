%lang starknet

from starkware.cairo.common.cairo_builtins import HashBuiltin
from starkware.starknet.common.syscalls import get_block_number, get_block_timestamp
from starkware.starknet.common.syscalls import get_caller_address
from starkware.cairo.common.uint256 import (
    Uint256, uint256_add, uint256_sub, uint256_le, uint256_lt, uint256_mul, uint256_check)
from starkware.cairo.common.hash import hash2
from starkware.cairo.common.math import (
    assert_in_range, assert_le, assert_nn_le, assert_lt, assert_not_zero)

from contracts.utils.AccessControlls import only_owner
from contracts.interfaces.AggregatorInterface import IAggregator
from contracts.interfaces.OffchainAggregatorInterface import IOffchainAggregator
from contracts.structs.Response_struct import Response

# ================================================================
# EVENTS
@event
func new_aggregator_proposed(
        current_aggretgator : felt, proposed_aggregator : felt, proposer : felt,
        block_number : felt):
end

@event
func new_aggregator_accepted(prev_aggretgator : felt, new_aggregator : felt, block_number : felt):
end

# ================================================================
# STORAGE VARS
@storage_var
func aggregator() -> (address : felt):
end

@storage_var
func proposed_aggregator() -> (address : felt):
end

# ================================================================
# AGGREGATOR FUNCTIONS

func initialize_aggregator{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        aggregator_address : felt):
    assert_not_zero(aggregator_address)  # TODO: check this is a valid address not just non-zero

    aggregator.write(value=aggregator_address)
    return ()
end

func _get_aggregator{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        aggregator_address : felt):
    let (aggregator_address) = aggregator.read()

    return (aggregator_address)
end

func _get_proposed_aggregator{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        ) -> (aggregator_address : felt):
    let (proposed_aggregator_address) = proposed_aggregator.read()

    return (proposed_aggregator_address)
end

func _propose_new_aggregator{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        new_aggregator : felt) -> ():
    assert_not_zero(new_aggregator)  # TODO: Check that it's a valid address not just non-zero
    only_owner()

    let (block_number) = get_block_number()
    let (msg_sender) = get_caller_address()
    let (_aggregator) = aggregator.read()

    proposed_aggregator.write(value=new_aggregator)
    new_aggregator_proposed.emit(
        current_aggretgator=_aggregator,
        proposed_aggregator=new_aggregator,
        proposer=msg_sender,
        block_number=block_number)
    return ()
end

func _confirm_new_aggregator{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        new_aggregator : felt) -> ():
    assert_not_zero(new_aggregator)  # TODO: Check that it's a valid address not just non-zero
    only_owner()

    let (block_number) = get_block_number()
    let (_aggregator) = aggregator.read()
    let (_proposed_aggregator) = proposed_aggregator.read()

    assert new_aggregator = _proposed_aggregator
    proposed_aggregator.write(value=0)
    aggregator.write(value=new_aggregator)

    new_aggregator_accepted.emit(
        prev_aggretgator=_aggregator, new_aggregator=new_aggregator, block_number=block_number)
    return ()
end

# ================================================================
# GETTER FUNCTIONS  (helper functions for MainOracle)

func _latestTransmissionDetails{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        ) -> (
        config_digest : felt, epoch : felt, round : felt, latest_answer : felt,
        latest_timestamp : felt):
    let (aggregator_address) = aggregator.read()
    let (config_digest, epoch, round, latest_answer,
        latest_timestamp) = IOffchainAggregator.latestTransmissionDetails(
        contract_address=aggregator_address)

    return (config_digest, epoch, round, latest_answer, latest_timestamp)
end

func _transmitters{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        transmitters_len : felt, transmitters : felt*):
    let (aggregator_address) = aggregator.read()
    let (transmitters_len, transmitters) = IOffchainAggregator.transmitters(
        contract_address=aggregator_address)

    return (transmitters_len, transmitters)
end

func _latestAnswer{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        res : felt):
    let (aggregator_address) = aggregator.read()
    let (res : felt) = IOffchainAggregator.latestAnswer(contract_address=aggregator_address)

    return (res)
end

func _latestTimestamp{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        res : felt):
    let (aggregator_address) = aggregator.read()
    let (res) = IOffchainAggregator.latestTimestamp(contract_address=aggregator_address)

    return (res)
end

func _latestRound{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        res : felt):
    let (aggregator_address) = aggregator.read()
    let (res) = IOffchainAggregator.latestRound(contract_address=aggregator_address)

    return (res)
end

func _getAnswer{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        roundId : felt) -> (res : felt):
    let (aggregator_address) = aggregator.read()
    let (res) = IOffchainAggregator.getAnswer(contract_address=aggregator_address, roundId=roundId)

    return (res)
end

func _getTimestamp{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        roundId : felt) -> (res : felt):
    let (aggregator_address) = aggregator.read()
    let (res) = IOffchainAggregator.getTimestamp(
        contract_address=aggregator_address, roundId=roundId)

    return (res)
end

func _getRoundData{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        roundId : felt) -> (res : Response):
    let (aggregator_address) = aggregator.read()
    let (res : Response) = IOffchainAggregator.getRoundData(
        contract_address=aggregator_address, roundId=roundId)

    return (res)
end

func _latestRoundData{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        res : Response):
    let (aggregator_address) = aggregator.read()
    let (res : Response) = IOffchainAggregator.latestRoundData(contract_address=aggregator_address)

    return (res)
end

func _description{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        res : felt):
    let (aggregator_address) = aggregator.read()
    let (res : felt) = IOffchainAggregator.description(contract_address=aggregator_address)

    return (res)
end

func _decimals{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (res : felt):
    let (aggregator_address) = aggregator.read()
    let (res) = IOffchainAggregator.decimals(contract_address=aggregator_address)

    return (res)
end
