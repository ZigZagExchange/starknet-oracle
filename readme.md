# STARKNET ORACLE

![zigzag](https://user-images.githubusercontent.com/57314871/154353264-211a4030-8f5d-4aa8-878f-f654fa242589.png)


---

## USAGE



### ADDRESS

**MainOracle** = 0x03e8cc88d807820c4d7ad76c8f615dcbb9db0408a9318666dd114b388263369a



### Functions:
```cairo
latest_timestamp() -> (ts : felt)   # Returns the timestamp of when prices where last updated
latest_block_number() -> (bn : felt)   # Returns the block number of when prices where last updated
latest_round() -> (roundId: felt)   # Returns the round ID of when prices where last updated
latest_price(id : felt) -> (price: felt)   # takes in the asset ID argument (see below) and returns a Uint256 price
latest_aggregated_prices() -> (prices_len : felt, prices : Uint256*)   # returns a list of Uint256 prices of all assets in order (see below)
latest_round_data(id : felt) -> (res : Response)   # takes in the asset ID argument (see below) and returns the latest Response data (see below)
get_round_data(id : felt, roundId : felt) -> (res : Response)   # takes an asset ID and round ID and returns the Response data of selected asset at round round ID    (Will add a function to find a specific time)
get_aggregated_round_data(roundId : felt) -> (round_data_len : felt, round_data : Response*)   # returns an array of all Responses at round roundId  
base_to_quote_price(base : felt, quote : felt) -> Returns the latest base price denominated in quote price  (E.g ETH/BTC; ETH=base, BTC=quote)
```

### NOTE:
__Prices returned by the oracle are multiplied by 10**6 because cairo doesn't support decimal numbers__



---


#### Asset IDs:



```
{'1inch': 0, 'aave': 1, 'ada': 2, 'avax': 3, 'bat': 4, 'bnb': 5, 'btc': 6, 'comp': 7, 'cro': 8, 'dai': 9, 'doge': 10, 'dot': 11, 'dydx': 12, 'ens': 13, 'eth': 14, 'ftm': 15, 'keep': 16, 'knc': 17, 'link': 18, 'looks': 19, 'mana': 20, 'matic': 21, 'mkr': 22, 'shib': 23, 'snx': 24, 'sol': 25, 'storj': 26, 'uni': 27, 'ust': 28, 'xrp': 29, 'yfi': 30, 'zrx': 31} 
```


---

#### Response Struct

```cairo
struct Response:
    member roundId : felt  # self-explanatory
    member identifier : felt  # example ETH/USD (hashed index from asset IDs)
    member answer : Uint256  # price returned by request
    member timestamp : felt  # timestamp when request was filled
    member block_number : felt  # block_number when request was filled
    member data_source_address : felt  # address of data-source filleing the requests
end
```

---


### EXAMPLE

You can find a simple test script below, to try out some of the oracle functions in python. To use it download the [test_oracle.py](https://github.com/ZigZagExchange/starknet-oracle/blob/main/tests/test_oracle.py) file and make sure you have all the dependecies isnstalled (see below).

Run the file wit this command: 
`pytest -s <PATH_TO_FILE>/test_oracle.py::test_main_logic`

```python

oracle_functions = ["latest_timestamp", "latest_block_number", "latest_round",
                    "latest_price", "latest_aggregated_prices", "get_round_data", "base_to_quote_price"]


@pytest.mark.asyncio
async def test_main_logic(contract_factory):
    main_oracle = contract_factory

    # Test oracle_functions by changing the index (3)
    res1 = await main_oracle.functions[oracle_functions[3]].call(14)

    print(res1)

```

#### Requirements:

__pytest__:              ` pip install pytest `   
__starknet_py__:         ` pip install starknet.py `



---





