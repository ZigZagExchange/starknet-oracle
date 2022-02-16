%lang starknet

from starkware.cairo.common.uint256 import Uint256

# ============== STRUCTS ==============================
struct Response:
    member roundId : felt  # self-explanatory
    member identifier : felt  # example ETH/USD (identified by hash or index)
    member answer : Uint256  # price reurned by request
    member timestamp : felt  # timestamp when request was received
    member block_number : felt  # block_number when request was received
    member data_source_address : felt  # address of where the data is coming from (will be useful later)
end
