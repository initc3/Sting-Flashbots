import socket
import os 
import random
from hexbytes import HexBytes

from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
from web3.middleware import construct_sign_and_send_raw_middleware
from eth_utils import keccak
# from eth_account.account import Account
from lib.ecdsa.account import Account
from eth_account.datastructures import SignedTransaction
from eth_account.signers.local import LocalAccount
from eth_account._utils.legacy_transactions import Transaction

from flashbots import flashbot

from lib.commitment.elliptic_curves_finite_fields.elliptic import Point
from lib.commitment.secp256k1 import uint256_from_str, G, Fq, curve, ser

endpoint = f"http://{socket.gethostbyname('builder')}:8545"
ADMIN_ACCOUNT: LocalAccount = Account.from_key(os.environ.get("ADMIN_PRIVATE_KEY","0xf380884ad465b73845ca785d7e125e4cc831a8267ed1be5da6299ea6094d177c"))
ETH_ACCOUNT_SIGNATURE: LocalAccount = Account.from_key(os.environ.get("SEARCHER_KEY", "0x4ac4fdb381ee97a57fd217ce2cea80efa3c0d8ea7012d28b480bd51a942ce9f8"))
CHAIN_ID = 32382
GAS_LIMIT = 25000
SEED = 777
random.seed(SEED)
# secret_path = f'/data/sealed_data.txt'
# subversionservice_path = f'/input/subversion_service/leak.txt'
secret_path = '/Sting-Flashbots/searcher/enclave_data/sealed_data.txt'
subversionservice_path = '/Sting-Flashbots/searcher/input_data/leak.txt'

def get_web3():
    w3 = Web3(HTTPProvider(endpoint))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    flashbot(w3, ETH_ACCOUNT_SIGNATURE, endpoint)
    print(f'block {w3.eth.block_number}')
    return w3

def get_balance(w3, addr):
    balance = w3.eth.get_balance(addr)
    return balance

def get_account(w3, account_name):
    try:
        path = f'/input/keystores/{account_name}'
        filename = os.listdir(path)[0]
        keyfile = open(f'{path}/{filename}', 'r')
        encrypted_key = keyfile.read()
    except:
        path = f'/Sting-Flashbots/keystores/{account_name}'
        filename = os.listdir(path)[0]
        keyfile = open(f'{path}/{filename}', 'r')
        encrypted_key = keyfile.read()

    private_key = w3.eth.account.decrypt(encrypted_key, '')
    account = Account.from_key(private_key)
    return account

def setup_new_account(w3):
    new_account = w3.eth.account.create()
    w3.middleware_onion.add(construct_sign_and_send_raw_middleware(new_account))
    return new_account

def sign_tx(w3, tx, account, k=0):
    return w3.eth.account.sign_transaction(tx, account.privateKey, k)

def send_tx(w3, signed_tx):
    w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return wait_for_receipt(w3, signed_tx.hash)

def wait_for_receipt(w3, tx_hash):
    return w3.eth.wait_for_transaction_receipt(tx_hash)

def transfer_tx(w3, sender_addr, receiver_addr, amt):
    return {
        'to': receiver_addr,
        'from': sender_addr,
        'value': amt,
        "gasPrice": w3.eth.gas_price*10,
        'gas': GAS_LIMIT,
        'nonce': w3.eth.get_transaction_count(sender_addr),
        'chainId': CHAIN_ID,
    }

def refill_ether(w3, receiver_addr, amt=1000):
    print(f"admin_account balance: {get_balance(w3, ADMIN_ACCOUNT.address)}")
    balance = get_balance(w3, receiver_addr)
    amt -= balance
    print(f'refilling {receiver_addr} amt: {amt} current: {balance}')

    if amt > 0:
        tx = transfer_tx(w3, ADMIN_ACCOUNT.address, receiver_addr, amt)
        signed_tx = sign_tx(w3, tx, ADMIN_ACCOUNT)
        send_tx(w3, signed_tx)
    print(f'refilling {receiver_addr} updated: {get_balance(w3, receiver_addr)}')

def sample(max=1000):
    return random.randint(0, max)

def generate_tx(w3):
    sender = setup_new_account(w3)
    receiver = setup_new_account(w3)
    amt = sample()
    refill_ether(w3, sender.address, amt+300000000000000)
    return transfer_tx(w3, sender.address, receiver.address, amt), sender

def generate_signed_txs(w3, num):
    txs = []
    for _ in range(num):
        tx, sender = generate_tx(w3)
        signed_tx = sign_tx(w3, tx, sender)
        txs.append(signed_tx)
    return txs

def make_bundle(signed_txs):
    bundle = []
    for signed_tx in signed_txs:
        bundle.append({
            "signed_transaction": signed_tx.rawTransaction,
        })
    return bundle

def send_bundle(w3, bundle, block=None, wait=True):
    if block is None:
        block = w3.eth.blockNumber + 5
    print(f"sending bundle {bundle} for block {block}")
    result = w3.flashbots.send_bundle(bundle, target_block_number=block)
    if wait:
        result.wait()
        receipts = result.receipts()
        print(f"bundle receipts {receipts}")
    return block

Hx = Fq(0xbc4f48d7a8651dc97ae415f0b47a52ef1a2702098202392b88bc925f6e89ee17)
Hy = Fq(0x361b27b55c10f94ec0630b4c7d28f963221a0031632092bf585825823f6e27df)
H = Point(curve, Hx, Hy)

def make_pedersen_commitment(x, rnd_bytes=os.urandom):

    r = uint256_from_str(rnd_bytes(32))
    C = x * G + r * H
    return bytes_to_int(hex_to_bytes(ser(C))), r

def compute_pedersen_commitment(x, r):
    C = x * G + r * H
    return bytes_to_int(hex_to_bytes(ser(C)))

def bytes_to_int(x):
    return int.from_bytes(x, 'big')

def int_to_bytes(x):
    return x.to_bytes((x.bit_length() + 7) // 8, 'big')

def str_to_bytes(st):
    return bytes(st, encoding='utf-8')

def hex_to_bytes(hx):
    return bytes.fromhex(hx)

def deserialize_signed_tx(st):
    data = eval(st)
    return SignedTransaction(
        rawTransaction=HexBytes(data['rawTransaction']),
        hash=HexBytes(data['hash']),
        r=data['r'],
        s=data['s'],
        v=data['v'],
    )

def serialize_signed_tx(signed_tx):
    print(signed_tx)
    return str({
        'rawTransaction': signed_tx.rawTransaction.hex(),
        'hash': signed_tx.hash.hex(),
        'r': signed_tx.r,
        's': signed_tx.s,
        'v': signed_tx.v,
    })

def serialize_tx_list(tx_list):
    serialized_tx_list = list()
    for tx in tx_list:
        serialized_tx_list.append(serialize_signed_tx(tx))
    return bytes(str(serialized_tx_list), 'utf-8')

def deserialize_tx_list(serialized_tx_list):
    serialized_tx_list = eval(serialized_tx_list)
    tx_list = list()
    for serialized_tx in serialized_tx_list:
        tx_list.append(deserialize_signed_tx(serialized_tx))
    return tx_list

def recover_tx(raw_tx):
    tx_bytes = HexBytes(raw_tx)
    tx = Transaction.from_bytes(tx_bytes)
    return tx