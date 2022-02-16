# Declare this file as a StarkNet contract and set the required
# builtins.
%lang starknet
%builtins pedersen range_check

from starkware.cairo.common.cairo_builtins import HashBuiltin
from starkware.starknet.common.syscalls import get_caller_address
from starkware.cairo.common.alloc import alloc
from starkware.starknet.common.syscalls import get_contract_address
from starkware.cairo.common.uint256 import Uint256

from contracts.structs.Response_struct import Response

@storage_var
func oracle() -> (address : felt):
end

@constructor
func constructor{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        oracle_address : felt):
    oracle.write(oracle_address)
    return ()
end

@view
func test_latest_price{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        id : felt) -> (res : Uint256):
    alloc_locals
    let (oracle_addr) = oracle.read()
    let (res : Uint256) = IOracle.latest_price(contract_address=oracle_addr, id=id)

    return (res)
end

@view
func test_latest_aggregated_prices{
        syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        res_len : felt, res : Uint256*):
    alloc_locals
    let (oracle_addr) = oracle.read()
    let (res_len, res : Uint256*) = IOracle.latest_aggregated_prices(contract_address=oracle_addr)

    return (res_len, res)
end

@view
func test_latest_round_data{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        id : felt) -> (res : Response):
    alloc_locals
    let (oracle_addr) = oracle.read()
    let (res : Response) = IOracle.latest_round_data(contract_address=oracle_addr, id=id)

    return (res)
end

@view
func test_get_aggregated_round_data{
        syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(roundId : felt) -> (
        res_len : felt, res : Response*):
    alloc_locals
    let (oracle_addr) = oracle.read()
    let (res_len, res : Response*) = IOracle.get_aggregated_round_data(
        contract_address=oracle_addr, roundId=roundId)

    return (res_len, res)
end

# ======================================

@contract_interface
namespace IOracle:
    func latest_price(id : felt) -> (res : Uint256):
    end
    func latest_aggregated_prices() -> (res_len : felt, res : Uint256*):
    end
    func latest_round_data(id : felt) -> (res : Response):
    end
    func get_aggregated_round_data(roundId : felt) -> (
            round_data_len : felt, round_data : Response*):
    end
end
