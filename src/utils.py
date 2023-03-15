import json
import os

from src.ecc.cipher import ElGamal
from src.ecc.curve import Curve25519, Point
from src.ecc.key import get_public_key, gen_keypair
from eth_account.datastructures import SignedTransaction
from hexbytes import HexBytes


local_url = 'http://127.0.0.1:8545'

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
            print(receipt)
            contract = instantiate_contract('Honeypot', w3)
            log = contract.events.BountyClaimed().processReceipt(receipt)
            print(f'winner {log[0]["args"]["winner"]}')


def str_to_bytes(st):
    return bytes(st, encoding='utf-8')


def bytes_to_str(bt):
    return bt.decode(encoding='utf-8')


def parse_contract(contract_name):
    contract = json.load(open(f'chain/build/contracts/{contract_name}.json'))
    return contract['abi'], contract['bytecode']


def instantiate_contract(contract_name, w3):
    abi, bytecode = parse_contract(contract_name)
    return w3.eth.contract(address=contract_addr_dict[contract_name], abi=abi)


def get_balance(w3, addr):
    balance = w3.eth.get_balance(addr)
    print(f'balance of {addr} is {balance}')
    return balance


def get_account(w3, account_name):
    path = f'chain/keystores/{account_name}'
    for filename in os.listdir(path):
        with open(f'{path}/{filename}', 'r') as keyfile:
            encrypted_key = keyfile.read()
            private_key = w3.eth.account.decrypt(encrypted_key, '')
            account = w3.eth.account.privateKeyToAccount(private_key)
            return account


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


def encrypt(data, public_key): ### data is of bytes
    # c1, c2 = ElGamal(Curve25519).encrypt(data, public_key)
    # return c1.x, c1.y, c2.x, c2.y
    return data


def decrypt(sealed_data, private_key):
    # c1 = Point(sealed_data[0], sealed_data[1], Curve25519)
    # c2 = Point(sealed_data[2], sealed_data[3], Curve25519)
    # print(c1)
    # print(c2)
    # return ElGamal(Curve25519).decrypt(private_key, c1, c2)
    return sealed_data


def get_keypair(private_key_location):
    try:
        with open(private_key_location, 'r') as f:
            private_key = int(f.readline())
        public_key = get_public_key(private_key, Curve25519)
    except Exception as _:
        private_key, public_key = gen_keypair(Curve25519)
        with open(private_key_location, 'w') as f:
            f.write(f'{private_key}')
    return private_key, public_key


def get_public_key(private_key_location):
    return get_keypair(private_key_location)[1]


def get_private_key(private_key_location):
    return get_keypair(private_key_location)[0]


def bytes_to_int(x):
    return int.from_bytes(x, 'big')


def int_to_bytes(x):
    return x.to_bytes((x.bit_length() + 7) // 8, 'big')


def bytes_to_hex(bt):
    return '0x' + bt.hex()


def hex_to_bytes(hx):
    return bytes.fromhex(hx)
