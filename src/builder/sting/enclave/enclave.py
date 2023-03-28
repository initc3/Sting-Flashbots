#!/usr/bin/env python3
import random
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
from eth_abi import encode
from utils import build_tx, sign_tx, Block, str_to_bytes, bytes_to_int, int_to_bytes, asym_encrypt, local_url

from eth_utils import keccak

sealed_preimage_localtion = f'/data/sealed_preimage.txt'
key_location = f'/data/key.txt'
output_location = f'output/output.txt'

def sample():
    return random.randint(0, 10000)


def get_sym_key():
    try:
        with open(key_location, 'r') as f:
            key = eval(f.readline())
    except Exception as e:
        key = get_random_bytes(16)
        with open(key_location, 'w') as f:
            f.write(str(key))
    return key


def sym_encrypt(plaintext, key):
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    return cipher.nonce, tag, ciphertext


def sym_decrypt(ciphertext, key):
    nonce, tag, ciphertext = ciphertext
    cipher = AES.new(key, AES.MODE_EAX, nonce)
    return cipher.decrypt_and_verify(ciphertext, tag)


def ecall_create_puzzle():
    preimage = sample()
    print(f'preimage: {preimage}')

    puzzle = keccak(encode(['uint'], [preimage]))
    print(f'puzzle {puzzle}')

    bytes_preimage = int_to_bytes(preimage)
    # key = get_sym_key()
    # print(f'bytes_preimage {bytes_preimage}')
    # sealed_preimage = sym_encrypt(bytes_preimage, key)

    with open(sealed_preimage_localtion, 'w') as f:
        f.write(f'{bytes_preimage}')

    with open(output_location, "wb") as f:
        f.write(puzzle)
    return puzzle


def fetch_preimage():
    with open(sealed_preimage_localtion, 'r') as f:
        sealed_preimage = eval(f.readline())
        preimage = bytes_to_int(sealed_preimage)#sym_decrypt(sealed_preimage, key))
        print(f'preimage: {preimage}')
        return preimage


def ecall_claim_bounty(contract, account, relayer_public_key):
    w3 = Web3(HTTPProvider(local_url))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    preimage = fetch_preimage()
    return warp_encrypted_block(preimage, w3, contract, account, relayer_public_key)


def warp_encrypted_block(preimage, w3, contract, account, relayer_public_key):
    tx = build_tx(contract.functions.claimBounty(preimage), w3, account.address)
    print(f'tx {tx}')
    signed_tx = sign_tx(tx, w3, account)
    print(f'signed_tx {signed_tx}')

    tx_list = [signed_tx]
    block = Block(tx_list)
    return asym_encrypt(str_to_bytes(block.serialize()), relayer_public_key)

ecall_create_puzzle()