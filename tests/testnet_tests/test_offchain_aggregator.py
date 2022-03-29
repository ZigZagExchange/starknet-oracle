import ast
import os
import time

import pytest
import asyncio
from pathlib import Path
import json

from dataclasses import dataclass
from decouple import config
from Transmitter import Transmitter

from starkware.crypto.signature.signature import private_to_stark_key, get_random_private_key
from starkware.starknet.public.abi import get_selector_from_name, get_storage_var_address


from starknet_py.net.client import Client
from starknet_py.net.account.account_client import AccountClient, KeyPair
from starknet_py.contract import Contract


abis_path = os.path.join(
    os.path.normpath(os.getcwd() + os.sep + os.pardir + os.sep + os.pardir),
    "artifacts/abis/")

OWNER_PRIV_KEY = int(config('OWNER_PRIV_KEY'))
TRANSMITTER_PRIV_KEY = int(config('TRANSMITTER_PRIV_KEY'))


account_abi = Path(os.path.join(abis_path, "Account.json")).read_text()
account_abi = ast.literal_eval(account_abi)

transmitter_abi = Path(os.path.join(abis_path, "Transmitter.json")).read_text()
transmitter_abi = ast.literal_eval(transmitter_abi)

main_oracle_abi = Path(os.path.join(abis_path, "MainOracle.json")).read_text()
print("main_oracle_abi: ", main_oracle_abi)
# main_oracle_abi = ast.literal_eval(main_oracle_abi)

ofc_aggregator_abi = Path(os.path.join(
    abis_path, "OffchainAggregator.json")).read_text()
ofc_aggregator_abi = ast.literal_eval(ofc_aggregator_abi)


owner_addr = "0x05e8e3ffb034bb955aa73bc58d47f8126e9664c5398d0307fbd6dc54f10d867c"
transmitter_addr = "0x0385eb396a9f04e0c4364c540727831935201893e60d982a6203947f30803d17"

ofc_aggregator_addr = "0x06da2ddb9ae628cd405c5050466ae70abb36a1071fdc00987c9b19a19bc471de"
main_oracle_addr = "0x73033b822f094e4ea7e6ccef82254c819224e8d65f660f108da844956d463d3"

# transmitter = Transmitter(TRANSMITTER_PRIV_KEY)
transmitter = Transmitter(
    369845423575795833804508439466765636244729169355142507531150208559352357013)
# ...............................................................................
file_path = os.path.join(
    os.path.normpath(os.getcwd() + os.sep + os.pardir + os.sep + os.pardir),
    "tests/dummy_data/dummy_calldata.json")
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
# ...............................................................................


@dataclass
class KeyPair:
    private_key: int
    public_key: int

    @staticmethod
    def from_private_key(key: int) -> "KeyPair":
        return KeyPair(private_key=key, public_key=private_to_stark_key(key))
# ...............................................................................


@pytest.fixture(scope='module')
def event_loop():
    return asyncio.new_event_loop()


@pytest.fixture(scope='module')
async def contract_factory():

    owner_key_pair = KeyPair.from_private_key(OWNER_PRIV_KEY)

    owner_client = AccountClient(
        owner_addr, owner_key_pair, "testnet")

    local_network_client = Client("testnet")

    transmitter_acc = Contract(address=transmitter_addr, abi=transmitter_abi,
                               client=local_network_client)

    main_oracle = Contract(address=main_oracle_addr, abi=main_oracle_abi,
                           client=local_network_client)

    ofc_aggregator = Contract(address=ofc_aggregator_addr, abi=ofc_aggregator_abi,
                              client=local_network_client)

    return owner_client, main_oracle, transmitter_acc, ofc_aggregator


@pytest.mark.asyncio
async def test_main_logic(contract_factory):
    owner_client, main_oracle, transmitter_acc, ofc_aggregator = contract_factory

    start = time.time()
    print("start: ", start)
    res = await ofc_aggregator.functions["latestRoundData"].call()
    end = time.time()
    print("end: ", end)
    print("time: ", end - start)
    print(res)


@pytest.mark.asyncio
async def test_set_config(contract_factory):
    owner_client, main_oracle, transmitter_acc, ofc_aggregator = contract_factory

    encoded_config = 1234567898765

    invocation = await ofc_aggregator.functions["set_config"].invoke(
        signer_pub_keys,
        [int(transmitter_addr, 16)] + transmitter_pub_keys[1:],
        10, 1, encoded_config)

    res = await invocation.wait_for_acceptance()

    # print([int(transmitter_addr, 16)] + transmitter_pub_keys[1:])

    print(res)


@pytest.mark.asyncio
async def test_get_config(contract_factory):
    owner_client, main_oracle, transmitter_acc, ofc_aggregator = contract_factory

    res = await ofc_aggregator.functions["transmitters"].call()

    print(res)


@pytest.mark.asyncio
async def test_transmit(contract_factory):
    owner_client, main_oracle, transmitter_acc, ofc_aggregator = contract_factory

    # encoded_config = 12345678987654321

    # invocation = await ofc_aggregator.functions["set_config"].invoke(
    #     signer_pub_keys,
    #     [int(transmitter_addr, 16)] + transmitter_pub_keys[1:],
    #     10, 1, encoded_config)

    # res1 = await invocation.wait_for_acceptance()
    # print(res1)
    # print("\n =====================================================")

    calldata = [int(rawReportContext, 16),
                int(rawObservers[:60], 16),
                observations1,
                r_sigs1,
                s_sigs1,
                "0x" + "00" * 32]

    invocation = await transmitter.send_transaction(
        account=transmitter_acc,
        to=ofc_aggregator.address,
        selector_name='transmit',
        calldata=calldata)

    res2 = await invocation.wait_for_acceptance()

    print(res2)
