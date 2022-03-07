
import time
from tracemalloc import start
from decouple import config
from dataclasses import dataclass
import asyncio
from contextlib import suppress
from unittest import result
import cryptowatch as cw

import requests
import ast
import math

from pathlib import Path

from starknet_py.net.models import StarknetChainId, InvokeFunction
from starknet_py.contract import Contract
from starknet_py.net.account.account_client import AccountClient, KeyPair
from starknet_py.net.client import Client
from starkware.starknet.public.abi import get_selector_from_name
from starkware.crypto.signature.signature import private_to_stark_key


API_KEY = config('API_KEY')
cw.api_key = API_KEY

OWNER_PRIV_KEY = int(config('OWNER_PRIV_KEY'))
EXTERNAL_ORACLE_PRIV_KEY = int(config('EXTERNAL_ORACLE_PRIV_KEY'))


data_source_abi = Path("artifacts/abis/DataSource.json").read_text()
data_source_abi = ast.literal_eval(data_source_abi)

main_oracle_abi = Path("artifacts/abis/MainOracle.json").read_text()
main_oracle_abi = ast.literal_eval(main_oracle_abi)

account_abi = Path("artifacts/abis/MainOracle.json").read_text()
account_abi = ast.literal_eval(main_oracle_abi)


@dataclass
class KeyPair:
    private_key: int
    public_key: int

    @staticmethod
    def from_private_key(key: int) -> "KeyPair":
        return KeyPair(private_key=key, public_key=private_to_stark_key(key))


owner_addr = "0x05e8e3ffb034bb955aa73bc58d47f8126e9664c5398d0307fbd6dc54f10d867c"
external_oracle_addr = "0x07d10fb304e6752b577c1f0b85bdab549c937320f13175c36f623735ad3737ef"

data_source_addr = "0x07f294c1b283fe0ed3fe8b2cbfc5f107050d827e1e40d5cdaf4001c85f600be7"
main_oracle_addr = "0x03e8cc88d807820c4d7ad76c8f615dcbb9db0408a9318666dd114b388263369a"


oracle_key_pair = KeyPair.from_private_key(EXTERNAL_ORACLE_PRIV_KEY)
owner_key_pair = KeyPair.from_private_key(OWNER_PRIV_KEY)

oracle_client = AccountClient(
    external_oracle_addr, oracle_key_pair, "testnet")
owner_client = AccountClient(
    external_oracle_addr, owner_key_pair, "testnet")

main_oracle = Contract(address=main_oracle_addr, abi=main_oracle_abi,
                       client=oracle_client)

data_source = Contract(address=data_source_addr, abi=data_source_abi,
                       client=oracle_client)


coinbase_assets = ['eth', 'btc', 'mkr', 'storj', 'link', 'matic', 'dai', 'keep', 'comp', 'avax', 'yfi', 'shib',
                   'uni', 'ust', 'aave', 'ens', 'zrx', 'bat', 'dot', 'knc', 'snx', 'mana', '1inch', 'ada', 'doge', 'cro']
ftx_assets = ["ftm", "bnb", "dydx", "looks", "sol", 'xrp']


async def set_and_update_prices(multiplied_prices):

    invocation = await data_source.functions["set_prices"].invoke(multiplied_prices)
    res = await invocation.wait_for_acceptance()
    # print(res)


async def get_prices():
    results = {}
    for asset in coinbase_assets:
        try:
            price = cw.markets.get(
                "coinbase-pro" + ":" + asset + "usd")
            price = price.market.price.last
            results[asset] = price

        except cw.errors.APIResourceNotFoundError:
            price = cw.markets.get(
                "coinbase-pro" + ":" + asset + "usdt")
            price = price.market.price.last
            results[asset] = price

    for asset in ftx_assets:
        try:
            price = cw.markets.get(
                "ftx" + ":" + asset + "usd")
            price = price.market.price.last
            results[asset] = price

        except cw.errors.APIResourceNotFoundError:
            price = cw.markets.get(
                "ftx" + ":" + asset + "usdt")
            price = price.market.price.last
            results[asset] = price

    asset_prices = {k: results[k] for k in sorted(results)}
    multiplied_prices = [int(price * math.pow(10, 6))
                         for price in list(asset_prices.values())]

    return multiplied_prices


async def main():
    print("Updating prices...")

    multiplied_prices = await get_prices()

    task = asyncio.Task(set_and_update_prices(multiplied_prices))

    await asyncio.sleep(75)


if __name__ == '__main__':
    while True:
        asyncio.run(main())
