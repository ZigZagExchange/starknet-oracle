from copyreg import constructor
import math
import pytest
import asyncio
import json

from starkware.starknet.testing.starknet import Starknet
from starkware.starknet.testing.contract import StarknetContract

from utils import Signer

owner = Signer(111111111111111111111)

# ============   ============   ============   ==============   ==============

signer1 = "0x17631c78189801f795c548f8c18787ef9e79d98ed4cadbda610501ee5b02ae18"
signer2 = "0x797d48b7eea5e2c691d978b68e42f614d903b5fe072cde78055934f021caa6f7"
signer3 = "0x98190e18fff5c5d755a40084034be4b294ef7a8d346565028d097f8196455268"
signer4 = "0xc45bcc428670b2548268cb1138732e89646f0ef494a8d6432d635ae3b6487e49"
signer5 = "0xf943c5c8fa0e12e139942cf452717e1b4943c75738a23e5518b070deed77995a"
signer6 = "0x989dfcc07a520100c68196cc49c9d077654658134175df6aa8296e3afd2e7bcc"
signer7 = "0xdffa6c7fb333c45b26c055b601690c20f5257e91f1571e7309387b84bedf2c29"
signer8 = "0x717a4e95497a435583587898ab7fc3b782f4a2e3bca36805f241fcc5c918d974"
signer9 = "0xc48d8f7eff6ccf6f0df32a36b8e743c1af3d2efa1bef8b317ae42895d9116195"
signer10 = "0x208f1d42f53483403dbab0593be7431b59b35b5011fe8edf1449c7c73bde7e84"

transmitter1 = "0x7140fe27897e9b8101cddf2d2a223c81de629dfea994e4fe188003ba79be88ae"
transmitter2 = "0x4b107cd499622c0cc149a3621cb1bb091c60e111d058eb8bcd8799218b79e6f8"
transmitter3 = "0x4868d4ca4ccdfc19c250179bf37cefa54d13d884c101bfd11d88afc3601f9a30"
transmitter4 = "0x8c3f20074aaf07732592e07102494c28997d6f5989c9f7d412e70d54c8b08cdc"
transmitter5 = "0xfb2009f0b894fceea51ad700356f07df8f8973af40219df1db6a87698874270c"
transmitter6 = "0xf99b2f5acdcc527189e4d9dce2e2dae5ae3902a3c7eee878864da172af0a3afb"
transmitter7 = "0x9b0ee9bac840ddc85004168a508f535a2aa45ec1b18c0df400ac65c85f9376ea"
transmitter8 = "0x56c993462dc007b7ac3f0124027227a2a7e32044d90021c2ea4af4c6a5fd7e7d"
transmitter9 = "0x14e00f6078968a51d30d54d5de940c3ec3de87279488a49cfdeaca1d92bf9fda"
transmitter10 = "0xb7209f4d8e735a95c8e6ebac0780af4e43cb5c818f4b210e851af9b4aed7334d"

signers = [int(signer1, 16)//100, int(signer2, 16)//100,
           int(signer3, 16)//100, int(signer4, 16)//100,
           int(signer5, 16)//100, int(signer6, 16)//100,
           int(signer7, 16)//100, int(signer8, 16)//100,
           int(signer9, 16)//100, int(signer10, 16)//100]

transmitters = [int(transmitter1, 16)//100, int(transmitter2, 16)//100,
                int(transmitter3, 16)//100, int(transmitter4, 16)//100,
                int(transmitter5, 16)//100, int(transmitter6, 16)//100,
                int(transmitter7, 16)//100, int(transmitter8, 16)//100,
                int(transmitter9, 16)//100, int(transmitter10, 16)//100]

# ============   ============   ============   ==============   ==============
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
# ============   ============   ============   ==============   ==============


signers2 = [x*2//3 for x in signers]
transmitters2 = [x*2//3 for x in transmitters]

acc_path = "contracts/OpenZepplin/contracts/Account.cairo"
ofc_agg_path = "contracts/Chainlink/OffchainAggregator.cairo"


@pytest.fixture(scope='module')
def event_loop():
    return asyncio.new_event_loop()


@pytest.fixture(scope='module')
async def contract_factory():
    starknet = await Starknet.empty()

    ofc_agg_contract = await starknet.deploy(
        ofc_agg_path,
        constructor_calldata=[10**8, 10**11, 8]
    )

    owner_acc = await starknet.deploy(
        acc_path,
        constructor_calldata=[owner.public_key]
    )

    await ofc_agg_contract.set_config(
        signers, transmitters, 3, 12345678, 987654321).invoke()

    return starknet, ofc_agg_contract, owner_acc


@pytest.mark.asyncio
async def test_main_logic(contract_factory):
    starknet, ofc_agg_contract, owner_acc = contract_factory

    res = await ofc_agg_contract.transmit(
        int(rawReportContext, 16),
        (int(rawObservers[:32], 16),
         int(rawObservers[32:], 16)),
        observations,
        r_sigs,
        s_sigs,
        public_keys,
    ).invoke()

    print(res.result)


@pytest.mark.asyncio
async def test_set_config_signers_transmitters(contract_factory):
    starknet, ofc_agg_contract, owner_acc = contract_factory

    await ofc_agg_contract.set_config(
        signers, transmitters, 3, 12345678, 987654321).invoke()

    for i in range(len(signers)):
        s = await ofc_agg_contract.get_signer(i).call()
        t = await ofc_agg_contract.get_transmitter(i).call()
        assert s.result.signer == signers[len(signers) - i-1]
        assert t.result.transmitter == transmitters[len(signers) - i-1]

    await ofc_agg_contract.set_config(
        signers2, transmitters2, 3, 12345678, 987654321).invoke()
    for i in range(len(signers)):
        s = await ofc_agg_contract.get_signer(i).call()
        t = await ofc_agg_contract.get_transmitter(i).call()
        assert s.result.signer == signers2[len(signers) - i-1]
        assert t.result.transmitter == transmitters2[len(signers) - i-1]

    print("\n", "test_set_config_singers_transmitters: PASSED")


@ pytest.mark.asyncio
async def test_set_config_other(contract_factory):
    starknet, ofc_agg_contract, owner_acc = contract_factory

    res = await ofc_agg_contract.set_config(
        signers, transmitters, 3, 12345678, 987654321).invoke()

    h_vars = await ofc_agg_contract.get_latest_hot_vars_test().call()
    # conf_count = await ofc_agg_contract.get_configCount().call()
    # l_bn = await ofc_agg_contract.get_latestConfigBlockNumber().call()

    print("\n", h_vars.result)


@ pytest.mark.asyncio
async def test_config_digest_from_data(contract_factory):
    starknet, ofc_agg_contract, owner_acc = contract_factory

    res = await ofc_agg_contract.config_digest_from_config_data(
        12892353439029830121023, 3, signers, transmitters, 8,
        12092395732124367332797023, 129728432856372493286482).call()

    print(res.result.digest)
    print("test_config_digest_from_data: PASSED")


@ pytest.mark.asyncio
async def test_get_transmitters(contract_factory):
    starknet, ofc_agg_contract, owner_acc = contract_factory

    res = await ofc_agg_contract.transmitters().call()

    for i, transmitter in enumerate(list(res.result.transmitters)):
        assert transmitter == transmitters[i]

    print("test_get_transmitters: PASSED")


def split_hex_64(x):
    return int(x[:32], 16), int(x[32:], 16)
