import pytest
import asyncio

from starkware.starknet.testing.starknet import Starknet
from starkware.starknet.testing.contract import StarknetContract

from utils import Signer


owner = Signer(111111111111111111111)
moderator = Signer(222222222222222222222)
external_oracle = Signer(333333333333333333333)

# Enables modules.
acc_path = "contracts/Accounts/account.cairo"


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

    aggregator = await starknet.deploy(
        "tests/contracts/Aggregator.cairo",
    )

    apt_contract = await starknet.deploy(
        "tests/contracts/AggregatorProxyTests.cairo",
        constructor_calldata=[
            owner_acc.contract_address,
            moderator_acc.contract_address,
            external_oracle_acc.contract_address,
            aggregator.contract_address,
        ]
    )

    return starknet, apt_contract, aggregator, owner_acc, moderator_acc,


@pytest.mark.asyncio
async def test_main_logic(contract_factory):
    starknet, apt_contract, aggregator, owner_acc, moderator_acc, = contract_factory

    new_aggregator = await starknet.deploy(
        "tests/contracts/Aggregator.cairo",
    )

    res = await apt_contract.get_aggregator_address().call()
    assert res.result.aggregator_address == aggregator.contract_address

    propose_res = await moderator.send_transaction(
        account=moderator_acc,
        to=apt_contract.contract_address,
        selector_name='test_propose_new_aggregator',
        calldata=[new_aggregator.contract_address])

    res = await apt_contract.get_proposed_agregator_address().call()
    assert res.result.aggregator_address == new_aggregator.contract_address

    confirm_res = await owner.send_transaction(
        account=owner_acc,
        to=apt_contract.contract_address,
        selector_name='test_confirm_new_aggregator',
        calldata=[new_aggregator.contract_address])

    res = await apt_contract.get_aggregator_address().call()
    assert res.result.aggregator_address == new_aggregator.contract_address

    propose_res_events = propose_res.raw_events[0].data
    confirm_res_events = confirm_res.raw_events[0].data

    assert propose_res_events[0] == aggregator.contract_address
    assert propose_res_events[1] == new_aggregator.contract_address
    assert propose_res_events[2] == moderator_acc.contract_address

    assert confirm_res_events[0] == aggregator.contract_address
    assert confirm_res_events[1] == new_aggregator.contract_address

    print("Propose_Confirm_new_aggregator_test: PASSED")


@pytest.mark.asyncio
async def test_aggregator_initilization(contract_factory):
    _, apt_contract, aggregator, owner_acc, moderator_acc, = contract_factory

    res = await apt_contract.get_aggregator_address().call()

    assert res.result.aggregator_address == aggregator.contract_address

    print("Aggregator_initilization_test: PASSED")


@pytest.mark.asyncio
async def test_aggregator_simple_functions(contract_factory):
    _, apt_contract, aggregator, owner_acc, moderator_acc, = contract_factory

    latest_answer = await apt_contract.test_latest_answer().call()
    latest_timestamp = await apt_contract.test_latest_timestamp().call()
    latest_round = await apt_contract.test_latest_round().call()
    decimals = await apt_contract.decimals().call()

    assert latest_answer.result.answer == 324741000000
    assert latest_timestamp.result.timestamp == 1644490567
    assert latest_round.result.roundId == 92233720368547777169
    assert decimals.result.decimals == 8

    print("Aggregator_simple_functions: PASSED")


@pytest.mark.asyncio
async def test_aggregator_other_functions(contract_factory):
    _, apt_contract, aggregator, owner_acc, moderator_acc, = contract_factory

    res1 = await apt_contract.test_get_round_data(1).call()
    res2 = await apt_contract.test_latest_round_data().call()

    print("\n" + res1.result.response)
    print(res2.result.response)

    print("Aggregator_other_functions: PASSED")


@pytest.mark.asyncio
async def test_propose_confirm_new_aggregator(contract_factory):
    starknet, apt_contract, aggregator, owner_acc, moderator_acc, = contract_factory

    new_aggregator = await starknet.deploy(
        "tests/contracts/Aggregator.cairo",
    )

    res = await apt_contract.get_aggregator_address().call()
    assert res.result.aggregator_address == aggregator.contract_address

    propose_res = await moderator.send_transaction(
        account=moderator_acc,
        to=apt_contract.contract_address,
        selector_name='test_propose_new_aggregator',
        calldata=[new_aggregator.contract_address])

    res = await apt_contract.get_proposed_agregator_address().call()
    assert res.result.aggregator_address == new_aggregator.contract_address

    confirm_res = await owner.send_transaction(
        account=owner_acc,
        to=apt_contract.contract_address,
        selector_name='test_confirm_new_aggregator',
        calldata=[new_aggregator.contract_address])

    res = await apt_contract.get_aggregator_address().call()
    assert res.result.aggregator_address == new_aggregator.contract_address

    propose_res_events = propose_res.raw_events[0].data
    confirm_res_events = confirm_res.raw_events[0].data

    assert propose_res_events[0] == aggregator.contract_address
    assert propose_res_events[1] == new_aggregator.contract_address
    assert propose_res_events[2] == moderator_acc.contract_address

    assert confirm_res_events[0] == aggregator.contract_address
    assert confirm_res_events[1] == new_aggregator.contract_address

    print("propose_confirm_new_aggregator_test: PASSED")
