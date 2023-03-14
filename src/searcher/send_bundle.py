### Source: https://github.com/flashbots/web3-flashbots/blob/master/examples/simple.py

import os

from src.searcher.flashbots import flashbot
from uuid import uuid4
from web3 import Web3, HTTPProvider
from web3.exceptions import TransactionNotFound
from web3.types import TxParams


CHAIN_ID = 5


def get_balance(w3, addr):
    balance = w3.eth.get_balance(addr)
    print(f'balance of {addr} is {Web3.fromWei(balance, "ether")} ether')
    return balance


def get_account(w3, account_name):
    path = f'keystores/{account_name}'
    for filename in os.listdir(path):
        with open(f'{path}/{filename}', 'r') as keyfile:
            encrypted_key = keyfile.read()
            private_key = w3.eth.account.decrypt(encrypted_key, '')
            account = w3.eth.account.privateKeyToAccount(private_key)
            return account


w3 = Web3(HTTPProvider('https://goerli.infura.io/v3/6a82d2519efb4d748c02552e02e369c1'))
signer = get_account(w3, 'signer')
get_balance(w3, signer.address)

sender = get_account(w3, 'sender')
get_balance(w3, sender.address)

receiver = get_account(w3, 'receiver')
get_balance(w3, receiver.address)

flashbot(w3, signer, "https://relay-goerli.flashbots.net")

nonce = w3.eth.get_transaction_count(sender.address)
tx1 = {
    "to": receiver.address,
    "value": Web3.toWei(0.001, "ether"),
    "gas": 21000,
    "maxFeePerGas": Web3.toWei(200, "gwei"),
    "maxPriorityFeePerGas": Web3.toWei(50, "gwei"),
    "nonce": nonce,
    "chainId": CHAIN_ID,
    "type": 2,
}
tx1_signed = sender.sign_transaction(tx1)

tx2 = {
    "to": receiver.address,
    "value": Web3.toWei(0.001, "ether"),
    "gas": 21000,
    "maxFeePerGas": Web3.toWei(200, "gwei"),
    "maxPriorityFeePerGas": Web3.toWei(50, "gwei"),
    "nonce": nonce + 1,
    "chainId": CHAIN_ID,
    "type": 2,
}

bundle = [
    {"signed_transaction": tx1_signed.rawTransaction},
    {"signer": sender, "transaction": tx2},
]

# keep trying to send bundle until it gets mined
while True:
    block = w3.eth.block_number
    print(f"Simulating on block {block}")
    # simulate bundle on current block
    try:
        w3.flashbots.simulate(bundle, block)
        print("Simulation successful.")
    except Exception as e:
        print("Simulation error:", e)
        break

    # send bundle targeting next block
    print(f"Sending bundle targeting block {block+1}")
    replacement_uuid = str(uuid4())
    print(f"replacementUuid {replacement_uuid}")
    send_result = w3.flashbots.send_bundle(
        bundle,
        target_block_number=block + 1,
        opts={"replacementUuid": replacement_uuid},
    )
    print("bundleHash", w3.toHex(send_result.bundle_hash()))

    stats_v1 = w3.flashbots.get_bundle_stats(
        w3.toHex(send_result.bundle_hash()), block
    )
    print("bundleStats v1", stats_v1)

    stats_v2 = w3.flashbots.get_bundle_stats_v2(
        w3.toHex(send_result.bundle_hash()), block
    )
    print("bundleStats v2", stats_v2)

    send_result.wait()
    try:
        receipts = send_result.receipts()
        print(f"\nBundle was mined in block {receipts[0].blockNumber}\a")
        break
    except TransactionNotFound:
        print(f"Bundle not found in block {block+1}")
        # essentially a no-op but it shows that the function works
        cancel_res = w3.flashbots.cancel_bundles(replacement_uuid)
        print(f"canceled {cancel_res}")

get_balance(w3, sender.address)
get_balance(w3, receiver.address)
