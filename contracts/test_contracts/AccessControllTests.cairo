%lang starknet
%builtins pedersen range_check

from starkware.cairo.common.cairo_builtins import HashBuiltin
from starkware.starknet.common.syscalls import get_block_number, get_block_timestamp
from starkware.starknet.common.syscalls import get_caller_address
from starkware.cairo.common.uint256 import (
    Uint256, uint256_add, uint256_sub, uint256_le, uint256_lt, uint256_mul, uint256_check)
from starkware.cairo.common.hash import hash2

from contracts.utils.AccessControlls import (
    set_access_controlls, get_owner, only_owner, only_owner_or_moderator, only_external_oracle,
    get_access_controll_addresses, transfer_ownership, change_moderator, change_external_oracle)

@constructor
func constructor{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        owner_address : felt, moderator_address : felt, external_oracle_address : felt):
    set_access_controlls(
        owner_address=owner_address,
        moderator_address=moderator_address,
        external_oracle_address=external_oracle_address)
    return ()
end

@view
func read_access_controll_addresses{
        syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        owner_address : felt, moderator_address : felt, external_oracle_address : felt):
    let (o, m, eo) = get_access_controll_addresses()
    return (o, m, eo)
end

@view
func check_only_owner{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> ():
    only_owner()
    return ()
end

@view
func check_only_owner_or_moderator{
        syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> ():
    only_owner_or_moderator()
    return ()
end

@view
func check_only_external_oracle{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        ) -> ():
    only_external_oracle()
    return ()
end

@view
func test_transfer_ownership{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        new_owner : felt) -> (prev_owner : felt, new_owner : felt):
    let (prev_owner) = get_owner()
    transfer_ownership(new_owner)
    let (new_owner) = get_owner()

    return (prev_owner, new_owner)
end

@external
func change_access_controlls{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        new_moderator : felt, new_external_oracle : felt) -> ():
    change_moderator(new_moderator)
    change_external_oracle(new_external_oracle)
    return ()
end
