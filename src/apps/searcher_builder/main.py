import os
import random

from lib.commitment.elliptic_curves_finite_fields.elliptic import Point
from lib.commitment.secp256k1 import uint256_from_str, G, Fq, curve, ser
from src.SF.SF_Application.SF_Application import generate_stinger
from src.SF.Subversion_Service.Subversion_Service import leak_data
from src.utils.asym_enc import get_public_key, target_key_path, asym_decrypt
from src.utils.chain import get_web3, get_account, refill_ether, get_address, transfer_ether, sign_tx, ether_unit, send_tx
from src.utils.general import int_to_bytes, str_to_bytes, bytes_to_str, bytes_to_int, hex_to_bytes
from src.utils.tx import serialize_tx_list, deserialize_tx_list, recover_tx

seed = 7

Hx = Fq(0xbc4f48d7a8651dc97ae415f0b47a52ef1a2702098202392b88bc925f6e89ee17)
Hy = Fq(0x361b27b55c10f94ec0630b4c7d28f963221a0031632092bf585825823f6e27df)
H = Point(curve, Hx, Hy)

commitment_opening_location = f'src/apps/searcher_builder'


def sample():
    random.seed(seed)
    return random.randint(0, 10000)


def create_tx(w3, k, name):
    sender_account = get_account(w3, name)
    refill_ether(w3, sender_account.address)

    receiver_addr = get_address(w3, 'receiver')

    unsigned_tx = transfer_ether(w3, sender_account, receiver_addr, amt=int(0.5 * ether_unit))
    signed_tx = sign_tx(unsigned_tx, w3, sender_account, k=k)
    return signed_tx, unsigned_tx


def make_bundle(w3):
    k = sample()
    print(f'use randomly sampled k {k} in signature')
    signed_tx, _ = create_tx(w3, k, 'sender')

    bundle = [
        # {"signed_transaction": signed_tx.rawTransaction},
        signed_tx,
    ]

    return int_to_bytes(k), str_to_bytes(serialize_tx_list(bundle))


def decrypt_bundle(encrypted_bundle, private_key):
    bundle = deserialize_tx_list(bytes_to_str(asym_decrypt(encrypted_bundle, private_key)))
    return bundle



def make_pedersen_commitment(x, rnd_bytes=os.urandom):
    r = uint256_from_str(rnd_bytes(32))
    C = x * G + r * H
    return bytes_to_int(hex_to_bytes(ser(C))), r


def compute_pedersen_commitment(x, r):
    C = x * G + r * H
    return bytes_to_int(hex_to_bytes(ser(C))), r


def make_evidence(w3, bundle):
    victim_tx = bundle[0]

    C, r = make_pedersen_commitment(victim_tx.r)

    print(f'use commitment {C} as k in signature')

    adv_tx, unsigned_adv_tx = create_tx(w3, C, 'sting')

    ###TODO: integrate with builder
    bundle.insert(0, adv_tx)

    return bundle, r, unsigned_adv_tx


def apply(bundle):
    receipt_list = list()
    for tx in bundle:
        receipt = send_tx(tx, w3)
        receipt_list.append(receipt)
    return receipt_list


def verify(w3, r, sting_account, receipt_list, unsigned_adv_tx):
    adv_tx_hash = receipt_list[0]['transactionHash']
    victim_tx_hash = receipt_list[1]['transactionHash']
    adv_tx = recover_tx(w3.eth.get_raw_transaction(adv_tx_hash))
    victim_tx = recover_tx(w3.eth.get_raw_transaction(victim_tx_hash))

    C, _ = compute_pedersen_commitment(victim_tx.r, r)
    tx = sign_tx(unsigned_adv_tx, w3, sting_account, k=C)

    assert(tx.v == adv_tx.v)
    assert(tx.r == adv_tx.r)
    assert(tx.s == adv_tx.s)


if __name__ == '__main__':
    w3 = get_web3()

    target_public_key = get_public_key(target_key_path)
    s = generate_stinger(make_bundle, (w3), target_public_key)

    l = leak_data(decrypt_bundle, s)

    bundle, r, unsigned_adv_tx = make_evidence(w3, l)

    receipt_list = apply(bundle)

    sting_account = get_account(w3, 'sting')
    refill_ether(w3, sting_account.address)

    verify(w3, r, sting_account, receipt_list, unsigned_adv_tx)



