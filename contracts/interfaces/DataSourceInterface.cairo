%lang starknet

from starkware.cairo.common.uint256 import (
    Uint256, uint256_add, uint256_sub, uint256_le, uint256_lt, uint256_check)

@contract_interface
namespace IDataSource:
    func read_price(id : felt) -> (identifier : felt, price : Uint256):
    end
    func get_indexes_len() -> (idxs_len : felt):
    end
    func get_decimals() -> (decimals : felt):
    end
    func get_timestamp() -> (timestamp : felt, block_number : felt):
    end
    func get_round() -> (roundId : felt):
    end
end
