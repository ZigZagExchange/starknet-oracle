import math
import pytest
import asyncio
import json

from starkware.starknet.testing.starknet import Starknet
from starkware.crypto.signature.signature import (
    pedersen_hash, private_to_stark_key, sign, get_random_private_key)
from utils import Signer

owner = Signer(111111111111111111111)

acc_path = "contracts/OpenZepplin/contracts/Account.cairo"
# ============   ============   ============   ==============
file_path = "tests/dummy_data/dummy_calldata.json"
f = open(file_path, 'r')
calldata = json.load(f)
f.close()

msg_hash = calldata["cairo-calldata"]["msg_hash"]
rawReportContext = calldata["cairo-calldata"]["rawReportContext"]
rawObservers = calldata["cairo-calldata"]["rawObservers"]
r_sigs = calldata["cairo-calldata"]["r_sigs"]
s_sigs = calldata["cairo-calldata"]["s_sigs"]
public_keys = calldata["cairo-calldata"]["public_keys"]
observations = calldata["cairo-calldata"]["observations"]
# ============   ============   ============   ==============


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

    arr = [1, 3, 5, 6, 7, 8, 9, 13]
    res = await contract.assert_array_sorted(arr).call()

    print(res.result)


@pytest.mark.asyncio
async def test_verify_all_signatures(contract_factory):
    starknet, contract, owner_acc = contract_factory

    await contract.test_verify_all_sigs(
        int(rawReportContext, 16),
        (int(rawObservers[:32], 16),
         int(rawObservers[32:], 16)),
        observations,
        r_sigs,
        s_sigs,
        public_keys,
    ).call()

    print("test_verify_all_signatures: PASSED")


@pytest.mark.asyncio
async def test_signatures(contract_factory):
    starknet, contract, owner_acc = contract_factory

    for i in range(len(r_sigs)):
        await contract.test_verify_sig(
            msg_hash,
            (r_sigs[i], s_sigs[i]),
            public_keys[i]
        ).call()

    print("All signatures are valid")


@pytest.mark.asyncio
async def test_make_hex_array(contract_factory):
    starknet, contract, owner_acc = contract_factory
