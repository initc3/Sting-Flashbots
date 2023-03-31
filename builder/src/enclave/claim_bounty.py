import os 

from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
from Crypto.PublicKey import RSA

from utils import asym_encrypt, Block, local_url, fetch_preimage, str_to_bytes, instantiate_contract

relayer_key_location = f'/input/relayer_key.pem'
output_block_path = f'/output/enc_block.txt'

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

def get_account(w3, account_name):
    path = f'/input/{account_name}'
    for filename in os.listdir(path):
        with open(f'{path}/{filename}', 'r') as keyfile:
            encrypted_key = keyfile.read()
            private_key = w3.eth.account.decrypt(encrypted_key, '')
            account = w3.eth.account.privateKeyToAccount(private_key)
            return account


def warp_encrypted_block(preimage, w3, contract, account, relayer_public_key):
    tx = build_tx(contract.functions.claimBounty(preimage), w3, account.address)
    print(f'tx {tx}')
    signed_tx = sign_tx(tx, w3, account)
    print(f'signed_tx {signed_tx}')

    tx_list = [signed_tx]
    block = Block(tx_list)
    return asym_encrypt(str_to_bytes(block.serialize()), relayer_public_key)

def ecall_claim_bounty():
    relayer_public_key = RSA.import_key(open(relayer_key_location).read())
    print(f"relayer_public_key {relayer_public_key}")
    w3 = Web3(HTTPProvider(local_url))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    account = get_account(w3, 'sting')
    contract = instantiate_contract("Honeypot", w3)
    preimage = fetch_preimage()
    
    block =  warp_encrypted_block(preimage, w3, contract, account, relayer_public_key)
    print("block", block)
    with open(output_block_path, "w") as f:
        f.write(f"{block}")
    print(f"sting_addr {account.address}")

ecall_claim_bounty()