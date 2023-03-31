#!/usr/bin/env python3

import json
import os
import socket

from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from eth_account.datastructures import SignedTransaction
from hexbytes import HexBytes


ip_addr = socket.gethostbyname('eth')
local_url = f'http://{ip_addr}:8545'

contract_addr_dict = {
    'Honeypot': '0x2ACe51b358Aa73b3D85C1962e8D2A9cD8e6349c7',
}

ether_unit = 10**18


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


def parse_contract(contract_name):
    contract = json.load(open(f'/Sting-Flashbots/chain/build/contracts/{contract_name}.json'))
    return contract['abi'], contract['bytecode']

def instantiate_contract(contract_name, w3):
    abi, bytecode = parse_contract(contract_name)
    return w3.eth.contract(address=contract_addr_dict[contract_name], abi=abi)

def get_account(w3, account_name):
    path = f'/Sting-Flashbots/chain/keystores/{account_name}'
    for filename in os.listdir(path):
        with open(f'{path}/{filename}', 'r') as keyfile:
            encrypted_key = keyfile.read()
            private_key = w3.eth.account.decrypt(encrypted_key, '')
            account = w3.eth.account.privateKeyToAccount(private_key)
            return account

def get_balance(w3, addr):
    balance = w3.eth.get_balance(addr)
    print(f'balance of {addr} is {balance}')
    return balance

def transfer_ether(w3, sender_addr, receiver_addr, amt):
    w3.eth.defaultAccount = sender_addr
    tx_hash = w3.eth.send_transaction({
        'to': receiver_addr,
        'from': sender_addr,
        'value': amt
    })
    wait_for_receipt(tx_hash, w3)


def refill_ether(w3, receiver_addr):
    admin_account = get_account(w3, f'admin')

    amt = 100 * ether_unit
    balance = get_balance(w3, receiver_addr)
    amt -= balance
    print(f'refilling {amt}...')

    if amt > 0:
        transfer_ether(w3, admin_account.address, receiver_addr, amt)

    get_balance(w3, receiver_addr)


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


def transact(func_to_call, w3, account, value=0):
    tx = build_tx(func_to_call, w3, account.address, value)
    signed_tx = sign_tx(tx, w3, account)
    return send_tx(signed_tx, w3)


def gen_keypair(key_path):
    key = RSA.generate(2048)
    private_key = key.export_key()
    with open(f'{key_path}/private.pem', 'wb') as f:
        f.write(private_key)

    public_key = key.publickey().export_key()
    with open(f'{key_path}/receiver.pem', 'wb') as f:
        f.write(public_key)

    return key, key.publickey()


def get_private_key(key_path):
    try:
        private_key = RSA.import_key(open(f'{key_path}/private.pem').read())
    except Exception as _:
        private_key, _ = gen_keypair(key_path)

    return private_key


def get_public_key(key_path):
    try:
        recipient_key = RSA.import_key(open(f'{key_path}/receiver.pem').read())
    except Exception as _:
        _, recipient_key = gen_keypair(key_path)

    return recipient_key

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

def bytes_to_hex(bt):
    return '0x' + bt.hex()
