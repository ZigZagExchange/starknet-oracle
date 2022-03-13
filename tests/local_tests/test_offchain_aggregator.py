from copyreg import constructor
import math
import random
import pytest
import asyncio
import json

from starkware.starknet.testing.starknet import Starknet
from starkware.cairo.common.hash_state import compute_hash_on_elements

from utils import Signer, Transmitter


# ============   ============   ============   ==============   ==============
file_path = "tests/dummy_data/dummy_calldata.json"
f = open(file_path, 'r')
calldata = json.load(f)
f.close()

rawReportContext = calldata["cairo-calldata"]["rawReportContext"]
rawObservers = calldata["cairo-calldata"]["rawObservers"]
signer_pub_keys = calldata["cairo-calldata"]["signer_public_keys"]
transmitter_pub_keys = calldata["cairo-calldata"]["transmitter_public_keys"]
transmitter_priv_keys = calldata["cairo-calldata"]["transmitter_private_keys"]

r_sigs1 = calldata["cairo-calldata"]["calldata1"]["r_sigs"]
s_sigs1 = calldata["cairo-calldata"]["calldata1"]["s_sigs"]
observations1 = calldata["cairo-calldata"]["calldata1"]["observations"]

r_sigs2 = calldata["cairo-calldata"]["calldata2"]["r_sigs"]
s_sigs2 = calldata["cairo-calldata"]["calldata2"]["s_sigs"]
observations2 = calldata["cairo-calldata"]["calldata2"]["observations"]

r_sigs3 = calldata["cairo-calldata"]["calldata3"]["r_sigs"]
s_sigs3 = calldata["cairo-calldata"]["calldata3"]["s_sigs"]
observations3 = calldata["cairo-calldata"]["calldata3"]["observations"]
# ============   ============   ============   ==============   ==============

owner = Signer(111111111111111111111)
transmitter = Transmitter(transmitter_priv_keys[0])
transmitter2 = Transmitter(transmitter_priv_keys[1])
transmitter3 = Transmitter(transmitter_priv_keys[2])


