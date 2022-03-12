import math
import pytest
import asyncio
import json

from starkware.starknet.testing.starknet import Starknet
from starkware.crypto.signature.signature import (
    pedersen_hash, private_to_stark_key, sign, get_random_private_key)
from utils import Signer

owner = Signer(111111111111111111111)

acc_path = "contracts/Accounts/account.cairo"
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
signer_pub_keys = calldata["cairo-calldata"]["signer_public_keys"]
signer_priv_keys = calldata["cairo-calldata"]["signer_private_keys"]
transmitter_pub_keys = calldata["cairo-calldata"]["transmitter_public_keys"]
transmitter_priv_keys = calldata["cairo-calldata"]["transmitter_private_keys"]
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

    res = await contract.test_hexes().call()
    print(res.result)


@pytest.mark.asyncio
async def test_hex_array(contract_factory):
    starknet, contract, owner_acc = contract_factory

    x = "09080e0c190b0307021a051d141e121615131b0f0106110d00181c0410170000"

    # num = (int(x[:32], 16), int(x[32:], 16))
    num = 111111111111111111111111111111111111111111111111111111111111111

    res = await contract.test_decimal_to_hex_array(num).call()
    print(res.result)


@pytest.mark.asyncio
async def test_verify_all_signatures(contract_factory):
    starknet, contract, owner_acc = contract_factory

    res = await contract.test_verify_all_sigs(
        int(rawReportContext, 16),
        int(rawObservers[:60], 16),
        observations,
        r_sigs,
        s_sigs,
        signer_pub_keys,
    ).call()

    print(res.result)

    print("test_verify_all_signatures: PASSED")


@pytest.mark.asyncio
async def test_signatures(contract_factory):
    starknet, contract, owner_acc = contract_factory

    private_key = signer_priv_keys[0]
    message_hash = msg_hash
    public_key = private_to_stark_key(private_key)
    signature = sign(
        msg_hash=message_hash, priv_key=private_key)
    print(f'Public key: {public_key}')
    print(f'Signature: {signature}')
    print(f'message_hash: {message_hash}')

    await contract.test_verify_sig(
        message_hash,
        (r_sigs[0], s_sigs[0]),
        signer_pub_keys[0]
    ).call()

    # for i in range(len(r_sigs)):
    #     await contract.test_verify_sig(
    #         msg_hash,
    #         (r_sigs[i], s_sigs[i]),
    #         signer_pub_keys[i]
    #     ).call()
    #     break

    print("All signatures are valid")


@pytest.mark.asyncio
async def test_make_hex_array(contract_factory):
    starknet, contract, owner_acc = contract_factory
