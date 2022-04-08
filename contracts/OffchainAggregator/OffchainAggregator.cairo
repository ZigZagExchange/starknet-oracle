%lang starknet
%builtins pedersen range_check ecdsa

from starkware.cairo.common.cairo_builtins import HashBuiltin, SignatureBuiltin
from starkware.starknet.common.syscalls import get_block_number, get_block_timestamp
from starkware.starknet.common.syscalls import get_caller_address, get_contract_address
from starkware.cairo.common.alloc import alloc
from starkware.cairo.common.uint256 import (
    Uint256, uint256_add, uint256_sub, uint256_le, uint256_lt, uint256_mul, uint256_check)
from starkware.cairo.common.hash import hash2
from starkware.cairo.common.math import (
    assert_not_zero, assert_le, assert_lt, unsigned_div_rem, split_felt)

from contracts.utils.AccessControlls import set_access_controlls, only_owner
from contracts.libraries.Hexadecimals import (
    splice_array, hex_array_to_decimal, decimal_to_hex_array)
from contracts.OffchainAggregator.utils import (
    check_for_duplicates, assert_array_sorted, check_config_valid, config_digest_from_config_data,
    hash_report, verify_sig)
from contracts.structs.Response_struct import Response


struct Transmission:
    member answer : felt
    member timestamp : felt
    member block_number : felt
    member transmitter : felt
end

struct Oracle:
    member index : felt
    member role : felt  # 0=unset, 1=Signer, 2-Transmitter
end

# TODO F = 5
const F = 1

# # ===========================================================================================
# # EVENTS

@event
func config_set(
        prev_config_block_numb : felt, config_count : felt, signers_len : felt, signers : felt*,
        transmitters_len : felt, transmitters : felt*, treshold : felt, encodedConfigVersion : felt,
        encoded : felt):
end

@event
func round_requested(requester : felt, configDigest : felt, epoch : felt, round : felt):
end

@event
func new_transmission(
        aggregatorRoundId : felt, answer : felt, transmitter : felt, observations_len : felt,
        observations : felt*, observers_len : felt, observers : felt*, rawReportContext : felt):
end

# # ===========================================================================================
# # STORAGE VARS

const maxNumOracles = 31

@storage_var
func s_latestConfigDigest() -> (res : felt):
end

@storage_var
func s_latestEpochAndRound() -> (res : felt):
end

@storage_var
func s_threshold() -> (res : felt):
end

@storage_var
func s_latestAggregatorRoundId() -> (res : felt):
end

@storage_var
func s_latestConfigBlockNumber() -> (res : felt):
end

@storage_var
func s_configCount() -> (res : felt):
end

@storage_var
func s_transmissions(roundId : felt) -> (res : Transmission):
end

@storage_var
func s_oracles(idx : felt) -> (res : Oracle):
end

@storage_var
func s_signers(idx : felt) -> (address : felt):
end

@storage_var
func s_transmitters(idx : felt) -> (address : felt):
end

@storage_var
func s_num_signers() -> (res : felt):
end

@storage_var
func s_decimals() -> (res : felt):
end

@storage_var
func s_description() -> (res : felt):
end

# # ===========================================================================================
# # CONSTRUCTOR

@constructor
func constructor{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        _decimals : felt, owner : felt, _description : felt):
    set_access_controlls(owner)
    s_decimals.write(_decimals)
    s_description.write(_description)
    return ()
end

# # ===========================================================================================
# # SETTERS

