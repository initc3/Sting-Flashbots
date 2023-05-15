import os
import random

from cytoolz import dissoc
from eth_account._utils.legacy_transactions import serializable_unsigned_transaction_from_dict
from eth_account._utils.signing import to_bytes32, to_eth_v, to_standard_v
from eth_utils import to_bytes
from lib.commitment.secp256k1 import uint256_from_str
from lib.mkp.proveth import generate_proof_blob_from_jsonrpc_using_number
from prev_demo.utils import parse_contract
from src.SF.SF_Application.SF_Application import generate_stinger
from src.SF.Subversion_Service.Subversion_Service import leak_data
from src.utils.asym_enc import get_public_key, target_key_path, asym_decrypt
from src.utils.chain import get_web3, get_account, get_address, transfer_ether, sign_tx, ether_unit, \
    send_tx, transact, local_url
from src.utils.general import int_to_bytes, str_to_bytes, bytes_to_str, bytes_to_int
from src.utils.tx import serialize_tx_list, deserialize_tx_list, recover_tx

seed = 7

commitment_opening_location = f'src/apps/searcher_builder'


def sample():
    random.seed(seed)
    return random.randint(0, 10000)


def create_tx(w3, name, k=0):
    sender_account = get_account(w3, name)

    receiver_addr = get_address(w3, 'receiver')

    unsigned_tx = transfer_ether(w3, sender_account, receiver_addr, amt=int(0.5 * ether_unit))
    if k != 0:
        signed_tx = sign_tx(unsigned_tx, w3, sender_account, k=k)
    else:
        signed_tx = sign_tx(unsigned_tx, w3, sender_account)

    return signed_tx, unsigned_tx


def make_bundle(w3):
    k = sample()
    signed_tx, _ = create_tx(w3, 'sender', k)

    bundle = [
        signed_tx,
    ]

    return int_to_bytes(k), str_to_bytes(serialize_tx_list(bundle))


def decrypt_bundle(encrypted_bundle, private_key):
    bundle = deserialize_tx_list(bytes_to_str(asym_decrypt(encrypted_bundle, private_key)))
    return bundle


def make_commitment(x, rnd_bytes=os.urandom):
    r = uint256_from_str(rnd_bytes(32))
    return bytes_to_int(x) ^ r, r


def compute_commitment(x, r):
    return bytes_to_int(x) ^ r


def make_evidence(w3, victim_bundle):
    victim_tx = victim_bundle[0]
    victim_tx_hash = victim_tx.hash

    C, r = make_commitment(victim_tx_hash)

    adv_tx, unsigned_adv_tx = create_tx(w3, 'sting', C)

    ###TODO: integrate with builder
    new_bundle = [adv_tx] + victim_bundle

    return new_bundle, r, unsigned_adv_tx


def apply(bundle):
    receipt_list = list()
    for tx in bundle:
        receipt = send_tx(tx, w3)
        receipt_list.append(receipt)
    return receipt_list


def verify(w3, r, sting_account, adv_tx_hash, unsigned_adv_tx, victim_bundle):
    adv_tx = recover_tx(w3.eth.get_raw_transaction(adv_tx_hash))

    victim_tx = victim_bundle[0]
    victim_tx_hash = victim_tx.hash
    print(f'victim_tx_hash {victim_tx_hash}')
    C = compute_commitment(victim_tx_hash, r)
    print(f'Commitment {C} r {r}')
    tx = sign_tx(unsigned_adv_tx, w3, sting_account, k=C)

    assert(tx.v == adv_tx.v)
    assert(tx.r == adv_tx.r)
    assert(tx.s == adv_tx.s)

    h = 0
    unsigned_adv_tx_hash = serializable_unsigned_transaction_from_dict(dissoc(unsigned_adv_tx, "from")).hash()
    print(f'unsigned_adv_tx_hash {unsigned_adv_tx_hash}')
    adv_tx_sig = (to_bytes32(adv_tx.r) + to_bytes32(adv_tx.s) + to_bytes(to_eth_v(to_standard_v(adv_tx.v))))
    print(f'adv_tx_sig {adv_tx_sig} {len(adv_tx_sig)}')
    assert(transact(contract.functions.claimBounty(
        r, h, victim_tx_hash,
        unsigned_adv_tx_hash, adv_tx_sig,
    ), w3, sting_account)['status'] == 1)

    print(f'Succeed!!!')


if __name__ == '__main__':
    w3 = get_web3()

    sting_account = get_account(w3, 'sting')

    mr_enclave = bytes()
    bounty = int(0.5 * ether_unit)
    abi, bytecode = parse_contract('Honeypot')
    receipt = transact(w3.eth.contract(
        abi=abi,
        bytecode=bytecode
    ).constructor(mr_enclave), w3, sting_account, bounty, k=123)
    contract_addr = receipt['contractAddress']
    contract = w3.eth.contract(address=contract_addr, abi=abi)

    target_public_key = get_public_key(target_key_path)
    s = generate_stinger(make_bundle, (w3), target_public_key)

    victim_bundle = leak_data(decrypt_bundle, s)

    new_bundle, r, unsigned_adv_tx = make_evidence(w3, victim_bundle)

    receipt_list = apply(new_bundle)
    victim_tx_receipt = receipt_list[-1]
    print('victim_tx_receipt', victim_tx_receipt)
    block_number = victim_tx_receipt['blockNumber']
    tx_index = victim_tx_receipt['transactionIndex']
    print('block_number', block_number)
    print('tx_index', tx_index)
    proof_blob = generate_proof_blob_from_jsonrpc_using_number(local_url, block_number, tx_index)
    print('proof_blob', proof_blob)
    exit(0)

    verify(w3, r, sting_account, receipt_list[0]['transactionHash'], unsigned_adv_tx, victim_bundle)

