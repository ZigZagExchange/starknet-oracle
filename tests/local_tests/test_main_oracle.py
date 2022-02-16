import math

from sqlalchemy import null
import pytest
import asyncio

from starkware.starknet.testing.starknet import Starknet
from starkware.starknet.testing.contract import StarknetContract

from utils import Signer


owner = Signer(111111111111111111111)
moderator = Signer(222222222222222222222)
external_oracle = Signer(333333333333333333333)

# Enables modules.
acc_path = "contracts/OpenZepplin/contracts/Account.cairo"

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


@pytest.fixture(scope='module')
def event_loop():
    return asyncio.new_event_loop()


@pytest.fixture(scope='module')
async def contract_factory():
    starknet = await Starknet.empty()
    owner_acc = await starknet.deploy(
        acc_path,
        constructor_calldata=[owner.public_key]
    )
    moderator_acc = await starknet.deploy(
        acc_path,
        constructor_calldata=[moderator.public_key]
    )
    external_oracle_acc = await starknet.deploy(
        acc_path,
        constructor_calldata=[external_oracle.public_key]
    )

    data_source = await starknet.deploy(
        "contracts/test_contracts/DataSource.cairo",
        constructor_calldata=[len(multiplied_prices), 8]
    )

    aggregator = await starknet.deploy(
        "contracts/test_contracts/Aggregator.cairo",
        constructor_calldata=[data_source.contract_address]
    )

    main_oracle = await starknet.deploy(
        "contracts/MainOracle.cairo",
        constructor_calldata=[
            owner_acc.contract_address,
            moderator_acc.contract_address,
            external_oracle_acc.contract_address,
            aggregator.contract_address,
        ]
    )

    consumer = await starknet.deploy(
        "contracts/test_contracts/Consumer.cairo",
        constructor_calldata=[main_oracle.contract_address]
    )

    await data_source.set_prices(multiplied_prices).invoke()

    await external_oracle.send_transaction(
        account=external_oracle_acc,
        to=main_oracle.contract_address,
        selector_name='update_data',
        calldata=[])

    return starknet, main_oracle, aggregator, data_source, owner_acc, moderator_acc, external_oracle_acc, consumer


@pytest.mark.asyncio
async def test_main_logic(contract_factory):
    starknet, main_oracle, aggregator, data_source, owner_acc, moderator_acc, external_oracle_acc, consumer = contract_factory

    res = await consumer.test_latest_aggregated_prices().call()

    print(res.result),
    # print(len(res.result.res))


@pytest.mark.asyncio
async def test_simple_getters(contract_factory):
    _, main_oracle, _, _, _, _, _ = contract_factory

    timestamp = await main_oracle.latest_timestamp().call()
    block_number = await main_oracle.latest_block_number().call()
    roundId = await main_oracle.latest_round().call()
    decimals = await main_oracle.get_decimals().call()

    print(timestamp.result)
    print(block_number.result)
    print(roundId.result)
    print(decimals.result)

    print("test_simple_getters: PASSED")


@pytest.mark.asyncio
async def test_complex_getters(contract_factory):
    _, main_oracle, _, _, _, _, _ = contract_factory

    roundId = await main_oracle.latest_round().call()

    res1 = await main_oracle.latest_round_data(1).call()
    res2 = await main_oracle.get_aggregated_round_data(roundId.result.roundId).call()

    print(res1.result.res)
    print(len(res2.result.round_data))

    print("test_complex_getters: PASSED")


@pytest.mark.asyncio
async def test_latest_prices(contract_factory):
    _, main_oracle, _, _, _, _, _ = contract_factory

    res = await main_oracle.latest_price(0).call()
    res2 = await main_oracle.latest_aggregated_prices().call()

    print(res.result.price)
    print(len(res2.result.prices))

    print("test_latest_prices: PASSED")


@pytest.mark.asyncio
async def test_base_to_quote_price(contract_factory):
    _, main_oracle, _, _, _, _, _ = contract_factory

    res = await main_oracle.base_to_quote_price(14, 6).invoke()

    x = list(asset_prices.values())[14]
    y = list(asset_prices.values())[6]

    res = res.result.res/math.pow(10, 8)

    assert abs(res-x/y) < 0.0001

    print("test_base_to_quote_price: PASSED")
