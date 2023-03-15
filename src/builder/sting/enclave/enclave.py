import random

from eth_abi import encode_single
from eth_utils import keccak
from src.utils import build_tx, sign_tx, Block, encrypt, decrypt, str_to_bytes, get_public_key, get_private_key, bytes_to_int, int_to_bytes


sealed_preimage_localtion = f'src/builder/sting/enclave/sealed_preimage.txt'
sealed_key_location = f'src/builder/sting/enclave/private_key.txt'


def sample():
    return random.randint(0, 10000)


def create_puzzle():
    preimage = sample()
    print(f'preimage: {preimage}')

    puzzle = keccak(encode_single('uint', preimage))
    print(f'puzzle {puzzle}')

    ### TODO: replace it w/ a symmetric encryption scheme
    public_key = get_public_key(sealed_key_location)
    sealed_preimage = encrypt(int_to_bytes(preimage), public_key)

    with open(sealed_preimage_localtion, 'w') as f:
        f.write(f'{sealed_preimage}')

    return puzzle


def fetch_preimage():
    private_key = get_private_key(sealed_key_location)

    with open(sealed_preimage_localtion, 'r') as f:
        sealed_preimage = eval(f.readline())
        preimage = bytes_to_int(decrypt(sealed_preimage, private_key))
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
    return encrypt(str_to_bytes(block.serialize()), relayer_public_key)
