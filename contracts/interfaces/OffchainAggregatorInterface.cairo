%lang starknet

from starkware.cairo.common.uint256 import (
    Uint256, uint256_add, uint256_sub, uint256_le, uint256_lt, uint256_check)

from contracts.structs.Response_struct import Response

@contract_interface
namespace IOffchainAggregator:
    func latestConfigDetails() -> (config_count : felt, block_num : felt, config_digest : felt):
    end
    func latestTransmissionDetails() -> (
            config_digest : felt, epoch : felt, round : felt, latest_answer : felt,
            latest_timestamp : felt):
    end
    func transmitters() -> (transmitters_len : felt, transmitters : felt*):
    end
    func latestAnswer() -> (res : felt):
    end
    func latestTimestamp() -> (res : felt):
    end
    func latestRound() -> (res : felt):
    end
    func getAnswer(roundId : felt) -> (res : felt):
    end
    func getTimestamp(roundId : felt) -> (res : felt):
    end
    func getRoundData(roundId : felt) -> (res : Response):
    end
    func latestRoundData() -> (res : Response):
    end
    func description() -> (res : felt):
    end
    func decimals() -> (res : felt):
    end
end
