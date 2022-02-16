from copyreg import constructor
import math
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

    dds_contract = await starknet.deploy(
        "contracts/test_contracts/DataSource.cairo",
        constructor_calldata=[len(multiplied_prices), 8]
    )

    dag_contract = await starknet.deploy(
        "contracts/test_contracts/Aggregator.cairo",
        constructor_calldata=[dds_contract.contract_address]
    )

    return starknet, dds_contract, dag_contract, owner_acc


@pytest.mark.asyncio
async def test_main_logic(contract_factory):
    starknet, dds_contract, dag_contract, owner_acc = contract_factory

    await dds_contract.set_prices(multiplied_prices).invoke()

    # res = await dag_contract.get_response_array([]).call()
    res = await dag_contract.aggregated_round_data().call()

    for i in range(len(res.result.a)):
        diff = res.result.a[i].answer.low / \
            math.pow(10, 8) - round(list(asset_prices.values())[i], 8)
        assert abs(diff) < 2*math.pow(10, -8)

    print("test_aggregated_round_data: PASSED")


@ pytest.mark.asyncio
async def test_set_get_prices(contract_factory):
    _, dds_contract, owner_acc, moderator_acc, = contract_factory

    await dds_contract.set_prices(multiplied_prices).invoke()

    res = await dds_contract.read_price(7).call()

    print(res.result.price.low / math.pow(10, 8))


@ pytest.mark.asyncio
async def test_simple_getters(contract_factory):
    _, dds_contract, dag_contract, owner_acc = contract_factory

    await dds_contract.set_prices(list(asset_prices_indexes.values()), multiplied_prices).invoke()

    await dds_contract.set_decimals(8).invoke()

    res1 = await dds_contract.get_decimals().call()
    res2 = await dds_contract.get_timestamp().call()
    res3 = await dds_contract.get_round().call()

    assert res1.result.decimals == 8
    print(res2.result.timestamp)
    print(res3.result.roundId)

    print("test_get_infos: PASSED")


@ pytest.mark.asyncio
async def test_aggregated_round_data(contract_factory):
    starknet, dds_contract, dag_contract, owner_acc = contract_factory

    await dds_contract.set_prices(list(asset_prices_indexes.values()), multiplied_prices).invoke()

    res = await dag_contract.aggregated_round_data().call()

    for i in range(len(res.result.a)):
        diff = res.result.a[i].answer.low / \
            math.pow(10, 8) - round(list(asset_prices.values())[i], 8)
        assert abs(diff) < 2*math.pow(10, -8)

    print("test_aggregated_round_data: PASSED")
