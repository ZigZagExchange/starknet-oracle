import ast
import math

from sqlalchemy import null
import pytest
import asyncio
from pathlib import Path

from dataclasses import dataclass
from decouple import config

from starknet_py.net.models import StarknetChainId, InvokeFunction
from starknet_py.contract import Contract
from starknet_py.net.client import Client
from starknet_py.net.account.account_client import AccountClient, KeyPair
from starknet_py.net.models.address import AddressRepresentation
from starkware.starknet.public.abi import get_selector_from_name
from starkware.crypto.signature.signature import private_to_stark_key, get_random_private_key


OWNER_PRIV_KEY = int(config('OWNER_PRIV_KEY'))

compiled = Path("artifacts/contract.json").read_text()
abi = Path("artifacts/abis/contract.json").read_text()
abi = ast.literal_eval(abi)

account_abi = Path("artifacts/abis/Account.json").read_text()
account_abi = ast.literal_eval(account_abi)


contract_addr = "0x06278eed365762a19fd91fa70765a94975b0855e326c3abc0ae8066e46cb46a5"
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

    account_client = AccountClient(owner_addr, owner_key_pair, "testnet")

    owner_acc = Contract(address=owner_addr, abi=account_abi,
                         client=local_network_client)

    contract = Contract(address=contract_addr, abi=abi,
                        client=local_network_client)

    return contract, owner_acc, account_client


@pytest.mark.asyncio
async def test_main_logic(contract_factory):
    contract, owner_acc, account_client = contract_factory

    # int_addrs = int(owner_addr, 16)
    # invocation = await contract.functions["set_owner"].invoke(int_addrs)

    # res1 = await invocation.wait_for_acceptance()
    # print(res1, "\n")

    int_addr = int(contract_addr, 16)
    int_selector = get_selector_from_name("test_access")

    calldata = []
    signature = []

    inp = InvokeFunction(int_addr, int_selector, calldata, signature)
    res1 = await account_client.add_transaction(inp)

    print(res1)
    # res = await contract.functions["test_access_func"].call()
    # print(res)
    #
    #
    #
    #
    #
    #
    #
    # contract, owner_acc, account_client = contract_factory

    # nonce = await owner_acc.functions["get_nonce"].call()

    # int_to = int(contract_addr, 16)
    # int_selector = get_selector_from_name("log_address")
    # # calldata = null
    # # nonce = nonce

    # invocation = await owner_acc.functions["execute"].invoke(int_to, "log_address", [], nonce.res)

    # res1 = await invocation.wait_for_acceptance()
    # print(res1, "\n")

    # res2 = await contract.functions["read_logged_address"].call()
    # print(res2)
