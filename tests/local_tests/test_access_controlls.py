import pytest
import asyncio

from starkware.starknet.testing.starknet import Starknet
from starkware.starknet.testing.contract import StarknetContract

from utils import Signer


owner = Signer(111111111111111111111)
moderator = Signer(222222222222222222222)
external_oracle = Signer(333333333333333333333)

new_owner = Signer(444444444444444444444)
new_moderator = Signer(555555555555555555555)
new_external_oracle = Signer(666666666666666666666)

# Enables modules.
acc_path = "contracts/OpenZepplin/contracts/Account.cairo"


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

    act_contract = await starknet.deploy(
        "contracts/test_contracts/AccessControllTests.cairo",
        constructor_calldata=[
            owner_acc.contract_address,
            moderator_acc.contract_address,
            external_oracle_acc.contract_address,
        ]
    )

    return starknet, act_contract, owner_acc, moderator_acc, external_oracle_acc


@pytest.mark.asyncio
async def test_main_logic(contract_factory):
    print("test_main_logic")
    # await access_controlls_initilization_test(contract_factory)
    # await access_controlls_test(contract_factory)
    # await transfer_ownership_test(contract_factory)
    # await change_access_controlls_test(contract_factory)


@pytest.mark.asyncio
async def test_access_controlls_initilization(contract_factory):
    _, act_contract, owner_acc, moderator_acc, external_oracle_acc = contract_factory

    res = await act_contract.read_access_controll_addresses().call()

    o = res.result.owner_address
    m = res.result.moderator_address
    eo = res.result.external_oracle_address

    assert o == owner_acc.contract_address
    assert m == moderator_acc.contract_address
    assert eo == external_oracle_acc.contract_address

    print("\n access_controlls_initilization_test: PASSED")


@pytest.mark.asyncio
async def test_access_controlls(contract_factory):
    _, act_contract, owner_acc, moderator_acc, external_oracle_acc = contract_factory

    await owner.send_transaction(
        account=owner_acc,
        to=act_contract.contract_address,
        selector_name='check_only_owner',
        calldata=[])

    await owner.send_transaction(
        account=owner_acc,
        to=act_contract.contract_address,
        selector_name='check_only_owner_or_moderator',
        calldata=[])

    await moderator.send_transaction(
        account=moderator_acc,
        to=act_contract.contract_address,
        selector_name='check_only_owner_or_moderator',
        calldata=[])

    await external_oracle.send_transaction(
        account=external_oracle_acc,
        to=act_contract.contract_address,
        selector_name='check_only_external_oracle',
        calldata=[])

    # Anything else would fail -> only these accounts can trigger these functions.

    print("\n access_controlls_test: PASSED")


@pytest.mark.asyncio
async def test_transfer_ownership(contract_factory):
    starknet, act_contract, owner_acc, _, _ = contract_factory

    new_owner_acc = await starknet.deploy(
        acc_path,
        constructor_calldata=[new_owner.public_key]
    )

    res = await owner.send_transaction(
        account=owner_acc,
        to=act_contract.contract_address,
        selector_name='test_transfer_ownership',
        calldata=[new_owner_acc.contract_address])

    assert res.result.response[0] == owner_acc.contract_address
    assert res.result.response[1] == new_owner_acc.contract_address

    print("\n transfer_ownership_test: PASSED")


@pytest.mark.asyncio
async def test_change_access_controlls(contract_factory):
    starknet, act_contract, owner_acc, _, _ = contract_factory

    new_moderator_acc = await starknet.deploy(
        acc_path,
        constructor_calldata=[new_moderator.public_key]
    )
    new_external_oracle_acc = await starknet.deploy(
        acc_path,
        constructor_calldata=[new_external_oracle.public_key]
    )

    res1 = await act_contract.read_access_controll_addresses().call()

    #o1 = res1.result.owner_address
    m1 = res1.result.moderator_address
    eo1 = res1.result.external_oracle_address

    res2 = await owner.send_transaction(
        account=owner_acc,
        to=act_contract.contract_address,
        selector_name='change_access_controlls',
        calldata=[new_moderator_acc.contract_address,
                  new_external_oracle_acc.contract_address])

    res3 = await act_contract.read_access_controll_addresses().call()

    #o2 = res3.result.owner_address
    m2 = res3.result.moderator_address
    eo2 = res3.result.external_oracle_address

    assert m2 == new_moderator_acc.contract_address
    assert eo2 == new_external_oracle_acc.contract_address

    assert res2.raw_events[0].from_address == act_contract.contract_address
    assert res2.raw_events[0].data[0] == m1
    assert res2.raw_events[0].data[1] == m2

    assert res2.raw_events[1].from_address == act_contract.contract_address
    assert res2.raw_events[1].data[0] == eo1
    assert res2.raw_events[1].data[1] == eo2

    print("\n change_access_controlls_test: PASSED")
