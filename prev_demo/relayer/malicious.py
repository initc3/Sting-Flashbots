from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
from prev_demo.builder.sting.enclave.enclave import warp_encrypted_block
from prev_demo.relayer.enclave.enclave import deliver_block, steal_preimage
from prev_demo.utils import local_url, instantiate_contract, get_account, refill_ether, get_public_key, relayer_key_path


def wrap_new_block(w3, preimage):
    contract = instantiate_contract('Honeypot', w3)
    relayer_account = get_account(w3, 'relayer')
    refill_ether(w3, relayer_account.address)
    relayer_public_key = get_public_key(relayer_key_path)
    return warp_encrypted_block(preimage, w3, contract, relayer_account, relayer_public_key)


if __name__ == '__main__':

    w3 = Web3(HTTPProvider(local_url))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    with open(f'data/sealed_block.txt', 'r') as f:
        encrypted_block = eval(f.readline())

    preimage = steal_preimage(encrypted_block)

    deliver_block(w3, wrap_new_block(w3, preimage))
