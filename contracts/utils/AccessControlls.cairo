%lang starknet

from starkware.cairo.common.cairo_builtins import HashBuiltin
from starkware.starknet.common.syscalls import get_caller_address
from starkware.starknet.common.syscalls import get_block_number, get_block_timestamp
from starkware.cairo.common.math import (
    assert_in_range, assert_le, assert_nn_le, assert_lt, assert_not_zero)

@event
func access_controlls_initialized(
        owner : felt, moderator : felt, external_oracle : felt, block_number : felt):
end
@event
func ownership_transfered(prev_owner : felt, new_owner : felt, block_number : felt):
end
@event
func moderator_changed(prev_moderator : felt, new_moderator : felt, block_number : felt):
end
@event
func external_oracle_changed(
        prev_external_oracle : felt, new_external_oracle : felt, block_number : felt):
end

@storage_var
func owner() -> (res : felt):
end
@storage_var
func moderator() -> (res : felt):
end  # not sure where moderator will be used yet
@storage_var
func external_oracle() -> (res : felt):
end

func set_access_controlls{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        owner_address : felt, moderator_address : felt, external_oracle_address : felt):
    # check addresses are valid (for now not zero)
    assert_not_zero(owner_address)
    assert_not_zero(moderator_address)
    assert_not_zero(external_oracle_address)

    # set addresses
    owner.write(value=owner_address)
    moderator.write(value=moderator_address)
    external_oracle.write(value=external_oracle_address)

    let (block_number) = get_block_number()
    access_controlls_initialized.emit(
        owner=owner_address,
        moderator=moderator_address,
        external_oracle=external_oracle_address,
        block_number=block_number)

    return ()
end

# ============== MODIFIERS ===========================

func only_owner{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> ():
    let (msg_sender) = get_caller_address()
    let (_owner) = owner.read()

    assert msg_sender = _owner
    return ()
end

func only_owner_or_moderator{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        ) -> ():
    let (msg_sender) = get_caller_address()
    let (_moderator) = moderator.read()
    let (_owner) = owner.read()

    if msg_sender == _owner:
        return ()
    else:
        assert msg_sender = _moderator
    end
    return ()
end

func only_external_oracle{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        ):
    let (msg_sender) = get_caller_address()
    let (_external_oracle) = external_oracle.read()

    assert msg_sender = _external_oracle
    return ()
end

func get_owner{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        owner : felt):
    let (_owner) = owner.read()

    return (owner=_owner)
end

func get_external_oracle_address{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        ) -> (oracle : felt):
    let (_ext_oracle) = external_oracle.read()

    return (_ext_oracle)
end

func transfer_ownership{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        new_owner : felt) -> (new_owner : felt):
    only_owner()
    assert_not_zero(new_owner)

    let (prev_owner) = owner.read()
    owner.write(new_owner)

    let (block_number) = get_block_number()
    ownership_transfered.emit(prev_owner=prev_owner, new_owner=new_owner, block_number=block_number)

    return (new_owner=new_owner)
end

func change_moderator{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        new_moderator : felt) -> (new_moderator : felt):
    only_owner()
    assert_not_zero(new_moderator)

    let (prev_moderator) = moderator.read()
    moderator.write(new_moderator)

    let (block_number) = get_block_number()
    moderator_changed.emit(
        prev_moderator=prev_moderator, new_moderator=new_moderator, block_number=block_number)

    return (new_moderator=new_moderator)
end

func change_external_oracle{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        new_external_oracle : felt) -> (new_external_oracle : felt):
    only_owner()
    assert_not_zero(new_external_oracle)

    let (prev_external_oracle) = external_oracle.read()
    external_oracle.write(new_external_oracle)

    let (block_number) = get_block_number()
    external_oracle_changed.emit(
        prev_external_oracle=prev_external_oracle,
        new_external_oracle=new_external_oracle,
        block_number=block_number)

    return (new_external_oracle=new_external_oracle)
end

# TESTING FUNCTIONS ================================================================

func get_access_controll_addresses{
        syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        o : felt, m : felt, eo : felt):
    let (owner_) = owner.read()
    let (moderator_) = moderator.read()
    let (external_oracle_) = external_oracle.read()
    return (owner_, moderator_, external_oracle_)
end
