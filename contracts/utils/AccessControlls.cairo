%lang starknet

from starkware.cairo.common.cairo_builtins import HashBuiltin
from starkware.starknet.common.syscalls import get_caller_address
from starkware.starknet.common.syscalls import get_block_number, get_block_timestamp
from starkware.cairo.common.math import (
    assert_in_range, assert_le, assert_nn_le, assert_lt, assert_not_zero)

@event
func access_controlls_initialized(owner : felt, external_oracle : felt, block_number : felt):
end
@event
func ownership_transfered(prev_owner : felt, new_owner : felt, block_number : felt):
end
@event
func external_oracle_changed(
        prev_external_oracle : felt, new_external_oracle : felt, block_number : felt):
end

@storage_var
func owner() -> (res : felt):
end
@storage_var
func external_oracle() -> (res : felt):
end

func set_access_controlls{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        owner_address : felt):
    # check addresses are valid (for now not zero)
    assert_not_zero(owner_address)
    # assert_not_zero(external_oracle_address)

    owner.write(value=owner_address)
    # external_oracle.write(value=external_oracle_address)

    let (block_number) = get_block_number()
    access_controlls_initialized.emit(
        owner=owner_address, external_oracle=0, block_number=block_number)

    return ()
end

# ============== MODIFIERS ===========================

func only_owner{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> ():
    let (msg_sender) = get_caller_address()
    let (_owner) = owner.read()

    assert msg_sender = _owner
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
        o : felt, eo : felt):
    let (owner_) = owner.read()
    let (external_oracle_) = external_oracle.read()
    return (owner_, external_oracle_)
end
