#!/usr/bin/env python3

import json
import random
import socket

from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Random import get_random_bytes
from eth_account.datastructures import SignedTransaction
from hexbytes import HexBytes

ip_addr = socket.gethostbyname('eth')
local_url = f'http://{ip_addr}:8545'
sealed_preimage_localtion = f'/data/sealed_preimage.txt'
puzzle_path =  f'/data/puzzle.txt'

contract_addr_dict = {
    'Honeypot': '0x2ACe51b358Aa73b3D85C1962e8D2A9cD8e6349c7',
}

def fetch_preimage():
    with open(sealed_preimage_localtion, 'r') as f:
        sealed_preimage = eval(f.readline())
        preimage = bytes_to_int(sealed_preimage)
        print(f'preimage: {preimage}')
        return preimage


def serialize_signed_tx(signed_tx):
    return str({
        'rawTransaction': signed_tx.rawTransaction.hex(),
        'hash': signed_tx.hash.hex(),
        'r': signed_tx.r,
        's': signed_tx.s,
        'v': signed_tx.v,
    })

def deserialize_signed_tx(st):
    data = eval(st)
    return SignedTransaction(
        rawTransaction = HexBytes(data['rawTransaction']),
        hash = HexBytes(data['hash']),
        r = data['r'],
        s = data['s'],
        v = data['v'],
    )

class Block:
    def __init__(self, tx_list):
        self.tx_list = tx_list

    def serialize(self):
        serialized_tx_list = list()
        for tx in self.tx_list:
            serialized_tx_list.append(serialize_signed_tx(tx))
        return str(serialized_tx_list)

def parse_contract(contract_name):
    contract = json.load(open(f'/input/{contract_name}.json'))
    return contract['abi'], contract['bytecode']

def instantiate_contract(contract_name, w3):
    abi, bytecode = parse_contract(contract_name)
    return w3.eth.contract(address=contract_addr_dict[contract_name], abi=abi)

def asym_encrypt(plaintext, recipient_key):
    session_key = get_random_bytes(16)

    # Encrypt the session key with the public RSA key
    cipher_rsa = PKCS1_OAEP.new(recipient_key)
    enc_session_key = cipher_rsa.encrypt(session_key)

    # Encrypt the data with the AES session key
    cipher_aes = AES.new(session_key, AES.MODE_EAX)
    ciphertext, tag = cipher_aes.encrypt_and_digest(plaintext)

    return enc_session_key, cipher_aes.nonce, tag, ciphertext

def asym_decrypt(ciphertext, private_key):
    enc_session_key, nonce, tag, ciphertext = ciphertext

    # Decrypt the session key with the private RSA key
    cipher_rsa = PKCS1_OAEP.new(private_key)
    session_key = cipher_rsa.decrypt(enc_session_key)

    # Decrypt the data with the AES session key
    cipher_aes = AES.new(session_key, AES.MODE_EAX, nonce)
    return cipher_aes.decrypt_and_verify(ciphertext, tag)

def str_to_bytes(st):
    return bytes(st, encoding='utf-8')

def bytes_to_str(bt):
    return bt.decode(encoding='utf-8')

def bytes_to_int(x):
    return int.from_bytes(x, 'big')

def int_to_bytes(x):
    return x.to_bytes((x.bit_length() + 7) // 8, 'big')

def hex_to_bytes(hx):
    return bytes.fromhex(hx)

def sample():
    return random.randint(0, 10000)