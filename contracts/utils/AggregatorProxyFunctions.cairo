%lang starknet

from starkware.cairo.common.cairo_builtins import HashBuiltin
from starkware.starknet.common.syscalls import get_block_number, get_block_timestamp
from starkware.starknet.common.syscalls import get_caller_address
from starkware.cairo.common.uint256 import (
    Uint256, uint256_add, uint256_sub, uint256_le, uint256_lt, uint256_mul, uint256_check)
from starkware.cairo.common.hash import hash2
from starkware.cairo.common.math import (
    assert_in_range, assert_le, assert_nn_le, assert_lt, assert_not_zero)

from contracts.utils.AccessControlls import (
    only_owner, only_owner_or_moderator, set_access_controlls, get_owner, only_external_oracle)
from contracts.interfaces.AggregatorInterface import IAggregator
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
    aggregator.write(aggregator_address)
    return ()
end

func _get_aggregator{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        aggregator_address : felt):
    let (aggregator_address) = aggregator.read()

    return (aggregator_address)
end

func _get_proposed_agregator{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        ) -> (aggregator_address : felt):
    let (proposed_aggregator_address) = proposed_aggregator.read()

    return (proposed_aggregator_address)
end

func _propose_new_aggregator{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        new_aggregator : felt) -> ():
    assert_not_zero(new_aggregator)  # TODO: Check that it's a valid address not just non-zero
    only_owner_or_moderator()

    let (block_number) = get_block_number()
    let (msg_sender) = get_caller_address()
    let (_aggregator) = aggregator.read()

    proposed_aggregator.write(new_aggregator)
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
    proposed_aggregator.write(0)
    aggregator.write(new_aggregator)

    new_aggregator_accepted.emit(
        prev_aggretgator=_aggregator, new_aggregator=new_aggregator, block_number=block_number)
    return ()
end

# ================================================================
# GETTER FUNCTIONS  (helper functions for MainOracle)

func _decimals{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        decimals : felt):
    let (aggregator_address) = aggregator.read()
    let (decimals : felt) = IAggregator.decimals(contract_address=aggregator_address)

    return (decimals)
end

func _latest_timestamp{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        timestamp : felt, block_number : felt):
    let (aggregator_address) = aggregator.read()
    let (timestamp, block_number) = IAggregator.latest_timestamp(
        contract_address=aggregator_address)

    assert_not_zero(timestamp)
    return (timestamp, block_number)
end

func _latest_round{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        roundId : felt):
    let (aggregator_address) = aggregator.read()
    let (roundId) = IAggregator.latest_round(contract_address=aggregator_address)

    assert_not_zero(roundId)
    return (roundId)
end

func _latest_answer{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        id : felt) -> (identifier : felt, answer : Uint256):
    alloc_locals
    let (aggregator_address) = aggregator.read()
    let (local identifier : felt, local answer : Uint256) = IAggregator.latest_answer(
        contract_address=aggregator_address, id=id)

    assert_not_zero(answer.low + answer.high)
    return (identifier, answer)
end

func _latest_round_data{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        round_data_len : felt, round_data : Response*):
    alloc_locals
    let (aggregator_address) = aggregator.read()

    let (round_data_len : felt, local round_data : Response*) = IAggregator.aggregated_round_data(
        contract_address=aggregator_address)

    return (round_data_len, round_data)
end