signers2 = [x*2//3 for x in signer_pub_keys]
transmitters2 = [x*2//3 for x in transmitter_pub_keys]

acc_path = "contracts/Accounts/Account.cairo"
transmitter_path = "contracts/Accounts/Transmitter.cairo"
ofc_agg_path = "contracts/OffchainAggregator/OffchainAggregator.cairo"


ETHUSD_hex = 0x4554482f555344
BNBUSD_hex = 0x424e422f555344
LUNAUSD_hex = 0x4c554e412f555344


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

    ofc_agg_contract = await starknet.deploy(
        ofc_agg_path,
        constructor_calldata=[10**8, 10**11, 8,
                              owner_acc.contract_address, ETHUSD_hex]
    )

    transmitter_acc = await starknet.deploy(
        transmitter_path,
        constructor_calldata=[transmitter_pub_keys[0]]
    )

    encoded_config = 12345678987654321
    await ofc_agg_contract.set_config(
        signer_pub_keys,
        [transmitter_acc.contract_address] + transmitter_pub_keys[1:],
        10, 1, encoded_config).invoke()

    return starknet, ofc_agg_contract, transmitter_acc, owner_acc


@pytest.mark.asyncio
async def test_main_logic(contract_factory):
    starknet, ofc_agg_contract, transmitter_acc, owner_acc = contract_factory


@pytest.mark.asyncio
async def test_transmit(contract_factory):
    starknet, ofc_agg_contract, transmitter_acc, owner_acc = contract_factory

    calldata = [int(rawReportContext, 16),
                int(rawObservers[:60], 16),
                observations1,
                r_sigs1,
                s_sigs1,
                signer_pub_keys]

    res = await transmitter.send_transaction(
        account=transmitter_acc,
        to=ofc_agg_contract.contract_address,
        selector_name='transmit',
        calldata=calldata)

    # calldata_list = [int(rawReportContext, 16), int(
    #     rawObservers[:60], 16)] + observations1

    # h = compute_hash_on_elements(calldata_list)

    # print("hash: ", h)
    print("\n", res.result)


@ pytest.mark.asyncio
async def test_ofc_getters(contract_factory):
    starknet, ofc_agg_contract, transmitter_acc, owner_acc = contract_factory

    res = await ofc_agg_contract.latestRound().call()
    res2 = await ofc_agg_contract.latestAnswer().call()

    print("\n", res.result)
    print("\n", res2.result)


@pytest.mark.asyncio
async def test_set_config_signers_transmitters(contract_factory):
    starknet, ofc_agg_contract, transmitter_acc, owner_acc = contract_factory

    for i in range(len(signer_pub_keys)):
        s = await ofc_agg_contract.get_signer(i).call()
        t = await ofc_agg_contract.get_transmitter(i).call()
        assert s.result.signer == signer_pub_keys[len(signer_pub_keys) - i-1]
        assert t.result.transmitter == transmitter_pub_keys[len(
            signer_pub_keys) - i-1]

    encoded_config = 12345678987654321
    await ofc_agg_contract.set_config(
        signers2, transmitters2, 10, 2, encoded_config).invoke()
    for i in range(len(signer_pub_keys)):
        s = await ofc_agg_contract.get_signer(i).call()
        t = await ofc_agg_contract.get_transmitter(i).call()
        assert s.result.signer == signers2[len(signer_pub_keys) - i-1]
        assert t.result.transmitter == transmitters2[len(
            signer_pub_keys) - i-1]

    print("\n", "test_set_config_singers_transmitters: PASSED")


@ pytest.mark.asyncio
async def test_set_config(contract_factory):
    starknet, ofc_agg_contract, transmitter_acc, owner_acc = contract_factory

    encoded_config = 12345678987654321
    res = await ofc_agg_contract.set_config(
        signer_pub_keys,
        [transmitter_acc.contract_address] + transmitter_pub_keys[1:],
        10, 1, encoded_config).invoke()

    # ..................................................

    elements = [ofc_agg_contract.contract_address, 1] + signer_pub_keys + \
        [transmitter_acc.contract_address] + \
        transmitter_pub_keys[1:] + [10, 1, encoded_config]

    h = compute_hash_on_elements(elements)
    _, digest = divmod(h, 2**128)

    print("\n", res.result)
    print("\n", digest)


@ pytest.mark.asyncio
async def test_config_digest_from_data(contract_factory):
    starknet, ofc_agg_contract, transmitter_acc, owner_acc = contract_factory

    res = await ofc_agg_contract.config_digest_from_config_data(
        12892353439029830121023, 3, signer_pub_keys, transmitter_pub_keys, 8,
        12092395732124367332797023, 129728432856372493286482).call()

    print(res.result.digest)
    print("test_config_digest_from_data: PASSED")


@ pytest.mark.asyncio
async def test_main_oracle(contract_factory):
    starknet, ofc_agg_contract, transmitter_acc, owner_acc = contract_factory

    main_oracle = await starknet.deploy(
        "contracts/MainOracle.cairo",
        constructor_calldata=[
            owner_acc.contract_address,
            ofc_agg_contract.contract_address,
        ]
    )

    calldata = [int(rawReportContext, 16),
                int(rawObservers[:60], 16),
                observations1,
                r_sigs1,
                s_sigs1,
                signer_pub_keys]

    await transmitter.send_transaction(
        account=transmitter_acc,
        to=ofc_agg_contract.contract_address,
        selector_name='transmit',
        calldata=calldata)

    latestTransmissionDetails = await main_oracle.latestTransmissionDetails().call()
    transmitters = await main_oracle.transmitters().call()
    latestAnswer = await main_oracle.latestAnswer().call()
    latestTimestamp = await main_oracle.latestTimestamp().call()
    latestRound = await main_oracle.latestRound().call()
    getAnswer = await main_oracle.getAnswer(1).call()
    getTimestamp = await main_oracle.getTimestamp(1).call()
    round_data = await main_oracle.getRoundData(1).call()
    getRoundData = await main_oracle.getRoundData(1).call()
    latestRoundData = await main_oracle.latestRoundData().call()
    description = await main_oracle.description().call()
    decimals = await main_oracle.decimals().call()

    print("latestTransmissionDetails: ", latestTransmissionDetails.result)
    print("transmitters: ", transmitters.result)
    print("latestAnswer: ", latestAnswer.result.res)
    print("latestTimestamp: ", latestTimestamp.result.res)
    print("latestRound: ", latestRound.result.res)
    print("getAnswer: ", getAnswer.result.res)
    print("getTimestamp: ", getTimestamp.result.res)
    print("round_data: ", round_data.result.res)
    print("getRoundData: ", getRoundData.result.res)
    print("latestRoundData: ", latestRoundData.result.res)
    print("description: ", description.result.res)
    print("decimals: ", decimals.result.decimals)
    print("test_main_oracle: PASSED")


@pytest.mark.asyncio
async def test_transmit_multiple(contract_factory):
    starknet, eth_agg_contract, transmitter_acc, owner_acc = contract_factory

    bnb_agg_contract = await starknet.deploy(
        ofc_agg_path,
        constructor_calldata=[10**7, 10**10, 8,
                              owner_acc.contract_address, BNBUSD_hex]
    )
    luna_agg_contract = await starknet.deploy(
        ofc_agg_path,
        constructor_calldata=[10**6, 10**10, 8,
                              owner_acc.contract_address, LUNAUSD_hex]
    )

    encoded_config = 12345678987654321
    await bnb_agg_contract.set_config(
        signer_pub_keys,
        [transmitter_acc.contract_address] + transmitter_pub_keys[1:],
        10, 1, encoded_config+1).invoke()
    encoded_config = 12345678987654321
    await luna_agg_contract.set_config(
        signer_pub_keys,
        [transmitter_acc.contract_address] + transmitter_pub_keys[1:],
        10, 1, encoded_config+2).invoke()

    calldata1 = [int(rawReportContext, 16),
                 int(rawObservers[:60], 16),
                 observations1,
                 r_sigs1,
                 s_sigs1,
                 signer_pub_keys]

    calldata2 = [int(rawReportContext, 16),
                 int(rawObservers[:60], 16),
                 observations2,
                 r_sigs2,
                 s_sigs2,
                 signer_pub_keys]

    calldata3 = [int(rawReportContext, 16),
                 int(rawObservers[:60], 16),
                 observations3,
                 r_sigs3,
                 s_sigs3,
                 signer_pub_keys]

    res1 = await transmitter.send_transaction(
        account=transmitter_acc,
        to=eth_agg_contract.contract_address,
        selector_name='transmit',
        calldata=calldata1)

    res2 = await transmitter.send_transaction(
        account=transmitter_acc,
        to=bnb_agg_contract.contract_address,
        selector_name='transmit',
        calldata=calldata2)

    res3 = await transmitter.send_transaction(
        account=transmitter_acc,
        to=luna_agg_contract.contract_address,
        selector_name='transmit',
        calldata=calldata3)

    latestTransmissionDetails = await eth_agg_contract.latestTransmissionDetails().call()
    latestTransmissionDetails2 = await bnb_agg_contract.latestTransmissionDetails().call()
    latestTransmissionDetails3 = await luna_agg_contract.latestTransmissionDetails().call()

    print("\n EthUsd", latestTransmissionDetails.result)
    print("\n BnbUsd", latestTransmissionDetails2.result)
    print("\n LunaUsd", latestTransmissionDetails3.result)


@ pytest.mark.asyncio
async def test_change_aggregator(contract_factory):
    starknet, ofc_agg_contract, transmitter_acc, owner_acc = contract_factory

    main_oracle = await starknet.deploy(
        "contracts/MainOracle.cairo",
        constructor_calldata=[
            owner_acc.contract_address,
            ofc_agg_contract.contract_address,
        ]
    )
    agg1 = await main_oracle.get_aggregator().call()
    prop_agg1 = await main_oracle.get_proposed_aggregator().call()
    # .................................................................
    await owner.send_transaction(
        account=owner_acc,
        to=main_oracle.contract_address,
        selector_name='propose_new_aggregator',
        calldata=[ofc_agg_contract.contract_address//2])

    agg2 = await main_oracle.get_aggregator().call()
    prop_agg2 = await main_oracle.get_proposed_aggregator().call()
    # .................................................................
    await owner.send_transaction(
        account=owner_acc,
        to=main_oracle.contract_address,
        selector_name='confirm_new_aggregator',
        calldata=[ofc_agg_contract.contract_address//2])
    agg3 = await main_oracle.get_aggregator().call()
    prop_agg3 = await main_oracle.get_proposed_aggregator().call()

    assert agg1.result.aggregator_address == ofc_agg_contract.contract_address
    assert prop_agg1.result.aggregator_address == 0

    assert agg2.result.aggregator_address == ofc_agg_contract.contract_address
    assert prop_agg2.result.aggregator_address == ofc_agg_contract.contract_address//2

    assert agg3.result.aggregator_address == ofc_agg_contract.contract_address//2
    assert prop_agg3.result.aggregator_address == 0

    print("test_change_aggregator: PASSED")
