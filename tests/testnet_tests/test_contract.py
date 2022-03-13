import ast

from sqlalchemy import true

import pytest
import asyncio
from pathlib import Path

from dataclasses import dataclass
from decouple import config

from starknet_py.contract import Contract
from starknet_py.net.client import Client
from starknet_py.net.account.account_client import AccountClient, KeyPair
from starkware.crypto.signature.signature import private_to_stark_key
from starkware.starknet.public.abi import get_selector_from_name
from starknet_py.net.models import InvokeFunction


OWNER_PRIV_KEY = int(config('OWNER_PRIV_KEY'))

compiled = Path("artifacts/contract.json").read_text()
abi = Path("artifacts/abis/contract.json").read_text()
abi = ast.literal_eval(abi)

account_abi = Path("artifacts/abis/Account.json").read_text()
account_abi = ast.literal_eval(account_abi)


contract_addr = "0x007487610b29fa703a009b439607b4441d3a5fce4b888beae9bfe8427b8fc612"
owner_addr = "0x05e8e3ffb034bb955aa73bc58d47f8126e9664c5398d0307fbd6dc54f10d867c"


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

    owner_key_pair = KeyPair.from_private_key(OWNER_PRIV_KEY)

    local_network_client = Client("testnet")

    # account_client = AccountClient(owner_addr, owner_key_pair, "testnet")

    owner_acc = Contract(address=owner_addr, abi=account_abi,
                         client=local_network_client)

    contract = Contract(address=contract_addr, abi=abi,
                        client=local_network_client)

    return contract, owner_acc, local_network_client


@pytest.mark.asyncio
async def test_main_logic(contract_factory):
    contract, owner_acc, client = contract_factory

    prepared = contract.functions["test_hexes"].prepare()
    invocation = await prepared.invoke(signature=[12345, 67890])

    print(invocation)
    # res = await client.add_transaction(
    #     InvokeFunction(
    #         entry_point_selector=get_selector_from_name("test_signatures"),
    #         calldata=[],
    #         contract_address=contract.address,
    #         signature=[1234567, 3456789],
    #     )
    # )

    # res1 = await client.wait_for_tx(res["transaction_hash"], True)

    # print(res)
