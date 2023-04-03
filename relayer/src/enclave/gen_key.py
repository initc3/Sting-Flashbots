#!/usr/bin/env python3

from utils import relayer_public_key_path, relayer_private_key_path

from Crypto.PublicKey import RSA

def ecall_gen_private_key():
    key = RSA.generate(2048)
    private_key = key.export_key()
    with open(relayer_private_key_path, 'wb') as f:
        f.write(private_key)

    public_key = key.publickey().export_key()
    # print(f"relayer_public_key {public_key}")
    with open(relayer_public_key_path, 'wb') as f:
        f.write(public_key)

ecall_gen_private_key()
