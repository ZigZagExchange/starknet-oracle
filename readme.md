

# STARKNET ORACLE

![zigzag](https://user-images.githubusercontent.com/57314871/154353264-211a4030-8f5d-4aa8-878f-f654fa242589.png)



---

## Description:
*Please keep in mind, this is still being developed and has not yet been deployed.*

A great deal of credit goes to the Chainlink team, since this oracle was heavily inspired by their [Offchain Reporting](https://uploads-ssl.webflow.com/5f6b7190899f41fb70882d08/603651a1101106649eef6a53_chainlink-ocr-protocol-paper-02-24-20.pdf) paper.

I will give a brief explanation of our implementation, which consist of the [offchain-oracle-network](https://github.com/ZigZagExchange/starknet-oracle/tree/main/offchain_oracle_network/nodes) and the [onchain-aggregator](https://github.com/ZigZagExchange/starknet-oracle/tree/main/contracts/OffchainAggregator).

The offchain oracle network consist of nodes coordinating amongst themselves to fetch prices from different sources, sign them and distribute them to all other nodes. Once enough nodes come to consensus, they start transmitting the report to the onchain aggregator contract, which then checks that:
1. enough observations have been submitted for a fair report
2. enough nodes have signed the report attesting its validity
3. all signatures are valid
4. the report is recent and has not yet been transmitted  

Since multiple nodes are signing the report, it is impossible for a malicious or faulty node operator to get incorrect prices accepted onchain or prevent honest nodes from transmitting, without at least a third of the operators colluding.


---


### Functions:
This are the most important functions.
```cairo
decimals() -> (decimals) # returned prices are multiplied by 10^decimals
latest_timestamp() -> (ts : felt)   # Returns the timestamp of when prices where last updated
latest_round() -> (roundId: felt)   # Returns the round ID of when prices where last updated
latest_price() -> (price: felt)   # returns a Uint256 price
latest_round_data() -> (res : Response)   # returns the latest Response data (see below)
get_round_data(roundId : felt) -> (res : Response)   # takes a round ID and returns the Response data at round round ID
latestTransmissionDetails() -> (config_digest, epoch, round, latest_answer,latest_timestamp):  # returns the latest transmission details
```

### NOTE:
*Prices returned by the oracle are multiplied by 10^decimals because cairo doesn't support decimal numbers


---


#### Response Struct

```cairo
struct Response:
    member roundId : felt  # self-explanatory
    member identifier : felt  # example ETH/USD (hashed index from asset IDs)
    member answer : Uint256  # price returned by request
    member timestamp : felt  # timestamp when request was filled
    member block_number : felt  # block_number when request was filled
    member transmitter : felt  # address of the sender of the transmission
end
```


