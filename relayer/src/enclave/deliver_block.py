#!/usr/bin/env python3

from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
from Crypto.PublicKey import RSA

from utils import local_url, decrypt_block, relayer_private_key_path, enc_block_path


def ecall_deliver_block():
    w3 = Web3(HTTPProvider(local_url))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    private_key = RSA.import_key(open(relayer_private_key_path).read())
    with open(enc_block_path, 'r') as f:
        encrypted_block = eval(f.readline())
    decrypt_block(encrypted_block, private_key).apply(w3)

ecall_deliver_block()