@external
func requestNewRound{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (res):
    alloc_locals
    # only_owner()

    let (msg_sender : felt) = get_caller_address()
    let (config_digest : felt) = s_latestConfigDigest.read()
    let (epoch_and_round) = s_latestEpochAndRound.read()
    let (epoch, round) = unsigned_div_rem(epoch_and_round, 16 ** 2)
    let (timestamp) = latestTimestamp()

    round_requested.emit(requester=msg_sender, configDigest=config_digest, epoch=epoch, round=round)

    let (roundId : felt) = s_latestAggregatorRoundId.read()

    return (roundId + 1)
end

@external
func set_config{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        _signers_len : felt, _signers : felt*, _transmitters_len : felt, _transmitters : felt*,
        _threshold : felt, config_version : felt, config_hash : felt) -> (res):
    alloc_locals
    check_config_valid(_signers_len, _transmitters_len, _threshold)
    # only_owner()
    # TODO Recive a signature proving owner sent this without sending it through the account

    let (n_signers : felt) = s_num_signers.read()
    remove_signers_transmitters(n_signers)
    add_signers_transmitters(_signers_len, _signers, _transmitters_len, _transmitters, _signers_len)

    s_num_signers.write(_signers_len)
    s_threshold.write(_threshold)

    let (prev_config_block_num : felt) = s_latestConfigBlockNumber.read()
    let (new_block_num : felt) = get_block_number()
    s_latestConfigBlockNumber.write(new_block_num)

    let (config_count : felt) = s_configCount.read()
    s_configCount.write(config_count + 1)

    let (contract_address : felt) = get_contract_address()

    let (digest : felt) = config_digest_from_config_data(
        contract_address,
        config_count,
        _signers_len,
        _signers,
        _transmitters_len,
        _transmitters,
        _threshold,
        config_version,
        config_hash)

    let (_, config_digest) = split_felt(digest)

    s_latestConfigDigest.write(config_digest)
    s_latestEpochAndRound.write(0)

    config_set.emit(
        prev_config_block_num,
        config_count + 1,
        _signers_len,
        _signers,
        _transmitters_len,
        _transmitters,
        _threshold,
        config_version,
        config_hash)

    return (config_digest)
end

# @params:
# - report_context - 11 bytes zero pading, 16 bytes config digest, 4 bytes epoch, 1 byte round
# - observer_idxs - observer indexes representing the order of the observations
# - observations - the price observed by the oracles
# - signatures - signatures used to sign the report
# - signer_idxs - raw hex string representing which node the signature belongs to (used to retrive pub_key)

@external
func transmit{
        syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr,
        ecdsa_ptr : SignatureBuiltin*}(
        report_context : felt, observer_idxs : felt, observations_len : felt, observations : felt*,
        r_sigs_len : felt, r_sigs : felt*, s_sigs_len : felt, s_sigs : felt*, signer_idxs) -> (res):
    alloc_locals

    let (hex_rrc_len, hex_rrc : felt*) = decimal_to_hex_array(report_context, 21)

    let (conf_digest_len, conf_digest : felt*) = splice_array(hex_rrc_len, hex_rrc, 0, 32)
    let (epoch_and_round_len, epoch_and_round : felt*) = splice_array(hex_rrc_len, hex_rrc, 32, 42)

    let (latest_config_digest : felt) = s_latestConfigDigest.read()
    let (report_config_digest : felt) = hex_array_to_decimal(conf_digest_len, conf_digest)

    with_attr error_message("==== (REPORT CONFIG DIGEST DOES NOT MATCH THE LATEST ONE) ===="):
        assert report_config_digest = latest_config_digest
    end

    let (latest_epoch_and_round : felt) = s_latestEpochAndRound.read()
    let (dec_epoch_and_round : felt) = hex_array_to_decimal(epoch_and_round_len, epoch_and_round)

    let (threshold) = s_threshold.read()
    # ......................................................

    with_attr error_message("==== (SOME BASIC OBSERVATION OR SIGNATURE ASSERTIONS FAILED) ===="):
        assert_lt(latest_epoch_and_round, dec_epoch_and_round)  # Assert report is not deprecated
        assert_lt(threshold, r_sigs_len)  # Assert there are enough signatures
        assert_le(r_sigs_len, maxNumOracles)  # Assert there aren't too many signatures
        assert r_sigs_len = s_sigs_len  # Assert there are the same number of r and s signatures
        assert_le(observations_len, maxNumOracles)  # Assert there aren't too many observations
        assert_lt(2 * threshold, observations_len)  # Assert there are enough observations
    end

    # ......................................................
    # Assert the caller contract is a registered transmitter address
    let (msg_sender) = get_caller_address()
    let (transmitter : Oracle) = s_oracles.read(msg_sender)
    let (s_transmitter) = s_transmitters.read(transmitter.index)

    with_attr error_message(
            "==== (THE CALLER CONTRACT MUST BE A REGISTERED TRANSMITTER ADDRESS) ===="):
        assert transmitter.role = 2
        assert msg_sender = s_transmitter
    end

    s_latestEpochAndRound.write(dec_epoch_and_round)  # Set the new latest epoch and round

    # ......................................................

    let (hex_observers_len, hex_observers : felt*) = decimal_to_hex_array(
        observer_idxs, observations_len)
    check_for_duplicates(hex_observers_len, hex_observers, 2)

    let (hex_signer_idxs_len, hex_signer_idxs : felt*) = decimal_to_hex_array(signer_idxs, 2)
    check_for_duplicates(hex_signer_idxs_len, hex_signer_idxs, 2)

    # ......................................................

    let (msg_hash) = hash_report(report_context, observer_idxs, observations_len, observations)

    verify_all_signatures(
        msg_hash, r_sigs_len, r_sigs, s_sigs_len, s_sigs, hex_signer_idxs_len, hex_signer_idxs)

    # ......................................................

    assert_array_sorted(observations_len, observations)

    let (median_idx : felt, _) = unsigned_div_rem(observations_len, 2)
    let median = observations[median_idx]

    let (latest_round_id : felt) = s_latestAggregatorRoundId.read()
    s_latestAggregatorRoundId.write(latest_round_id + 1)

    let (timestamp : felt) = get_block_timestamp()
    let (block_num : felt) = get_block_number()
    s_transmissions.write(
        roundId=latest_round_id + 1, value=Transmission(median, timestamp, block_num, msg_sender))

    # ......................................................

    new_transmission.emit(
        aggregatorRoundId=latest_round_id,
        answer=median,
        transmitter=msg_sender,
        observations_len=observations_len,
        observations=observations,
        observers_len=hex_observers_len,
        observers=hex_observers,
        rawReportContext=report_context)

    # ......................................................

    return (1)
end

# # ===========================================================================================
# # GETTERS

@view
func latestConfigDetails{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        config_count : felt, block_num : felt, config_digest : felt):
    alloc_locals

    let (config_count : felt) = s_configCount.read()
    let (block_num : felt) = s_latestConfigBlockNumber.read()
    let (config_digest : felt) = s_latestConfigDigest.read()

    return (config_count, block_num, config_digest)
end

@view
func latestTransmissionDetails{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        ) -> (
        config_digest : felt, epoch : felt, round : felt, latest_answer : felt,
        latest_timestamp : felt):
    alloc_locals

    let (config_digest : felt) = s_latestConfigDigest.read()
    let (epoch_and_round) = s_latestEpochAndRound.read()
    let (epoch, round) = unsigned_div_rem(epoch_and_round, 16 ** 2)
    let (answer) = latestAnswer()
    let (timestamp) = latestTimestamp()

    return (config_digest, epoch, round, answer, timestamp)
end

@view
func transmitters{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        transmitters_len : felt, transmitters : felt*):
    alloc_locals

    let (local empty_arr : felt*) = alloc()
    let (total_len : felt) = s_num_signers.read()
    let (transmitters_len : felt, transmitters : felt*) = load_transmitters_array(
        0, empty_arr, total_len)

    return (transmitters_len, transmitters)
end

@view
func latestAnswer{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        res : felt):
    alloc_locals

    let (roundId : felt) = s_latestAggregatorRoundId.read()
    let (transmission : Transmission) = s_transmissions.read(roundId)

    return (transmission.answer)
end

@view
func latestTimestamp{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        res : felt):
    alloc_locals

    let (roundId : felt) = s_latestAggregatorRoundId.read()
    let (transmission : Transmission) = s_transmissions.read(roundId)

    return (transmission.timestamp)
end

@view
func latestRound{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        res : felt):
    alloc_locals

    let (roundId : felt) = s_latestAggregatorRoundId.read()

    return (roundId)
end

@view
func getAnswer{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        roundId : felt) -> (res : felt):
    alloc_locals

    let (transmission : Transmission) = s_transmissions.read(roundId)

    return (transmission.answer)
end

@view
func getTimestamp{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        roundId : felt) -> (res : felt):
    alloc_locals

    let (transmission : Transmission) = s_transmissions.read(roundId)

    return (transmission.timestamp)
end

@view
func getRoundData{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        roundId : felt) -> (res : Response):
    alloc_locals

    let (transmission : Transmission) = s_transmissions.read(roundId)

    let identifier = 0  # hash of symbol or something
    let (high, low) = split_felt(transmission.answer)
    let answer = Uint256(low=low, high=high)
    let response = Response(
        roundId,
        identifier,
        answer,
        transmission.timestamp,
        transmission.block_number,
        transmission.transmitter)

    return (response)
end

@view
func latestRoundData{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        res : Response):
    alloc_locals

    let (roundId : felt) = s_latestAggregatorRoundId.read()

    return getRoundData(roundId)
end

@view
func description{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        res : felt):
    alloc_locals

    let (description) = s_description.read()

    return (description)
end

@view
func decimals{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (res : felt):
    alloc_locals

    let (decimals) = s_decimals.read()

    return (decimals)
end

# # ===========================================================================================
# # HELPERS

# removes all signer and transmitter addresses from storage so they can be reset
func remove_signers_transmitters{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        signers_len : felt):
    if signers_len == 0:
        s_num_signers.write(0)
        return ()
    end

    let (signer) = s_signers.read(idx=signers_len - 1)
    s_signers.write(idx=signers_len - 1, value=0)

    let (transmitter) = s_transmitters.read(idx=signers_len - 1)
    s_transmitters.write(idx=signers_len - 1, value=0)

    s_oracles.write(idx=signer, value=Oracle(index=0, role=0))
    s_oracles.write(idx=transmitter, value=Oracle(index=0, role=0))

    return remove_signers_transmitters(signers_len - 1)
end

# Adds all signer and transmitter addresses to storage
func add_signers_transmitters{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        signers_len : felt, signers : felt*, transmitters_len : felt, transmitters : felt*,
        total : felt):
    if signers_len == 0:
        return ()
    end

    let signer = signers[0]
    let (oracle) = s_oracles.read(signer)
    with_attr error_message("==== (SIGNER ADDRESS IS ALREADY REGISTERED) ===="):
        assert_not_zero(oracle.role - 1)
    end

    let oracle = Oracle(index=signers_len - 1, role=1)
    s_oracles.write(idx=signer, value=oracle)
    s_signers.write(idx=signers_len - 1, value=signer)

    # ====    ====    ====    ====    ====

    let transmitter = transmitters[0]
    let (oracle) = s_oracles.read(transmitter)
    with_attr error_message("==== (TRANSMITTER ADDRESS IS ALREADY REGISTERED) ===="):
        assert_not_zero(oracle.role - 2)
    end

    let oracle = Oracle(index=signers_len - 1, role=2)
    s_oracles.write(idx=transmitter, value=oracle)
    s_transmitters.write(idx=signers_len - 1, value=transmitter)

    return add_signers_transmitters(
        signers_len - 1, &signers[1], transmitters_len - 1, &transmitters[1], total)
end

# This is used to load all transmitter addresses from s_transmitters to an array
func load_transmitters_array{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        transmitters_len : felt, transmitters : felt*, total_len : felt) -> (
        transmitters_len : felt, transmitters : felt*):
    if transmitters_len == total_len:
        return (transmitters_len, transmitters)
    end

    let (transmitter : felt) = s_transmitters.read(idx=transmitters_len)
    assert transmitters[transmitters_len] = transmitter

    return load_transmitters_array(transmitters_len + 1, transmitters, total_len)
end

# Observer indexes represent which public_key in s_signers coresponds to which r,s signature
# If observer_indexes[i] = n than the ith signature coresponds to the public key in s_signers[n]
# Then checks all signatures are valid for the coresponding public key and message hash
func verify_all_signatures{
        syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr,
        ecdsa_ptr : SignatureBuiltin*}(
        hash : felt, r_sigs_len : felt, r_sigs : felt*, s_sigs_len : felt, s_sigs : felt*,
        signer_idxs_len : felt, signer_idxs : felt*) -> ():
    alloc_locals

    if r_sigs_len == 0:
        return ()
    end

    let r_sig = r_sigs[0]
    let s_sig = s_sigs[0]
    tempvar idx = signer_idxs[0] * 16 + signer_idxs[1]

    let (pub_key) = s_signers.read(idx)

    verify_sig(hash, (r_sig, s_sig), pub_key)

    return verify_all_signatures(
        hash,
        r_sigs_len - 1,
        &r_sigs[1],
        s_sigs_len - 1,
        &s_sigs[1],
        signer_idxs_len - 2,
        &signer_idxs[2])
end

# # ===========================================================================================
# # TESTING

@view
func get_signer{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(idx : felt) -> (
        signer : felt):
    let (signer) = s_signers.read(idx=idx)

    return (signer)
end

@view
func get_transmitter{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        idx : felt) -> (transmitter : felt):
    let (transmitter) = s_transmitters.read(idx=idx)

    return (transmitter)
end

@view
func get_oracle{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(idx : felt) -> (
        oracle : Oracle):
    let (oracle) = s_oracles.read(idx=idx)

    return (oracle)
end

@view
func get_configCount{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (
        res : felt):
    let (res) = s_configCount.read()

    return (res)
end

@view
func get_latestConfigBlockNumber{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(
        ) -> (res : felt):
    let (res) = s_latestConfigBlockNumber.read()

    return (res)
end
