%lang starknet

from starkware.cairo.common.cairo_builtins import HashBuiltin
from starkware.cairo.common.uint256 import Uint256
from starkware.cairo.common.hash import hash2
from starkware.cairo.common.alloc import alloc
from starkware.starknet.common.syscalls import get_block_number, get_block_timestamp
from starkware.cairo.common.registers import get_fp_and_pc
from starkware.starknet.common.syscalls import get_caller_address

from contracts.structs.Response_struct import Response

# ================================================================
# STORAGE VARS

@storage_var
func USDprices(idx : felt) -> (price : Uint256):
end

@storage_var
func indexes_len() -> (len : felt):
end

@storage_var
func timestamp() -> (timestamp : felt):
end

@storage_var
func block_number() -> (bn : felt):
end

@storage_var
func round() -> (round : felt):
end

@storage_var
func decimals() -> (decimals : felt):
end

@storage_var
func external_oracle() -> (address : felt):
end

@storage_var
func main_oracle() -> (address : felt):
end
# ================================================================
# CONSTRUCTOR

@constructor
func constructor{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        idxs_len : felt, decimals_ : felt, external_oracle_address : felt):
    indexes_len.write(idxs_len)
    decimals.write(decimals_)
    external_oracle.write(external_oracle_address)
    return ()
end

# ================================================================
# SETTERS

@external
func set_prices{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        prices_len : felt, prices : felt*):
    alloc_locals
    only_external_oracle()

    let (idxs_len) = indexes_len.read()

    if prices_len == 0:
        let (block_number_) = get_block_number()
        let (timestamp_) = get_block_timestamp()
        timestamp.write(timestamp_)
        block_number.write(block_number_)

        let (_round) = round.read()
        round.write(_round + 1)

        let (main_oracle_address) = main_oracle.read()
        IOracle.update_data(contract_address=main_oracle_address)
        return ()
    end

    let id = idxs_len - prices_len

    let (id_hash) = hash2{hash_ptr=pedersen_ptr}(id, 0)
    USDprices.write(idx=id_hash, value=Uint256(low=prices[0], high=0))

    return set_prices(prices_len=prices_len - 1, prices=&prices[1])
end

@external
func set_oracle_address{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        main_oracle_address : felt) -> ():
    only_external_oracle()
    main_oracle.write(main_oracle_address)

    return ()
end

# ================================================================
# GETTERS

@view
func read_price{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(id : felt) -> (
        identifier : felt, price : Uint256):
    let (id_hash) = hash2{hash_ptr=pedersen_ptr}(id, 0)
    let (price) = USDprices.read(idx=id_hash)

    return (id_hash, price)  # could also just send id instead of id_hash
end

@view
func get_indexes_len{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        idxs_len : felt):
    let (idxs_len) = indexes_len.read()
    return (idxs_len)
end

@view
func get_decimals{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        decimals : felt):
    let (decimals_) = decimals.read()

    return (decimals_)
end

@view
func get_timestamp{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        timestamp : felt, block_number : felt):
    let (timestamp_) = timestamp.read()
    let (block_number_) = block_number.read()

    return (timestamp_, block_number_)
end

@view
func get_round{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        roundId : felt):
    let (roundId) = round.read()

    return (roundId)
end

# ==================================================

func only_external_oracle{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        ):
    let (msg_sender) = get_caller_address()
    let (_external_oracle) = external_oracle.read()

    assert msg_sender = _external_oracle
    return ()
end

@contract_interface
namespace IOracle:
    func update_data() -> ():
    end
end
