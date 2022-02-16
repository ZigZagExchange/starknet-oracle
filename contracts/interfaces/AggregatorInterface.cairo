%lang starknet

from starkware.cairo.common.uint256 import (
    Uint256, uint256_add, uint256_sub, uint256_le, uint256_lt, uint256_check)

from contracts.structs.Response_struct import Response

@contract_interface
namespace IAggregator:
    func decimals() -> (res : felt):
    end
    func latest_answer(id : felt) -> (identifier : felt, answer : Uint256):
    end
    func latest_timestamp() -> (timestamp : felt, block_number : felt):
    end
    func latest_round() -> (res : felt):
    end
    func aggregated_round_data() -> (a_len : felt, a : Response*):
    end
end
