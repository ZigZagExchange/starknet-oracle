"""Utilities for testing Cairo contracts."""

from inspect import signature
from starkware.cairo.common.hash_state import compute_hash_on_elements
from starkware.crypto.signature.signature import private_to_stark_key, sign
from starkware.starknet.definitions.error_codes import StarknetErrorCode
from starkware.starkware_utils.error_handling import StarkException
from starkware.starknet.public.abi import get_selector_from_name

MAX_UINT256 = (2**128 - 1, 2**128 - 1)


def str_to_felt(text):
    b_text = bytes(text, 'UTF-8')
    return int.from_bytes(b_text, "big")


def uint(a):
    return(a, 0)


async def assert_revert(fun):
    try:
        await fun
        assert False
    except StarkException as err:
        _, error = err.args
        assert error['code'] == StarknetErrorCode.TRANSACTION_FAILED

# ===============================================================


class Transmitter():

    def __init__(self, private_key):
        self.private_key = private_key
        self.public_key = private_to_stark_key(private_key)

    def sign(self, message_hash):
        return sign(msg_hash=message_hash, priv_key=self.private_key)

    async def send_transaction(self, account, to, selector_name, calldata, nonce=None):
        rrc, robs,  obs, r_sigs, s_sigs, pub_keys = calldata
        if nonce is None:
            result = await account.functions["get_nonce"].call()
            nonce = result.res

        selector = get_selector_from_name(selector_name)
        message_hash = transmitter_hash_message(
            account.address, to, selector, calldata, nonce)
        sig_r, sig_s = self.sign(message_hash)

        transmit = account.functions["transmit"].prepare(
            to, selector, rrc, robs,  obs, r_sigs, s_sigs, pub_keys, nonce)
        return await transmit.invoke(signature=[sig_r, sig_s])
        # return await account.functions["transmit"] \
        #     .invoke(to, selector, rrc, robs,  obs, r_sigs, s_sigs, pub_keys, nonce, signature=[sig_r, sig_s])


def transmitter_hash_message(sender, to, selector, calldata, nonce):

    rrc, robs,  obs, r_sigs, s_sigs, pub_keys = calldata

    calldata_hash = compute_hash_on_elements(
        [rrc, robs] + obs + r_sigs + s_sigs + pub_keys)

    message = [
        sender,
        to,
        selector,
        calldata_hash,
        nonce
    ]
    return compute_hash_on_elements(message)
