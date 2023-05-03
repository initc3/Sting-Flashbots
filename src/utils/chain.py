import os

from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware


local_url = 'http://127.0.0.1:8545'
ether_unit = 10**18
GAS_LIMIT = 1000000
local_net_chain_id = 123


def get_web3():
    w3 = Web3(HTTPProvider(local_url))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3


def get_address(web3, account_name):
    dir = f'chain/keystores/{account_name}/'
    for filename in os.listdir(dir):
        with open(dir + filename) as keyfile:
            content = keyfile.read()
            addr = eval(content)['address']
            return web3.toChecksumAddress('0x' + addr)


def get_account(w3, account_name):
    path = f'chain/keystores/{account_name}'
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


def transfer_ether(w3, sender_account, receiver_addr, amt, chain_id=local_net_chain_id):
    tx = {
        'to': receiver_addr,
        'from': sender_account.address,
        'value': amt,
        "gasPrice": w3.eth.gas_price,
        'gas': GAS_LIMIT,
        'nonce': w3.eth.get_transaction_count(sender_account.address),
        'chainId': chain_id,
    }
    return tx


def refill_ether(w3, receiver_addr):
    admin_account = get_account(w3, f'admin')

    amt = 100 * ether_unit
    balance = get_balance(w3, receiver_addr)
    amt -= balance
    print(f'refilling {amt}...')

    if amt > 0:
        tx = transfer_ether(w3, admin_account, receiver_addr, amt)
        signed_tx = sign_tx(tx, w3, admin_account)
        return send_tx(signed_tx, w3)

    get_balance(w3, receiver_addr)


def build_tx(func_to_call, w3, account_addr, value=0, nonce=0):
    return func_to_call.build_transaction({
        'from': account_addr,
        'gas': GAS_LIMIT,
        "gasPrice": w3.eth.gas_price,
        'value': value,
        'nonce': w3.eth.get_transaction_count(account_addr) if nonce == 0 else nonce
    })


def sign_tx(tx, w3, account, k=0):
    return w3.eth.account.sign_transaction(tx, account.privateKey, k)


def send_tx(signed_tx, w3):
    w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return wait_for_receipt(signed_tx.hash, w3)


def wait_for_receipt(tx_hash, w3):
    return w3.eth.wait_for_transaction_receipt(tx_hash)


def transact(func_to_call, w3, account, value=0, k=0):
    tx = build_tx(func_to_call, w3, account.address, value)
    signed_tx = sign_tx(tx, w3, account, k)
    return send_tx(signed_tx, w3)
