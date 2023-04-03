#!/usr/bin/env python3

import os 

from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware

from enclave.utils import wait_for_receipt, local_url

ether_unit = 10**18


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

if __name__ == '__main__':
    w3 = Web3(HTTPProvider(local_url))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    
    admin_account = get_account(w3, f'admin')
    receiver_addr = get_account(w3, f'relayer').address
    amt = 100 * ether_unit
    balance = get_balance(w3, receiver_addr)
    amt -= balance
    print(f'refilling {amt}...')

    if amt > 0:
        transfer_ether(w3, admin_account.address, receiver_addr, amt)

    get_balance(w3, receiver_addr)