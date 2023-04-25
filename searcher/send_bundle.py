### Source: https://github.com/flashbots/web3-flashbots/blob/master/examples/simple.py

from eth_account import Account
from eth_account.signers.local import LocalAccount
from flashbots import flashbot
from uuid import uuid4
from web3 import Web3, HTTPProvider
from web3.exceptions import TransactionNotFound
from web3.middleware import construct_sign_and_send_raw_middleware, geth_poa_middleware
from utils import refill_ether
import os 
import socket

GAS_LIMIT = 1000000
CHAIN_ID = 32382
admin: LocalAccount = Account.from_key("0x2e0834786285daccd064ca17f1654f67b4aef298acbb82cef9ec422fb4975622")
#os.environ.get("ETH_SIGNER_KEY"))
sender: LocalAccount = Account.from_key("0x741c58d0a4d9a76279a30538d647000797306885431b34469ecb749396d4ff52")
receiver: LocalAccount = Account.from_key("0x30481460b2af32f533ba27e32cae4af4c67a96c1856dba6be719ad90d9699814")

# w3 = Web3(HTTPProvider('https://goerli.infura.io/v3/6a82d2519efb4d748c02552e02e369c1'))
# w3 = Web3(HTTPProvider(f"http://{socket.gethostbyname('builder')}:8545"))
# w3 = Web3(HTTPProvider(f"http://builder:8545"))
w3 = Web3(HTTPProvider(f"http://localhost:8545"))

w3.middleware_onion.inject(geth_poa_middleware, layer=0)
print("latest block",w3.eth.get_block('latest')['number'])

w3.middleware_onion.add(construct_sign_and_send_raw_middleware(sender))
w3.middleware_onion.add(construct_sign_and_send_raw_middleware(receiver))
print(f'balance of admin {admin.address} is {w3.eth.get_balance(admin.address)}')
print(f'balance of sender {sender.address} is {w3.eth.get_balance(sender.address)}')
refill_ether(w3, admin, sender.address)
# print(f'balance of sender {sender.address} is {w3.eth.get_balance(sender.address)}')



# fund_sender_tx = admin.sign_transaction({
#     'to': sender.address,
#     'from': admin.address,
#     'value': 100 * 10**18,
#     "gasPrice": w3.eth.gas_price,
#     'gas': GAS_LIMIT,
#     'nonce': w3.eth.get_transaction_count(sender.address),
#     'chainId': CHAIN_ID,
# })
# w3.eth.send_raw_transaction(fund_sender_tx)
# print(w3.eth.wait_for_transaction_receipt(fund_sender_tx.hash, w3))
# print(f'balance of sender {sender.address} is {w3.eth.get_balance(sender.address)}')


# flashbot(w3, signer, "https://relay-goerli.flashbots.net")
flashbot(w3, admin)

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

print(f'balance of sender {sender.address} is {w3.eth.get_balance(sender.address)}')
print(f'balance of receiver {receiver.address} is {w3.eth.get_balance(receiver.address)}')