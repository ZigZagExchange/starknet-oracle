import math
import pytest
import asyncio

from starkware.starknet.testing.starknet import Starknet
from starkware.starknet.testing.contract import StarknetContract

from utils import Signer

owner = Signer(111111111111111111111)

signer = Signer(123456789987654321)
other = Signer(987654321123456789)


acc_path = "contracts/OpenZepplin/contracts/Account.cairo"

address = "1769AF734428832E5658F74187FAF455131785C5692CD1FE7877E406B6E04E4"

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


@pytest.fixture(scope='module')
def event_loop():
    return asyncio.new_event_loop()


@pytest.fixture(scope='module')
async def contract_factory():
    starknet = await Starknet.empty()

    contract = await starknet.deploy(
        "contracts/test_contracts/contract.cairo",
    )

    owner_acc = await starknet.deploy(
        acc_path,
        constructor_calldata=[owner.public_key]
    )

    return starknet, contract, owner_acc


@pytest.mark.asyncio
async def test_main_logic(contract_factory):
    starknet, contract, owner_acc = contract_factory

    c1 = await contract.read_logged_address().call()
    print("\n", c1.result)

    await owner.send_transaction(
        account=owner_acc,
        to=contract.contract_address,
        selector_name='log_address',
        calldata=[])

    c2 = await contract.read_logged_address().call()
    print("\n", c2.result)

    print("\n", owner_acc.contract_address)


@pytest.mark.asyncio
async def test_access(contract_factory):
    starknet, contract, owner_acc = contract_factory

    c1 = await contract.set_owner(owner_acc.contract_address).invoke()
    # print("\n", c1.result)

    await owner.send_transaction(
        account=owner_acc,
        to=contract.contract_address,
        selector_name='test_access',
        calldata=[])

    c2 = await contract.test_access_func().call()
    print(c2.result)
