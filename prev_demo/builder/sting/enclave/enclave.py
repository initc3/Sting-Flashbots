import random

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from eth_abi import encode_single
from eth_utils import keccak
from prev_demo.utils import build_tx, sign_tx, Block, str_to_bytes, bytes_to_int, int_to_bytes, asym_encrypt

sealed_preimage_localtion = f'src/builder/sting/enclave/sealed_preimage.txt'
key_location = f'src/builder/sting/enclave/key.txt'


def sample():
    return random.randint(0, 10000)


def get_sym_key():
    try:
        with open(key_location, 'r') as f:
            key = eval(f.readline())
    except Exception as e:
        key = get_random_bytes(16)
        with open(key_location, 'w') as f:
            f.write(str(key))
    return key


def sym_encrypt(plaintext, key):
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    return cipher.nonce, tag, ciphertext


def sym_decrypt(ciphertext, key):
    nonce, tag, ciphertext = ciphertext
    cipher = AES.new(key, AES.MODE_EAX, nonce)
    return cipher.decrypt_and_verify(ciphertext, tag)


def create_puzzle():
    preimage = sample()
    print(f'preimage: {preimage}')

    puzzle = keccak(encode_single('uint', preimage))
    print(f'puzzle {puzzle}')

    bytes_preimage = int_to_bytes(preimage)
    key = get_sym_key()
    sealed_preimage = sym_encrypt(bytes_preimage, key)

    with open(sealed_preimage_localtion, 'w') as f:
        f.write(f'{sealed_preimage}')

    return puzzle


def fetch_preimage():
    key = get_sym_key()

    with open(sealed_preimage_localtion, 'r') as f:
        sealed_preimage = eval(f.readline())
        preimage = bytes_to_int(sym_decrypt(sealed_preimage, key))
        print(f'preimage: {preimage}')
        return preimage


def claim_bounty(w3, contract, account, relayer_public_key):
    preimage = fetch_preimage()
    return warp_encrypted_block(preimage, w3, contract, account, relayer_public_key)


def warp_encrypted_block(preimage, w3, contract, account, relayer_public_key):
    tx = build_tx(contract.functions.claimBounty(preimage), w3, account.address)
    print(f'tx {tx}')
    signed_tx = sign_tx(tx, w3, account)
    print(f'signed_tx {signed_tx}')

    tx_list = [signed_tx]
    block = Block(tx_list)
    return asym_encrypt(str_to_bytes(block.serialize()), relayer_public_key)
