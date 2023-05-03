from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
from chain import claim_bounty
from prev_demo.utils import local_url, get_account, refill_ether, instantiate_contract, get_public_key, relayer_key_path


if __name__ == '__main__':

    w3 = Web3(HTTPProvider(local_url))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    contract = instantiate_contract('Honeypot', w3)

    sting_account = get_account(w3, 'sting')
    refill_ether(w3, sting_account.address)

    relayer_public_key = get_public_key(relayer_key_path)
    encrypted_block = claim_bounty(w3, contract, sting_account, relayer_public_key)
    with open(f'data/sealed_block.txt', 'w') as f:
        f.write(f'{encrypted_block}')
