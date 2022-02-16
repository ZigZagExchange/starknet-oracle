import ast
import math
import requests

import pytest
from sqlalchemy import null
import asyncio
from pathlib import Path

from dataclasses import dataclass
from decouple import config

from starkware.crypto.signature.signature import private_to_stark_key, sign
from starkware.starknet.public.abi import get_selector_from_name, get_storage_var_address


from starknet_py.net.client import Client
from starknet_py.net.account.account_client import AccountClient, KeyPair
from starknet_py.contract import Contract
from starknet_py.net.models import StarknetChainId, InvokeFunction


OWNER_PRIV_KEY = int(config('OWNER_PRIV_KEY'))
MODERATOR_PRIV_KEY = int(config('MODERATOR_PRIV_KEY'))
EXTERNAL_ORACLE_PRIV_KEY = int(config('EXTERNAL_ORACLE_PRIV_KEY'))

compiled = Path("artifacts/contract.json").read_text()
abi = Path("artifacts/abis/contract.json").read_text()
abi = ast.literal_eval(abi)

account_abi = Path("artifacts/abis/Account.json").read_text()
account_abi = ast.literal_eval(account_abi)

data_source_abi = Path("artifacts/abis/DataSource.json").read_text()
data_source_abi = ast.literal_eval(data_source_abi)

main_oracle_abi = Path("artifacts/abis/MainOracle.json").read_text()
main_oracle_abi = ast.literal_eval(main_oracle_abi)

aggregator_abi = Path("artifacts/abis/Aggregator.json").read_text()
aggregator_abi = ast.literal_eval(aggregator_abi)

consumer_abi = Path("artifacts/abis/Consumer.json").read_text()
consumer_abi = ast.literal_eval(consumer_abi)


contract_addr = "0x176c6cf214add7824b98715977a56f60aea4dc8149b3fc87dfd9cc9f3a3b13e"

owner_addr = "0x05e8e3ffb034bb955aa73bc58d47f8126e9664c5398d0307fbd6dc54f10d867c"
moderator_addr = "0x06adb833832f37235712c11620042b40e535bf99e9e37d577d484a91e0d15bdd"
external_oracle_addr = "0x0419186ee3da4f00da8b9ced6c5d4e46867e2a5fb546fe8dbdf2346a550d9a46"

data_source_addr = "0x01ff6bac95b035983b359c21ba5eef8cf2f901750e02be476d0359723384f807"
aggregator_addr = "0x0713e5351b9f8b4c0be5132d4df8b5c07f90f56589c70d979a20d0c8dac4a468"
main_oracle_addr = "0x077d70364e74ad1dfe979751f583fbff5e0543e7dfff9ddc7b2f6a4540c3afdc"


asset_prices = {
    "maticusdt": 1.8808976391666665,
    "fraxusdt": 0.996,
    "1inchusdt": 1.830085625,
    "daiusdt": 0.9988891073471752,
    "aaveusdt": 179.47609048153842,
    "metisusdt": 190.388499995,
    "solusdt": 106.93956546538462,
    "compusdt": 135.87626153846156,
    "batusdt": 0.884420005,
    "linkusdt": 17.655447234999997,
    "ftmusdt": 2.1610626,
    "adausdt": 1.156999576923077,
    "yfiusdt": 24795.704724599094,
    "btcusdt": 43548.60903503389,
    "avaxusdt": 90.25314643461537,
    "uniusdt": 11.573817974272112,
    "ustusdt": 0.9998864722299763,
    "crousdt": 0.5228493571428572,
    "zrxusdt": 0.6752576844444445,
    "bnbusdt": 415.5871045642857,
    "dydxusdt": 8.004912606666666,
    "kncusdt": 2.0751989999999996,
    "mkrusdt": 2120.6609403145453,
    "keepusdt": 0.6986475366666666,
    "ensusdt": 19.005141666666663,
    "storjusdt": 1.2712491428571426,
    "lunausdt": 54.33879737702167,
    "dogeusdt": 0.1460085117255797,
    "ethusdt": 3111.6257759,
    "manausdt": 3.2018939533333333,
    "shibusdt": 0.00003180848,
    "dotusdt": 20.581113319285716,
    "snxusdt": 5.331355302,
    "xrpusdt": 0.8208104361538463,
    "usdcusdt": 0.9991156142621602,
    "looksusdt": 3.2951054699999998,
}

asset_prices = {k: asset_prices[k] for k in sorted(asset_prices)}

