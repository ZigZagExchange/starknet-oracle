# %lang starknet

# # AggregatorProxy is AggregatorInterface

# from starkware.cairo.common.cairo_builtins import HashBuiltin
# from starkware.starknet.common.syscalls import get_block_number, get_block_timestamp
# from starkware.starknet.common.syscalls import get_caller_address
# from starkware.cairo.common.uint256 import (
#     Uint256, uint256_add, uint256_sub, uint256_le, uint256_lt, uint256_mul, uint256_check)
# from starkware.cairo.common.hash import hash2
# from starkware.cairo.common.math import (
#     assert_in_range, assert_le, assert_nn_le, assert_lt, assert_not_zero)

# from contracts.utils.AccessControlls import (
#     only_owner, set_access_controlls, get_owner, only_external_oracle)
# from contracts.interfaces.AggregatorInterface import IAggregator
# from contracts.structs.Response_struct import Response

# from contracts.MainOracle import (
#     latest_answer, latest_timestamp, latest_round, get_round_data, latest_round_data,
#     get_aggregator, get_proposed_agregator, decimals, propose_new_aggregator,
#     confirm_new_aggregator)

# @view
# func get_aggregator_address{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
#         ) -> (aggregator_address : felt):
#     let (aggregator_address) = get_aggregator()
#     return (aggregator_address)
# end

# @view
# func get_proposed_agregator_address{
#         syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
#         aggregator_address : felt):
#     let (aggregator_address) = get_proposed_agregator()
#     return (aggregator_address)
# end

# # ====================================================

# @view
# func test_latest_answer{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
#         answer : felt):
#     let (answer : Uint256) = latest_answer()
#     return (answer.low)
# end

# @view
# func test_latest_timestamp{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
#         timestamp : felt):
#     let (timestamp : felt) = latest_timestamp()
#     return (timestamp)
# end

# @view
# func test_latest_round{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
#         roundId : felt):
#     let (roundId : felt) = latest_round()
#     return (roundId)
# end

# # ====================================================

# @view
# func test_get_round_data{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
#         roundId : felt) -> (response : Response):
#     let (response : Response) = get_round_data(roundId)
#     return (response)
# end

# @view
# func test_latest_round_data{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
#         ) -> (response : Response):
#     let (response : Response) = latest_round_data()
#     return (response)
# end

# # ====================================================

# @view
# func test_propose_new_aggregator{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
#         new_aggregator : felt) -> ():
#     propose_new_aggregator(new_aggregator)
#     return ()
# end

# @view
# func test_confirm_new_aggregator{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
#         new_aggregator : felt) -> ():
#     confirm_new_aggregator(new_aggregator)
#     return ()
# end
