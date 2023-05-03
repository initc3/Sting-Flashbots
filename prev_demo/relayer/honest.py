from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware

from prev_demo.relayer.enclave.enclave import deliver_block
from prev_demo.utils import local_url

if __name__ == '__main__':

    w3 = Web3(HTTPProvider(local_url))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    with open(f'data/sealed_block.txt', 'r') as f:
        encrypted_block = eval(f.readline())

    deliver_block(w3, encrypted_block)
