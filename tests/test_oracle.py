import pytest
import asyncio
import requests
import time

from starknet_py.net.client import Client
from starknet_py.contract import Contract


main_oracle_addr = "0x03e8cc88d807820c4d7ad76c8f615dcbb9db0408a9318666dd114b388263369a"


@pytest.fixture(scope='module')
def event_loop():
    return asyncio.new_event_loop()


@pytest.fixture(scope='module')
async def contract_factory():

    local_network_client = Client("testnet")

    main_oracle = await Contract.from_address(address=main_oracle_addr,
                                              client=local_network_client)

    return main_oracle


oracle_functions = ["latest_timestamp", "latest_block_number", "latest_round",
                    "latest_price", "latest_aggregated_prices", "get_round_data", "base_to_quote_price"]


@pytest.mark.asyncio
async def test_main_logic(contract_factory):
    main_oracle = contract_factory

    total_err = 0
    num_steps = 0

    while True:

        res1 = await main_oracle.functions[oracle_functions[3]].call(14)

        r2 = requests.get(
            "https://api.cryptowat.ch/markets/coinbase-pro/ethusd/price")
        price = r2.json()["result"]["price"]

        diff = abs(res1.price/10**6 - price)
        error = diff / price

        total_err += error
        num_steps += 1
        avg_err = total_err / num_steps

        print(f"{oracle_functions[3]} error: {error}")
        print(f"{oracle_functions[3]} avg_error: {avg_err}")
        await asyncio.sleep(3)


# async def main(main_oracle):

#     res1 = await main_oracle.functions[oracle_functions[3]].call(14)

#     r2 = requests.get(
#         "https://api.cryptowat.ch/markets/coinbase-pro/ethusd/price")
#     price = r2.json()["result"]["price"]

#     diff = abs(res1.price/10**6 - price)
#     error = diff / price

#     update_err(error)
#     avg_err = read_err()

#     print(f"{oracle_functions[3]} error: {error}")
#     print(f"{oracle_functions[3]} avg_error: {avg_err}")

#     await asyncio.sleep(10)
