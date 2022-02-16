# STARKNET ORACLE

![zigzag](https://user-images.githubusercontent.com/57314871/154353264-211a4030-8f5d-4aa8-878f-f654fa242589.png)

---

## USAGE


### Functions:
```
latest_timestamp() -> (ts : felt)   # Returns the timestamp of when prices where last updated
latest_block_number() -> (bn : felt)   # Returns the block number of when prices where last updated
latest_round() -> (roundId: felt)   # Returns the round ID of when prices where last updated
latest_price(id : felt) -> (price: felt)   # takes in the asset ID argument (see below) and returns a Uint256 price
latest_aggregated_prices() -> (prices_len : felt, prices : Uint256*)   # returns a list of Uint256 prices of all assets in order (see below)
latest_round_data(id : felt) -> (res : Response)   # takes in the asset ID argument (see below) and returns the latest Response data (see below)
get_round_data(id : felt, roundId : felt) -> (res : Response)   # takes an asset ID and round ID and returns the Response data of selected asset at round round ID    (Will add a function to find a specific time)
get_aggregated_round_data(roundId : felt) -> (round_data_len : felt, round_data : Response*)   # returns an array of all Responses at round roundId  
```


---



#### Asset IDs:



```
{'1inch': 0, 'aave': 1, 'ada': 2, 'avax': 3, 'bat': 4, 'bnb': 5, 'btc': 6, 'comp': 7, 'cro': 8, 'dai': 9, 'doge': 10, 'dot': 11, 'dydx': 12, 'ens': 13, 'eth': 14, 'ftm': 15, 'keep': 16, 'knc': 17, 'link': 18, 'looks': 19, 'mana': 20, 'matic': 21, 'mkr': 22, 'shib': 23, 'snx': 24, 'sol': 25, 'storj': 26, 'uni': 27, 'ust': 28, 'xrp': 29, 'yfi': 30, 'zrx': 31} 
```


---

#### Response Struct

```
struct Response:
    member roundId : felt  # self-explanatory
    member identifier : felt  # example ETH/USD (hashed index from asset IDs)
    member answer : Uint256  # price returned by request
    member timestamp : felt  # timestamp when request was filled
    member block_number : felt  # block_number when request was filled
    member data_source_address : felt  # address of data-source filleing the requests
end
```


### ADDRESSES

**DataSource** = 0x01ff6bac95b035983b359c21ba5eef8cf2f901750e02be476d0359723384f807

**Aggregator** = 0x0713e5351b9f8b4c0be5132d4df8b5c07f90f56589c70d979a20d0c8dac4a468

**MainOracle** = 0x077d70364e74ad1dfe979751f583fbff5e0543e7dfff9ddc7b2f6a4540c3afdc




