#!/usr/bin/env python3

import json
import os
import random
import socket

from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from eth_account.datastructures import SignedTransaction
from hexbytes import HexBytes


ip_addr = socket.gethostbyname('eth')
local_url = f'http://{ip_addr}:8545'
relayer_public_key_path = f'/output/relayer_key.pem'
relayer_private_key_path = f'/data/private_key.pem'
enc_block_path = f'/input/enc_block.txt'

contract_addr_dict = {
    'Honeypot': '0x2ACe51b358Aa73b3D85C1962e8D2A9cD8e6349c7',
}



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

    def deserialize(serialized_block):
        serialized_tx_list = eval(serialized_block)
        tx_list = list()
        for serialized_tx in serialized_tx_list:
            tx_list.append(deserialize_signed_tx(serialized_tx))
        return Block(tx_list)

    def apply(self, w3):
        for tx in self.tx_list:
            receipt = send_tx(tx, w3)
            print("receipt", receipt)
            contract = instantiate_contract('Honeypot', w3)
            log = contract.events.BountyClaimed().processReceipt(receipt)
            print(f'winner {log[0]["args"]["winner"]}')

def decrypt_block(encrypted_block, private_key):
    return Block.deserialize(bytes_to_str(asym_decrypt(encrypted_block, private_key)))

def wrap_block(preimage, w3, contract, account):
    tx = build_tx(contract.functions.claimBounty(preimage), w3, account.address)
    print(f'tx {tx}')
    signed_tx = sign_tx(tx, w3, account)
    print(f'signed_tx {signed_tx}')

    tx_list = [signed_tx]
    block = Block(tx_list)
    return block

def wrap_new_block(w3, preimage, relayer_account):
    contract = instantiate_contract('Honeypot', w3)
    return wrap_block(preimage, w3, contract, relayer_account)

def parse_contract(contract_name):
    contract = json.load(open(f'/input/{contract_name}.json'))
    return contract['abi'], contract['bytecode']

def instantiate_contract(contract_name, w3):
    abi, bytecode = parse_contract(contract_name)
    return w3.eth.contract(address=contract_addr_dict[contract_name], abi=abi)

def get_account(w3, account_name):
    path = f'/input/{account_name}'
    for filename in os.listdir(path):
        with open(f'{path}/{filename}', 'r') as keyfile:
            encrypted_key = keyfile.read()
            private_key = w3.eth.account.decrypt(encrypted_key, '')
            account = w3.eth.account.privateKeyToAccount(private_key)
            return account
def build_tx(func_to_call, w3, account_addr, value=0, nonce=0):
    return func_to_call.build_transaction({
        'from': account_addr,
        'gas': 5000000,
        "gasPrice": w3.eth.gas_price,
        'value': value,
        'nonce': w3.eth.get_transaction_count(account_addr) if nonce == 0 else nonce
    })

def sign_tx(tx, w3, account):
    return w3.eth.account.sign_transaction(tx, account.privateKey)

def send_tx(signed_tx, w3):
    w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return wait_for_receipt(signed_tx.hash, w3)

def wait_for_receipt(tx_hash, w3):
    return w3.eth.wait_for_transaction_receipt(tx_hash)




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