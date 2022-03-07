import math
import pytest
import asyncio
from dataclasses import dataclass


from starkware.starknet.testing.starknet import Starknet
from starkware.starknet.testing.contract import StarknetContract
from starkware.crypto.signature.signature import (
    pedersen_hash, private_to_stark_key, sign)
from starkware.cairo.common.cairo_secp.secp_utils import pack

from utils import Signer

owner = Signer(111111111111111111111)

signer = Signer(123456789987654321)
other = Signer(987654321123456789)


acc_path = "contracts/OpenZepplin/contracts/Account.cairo"


@dataclass
class BigInt3:
    d0: int
    d1: int
    d2: int


@pytest.fixture(scope='module')
def event_loop():
    return asyncio.new_event_loop()


@pytest.fixture(scope='module')
async def contract_factory():
    starknet = await Starknet.empty()

    ecdsa_contracts = await starknet.deploy(
        "contracts/test_contracts/ecdsa_tests.cairo",
    )

    # owner_acc = await starknet.deploy(
    #     acc_path,
    #     constructor_calldata=[owner.public_key]
    # )

    return starknet, ecdsa_contracts


@pytest.mark.asyncio
async def test_main_logic(contract_factory):
    starknet, ecdsa_contracts = contract_factory

    x = BigInt3(d0=1, d1=2, d2=3)
    P = 2 ** 251 + 17 * 2 ** 192 + 1
    num = pack(x, P)
    print(num)

    x1 = (1, 2, 3)

    res = await ecdsa_contracts.pack(x1, P//2).call()
    print(res.result.res)