asset_prices_indexes = {k: i for i, k in enumerate(asset_prices)}

multiplied_prices = [int(price * math.pow(10, 8))
                     for price in list(asset_prices.values())]


@dataclass
class KeyPair:
    private_key: int
    public_key: int

    @staticmethod
    def from_private_key(key: int) -> "KeyPair":
        return KeyPair(private_key=key, public_key=private_to_stark_key(key))


@pytest.fixture(scope='module')
def event_loop():
    return asyncio.new_event_loop()


@pytest.fixture(scope='module')
async def contract_factory():

    oracle_key_pair = KeyPair.from_private_key(EXTERNAL_ORACLE_PRIV_KEY)
    owner_key_pair = KeyPair.from_private_key(OWNER_PRIV_KEY)

    oracle_client = AccountClient(
        external_oracle_addr, oracle_key_pair, "testnet")
    owner_client = AccountClient(
        external_oracle_addr, owner_key_pair, "testnet")

    local_network_client = Client("testnet")

    external_oracle_acc = Contract(address=external_oracle_addr, abi=account_abi,
                                   client=local_network_client)

    main_oracle = Contract(address=main_oracle_addr, abi=main_oracle_abi,
                           client=local_network_client)

    data_source = Contract(address=data_source_addr, abi=data_source_abi,
                           client=oracle_client)

    aggregator = Contract(address=data_source_addr, abi=data_source_abi,
                          client=local_network_client)

    return main_oracle, oracle_client, owner_client, external_oracle_acc, data_source, aggregator


@pytest.mark.asyncio
async def test_main_logic(contract_factory):
    main_oracle, oracle_client, owner_client, external_oracle_acc, data_source, aggregator = contract_factory

    r2 = requests.get(
        "https://api.cryptowat.ch/markets/coinbase-pro/ethusd/price")
    price = r2.json()["result"]["price"]

    res1 = await main_oracle.functions["latest_price"].call(14)

    print(price)
    print(res1.price / 10**8)


@pytest.mark.asyncio
async def test_set_oracle_dds(contract_factory):
    main_oracle, oracle_client, _, external_oracle_acc, data_source, _ = contract_factory

    invocation1 = await data_source.functions["set_oracle_address"].invoke(int(main_oracle_addr, 16))

    res = await invocation1.wait_for_acceptance()

    main_oracle_key = get_storage_var_address('main_oracle')
    print(f'main_oracle key: {main_oracle_key}')

    print(res)


@pytest.mark.asyncio
async def test_set_prices_dds(contract_factory):
    main_oracle, oracle_client, _, external_oracle_acc, data_source, _ = contract_factory

    res1 = await main_oracle.functions["latest_price"].call(1)
    print(res1)

    invocation1 = await data_source.functions["set_prices"].invoke(multiplied_prices)

    res = await invocation1.wait_for_acceptance()
    print(res)

    res2 = await main_oracle.functions["latest_price"].call(1)
    print(res2)


@pytest.mark.asyncio
async def test_update_data(contract_factory):
    main_oracle, oracle_client, owner_client, external_oracle_acc, data_source, aggregator = contract_factory

    int_addr = int(main_oracle_addr, 16)
    int_selector = get_selector_from_name("update_data")
    calldata = []
    signature = []

    inp = InvokeFunction(int_addr, int_selector, calldata, signature)
    res = await oracle_client.add_transaction(inp)

    # invocation = await main_oracle.functions["update_data"].invoke()

    # res = await invocation.wait_for_acceptance()

    print(res)


@pytest.mark.asyncio
async def test_propose_new_aggregator(contract_factory):
    _, oracle_client, owner_client, _, _, _ = contract_factory

    int_addr = int(main_oracle_addr, 16)
    int_selector = get_selector_from_name("propose_new_aggregator")
    calldata = [int(aggregator_addr, 16)]
    signature = []

    inp = InvokeFunction(int_addr, int_selector, calldata, signature)
    res = await owner_client.add_transaction(inp)

    print(res)


@pytest.mark.asyncio
async def test_confirm_new_aggregator(contract_factory):
    main_oracle, oracle_client, owner_client, external_oracle_acc, data_source, aggregator = contract_factory

    int_addr = int(main_oracle_addr, 16)
    int_selector = get_selector_from_name("confirm_new_aggregator")
    calldata = [int(aggregator_addr, 16)]
    signature = []

    inp = InvokeFunction(int_addr, int_selector, calldata, signature)
    res = await oracle_client.add_transaction(inp)

    print(res)
