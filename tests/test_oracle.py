import pytest
import asyncio

from starknet_py.net.client import Client
from starknet_py.contract import Contract


main_oracle_addr = "0x077d70364e74ad1dfe979751f583fbff5e0543e7dfff9ddc7b2f6a4540c3afdc"


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

    # Test oracle_functions by changing the index (3)
    res1 = await main_oracle.functions[oracle_functions[3]].call(14)

    print(res1)
