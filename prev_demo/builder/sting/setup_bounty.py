<<<<<<<< HEAD:builder/src/setup_bounty.py
#!/usr/bin/env python3

========
from prev_demo.builder.sting.enclave.enclave import create_puzzle
from prev_demo.utils import get_account, parse_contract, local_url, refill_ether, transact, ether_unit
>>>>>>>> origin/searcher-builder:prev_demo/builder/sting/setup_bounty.py
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware

from utils import local_url, get_account, parse_contract, refill_ether, transact, ether_unit


puzzle_location = f'/Sting-Flashbots/builder/output_data/puzzle.txt'


if __name__ == '__main__':

    w3 = Web3(HTTPProvider(local_url))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    sting_account = get_account(w3, 'sting')
    refill_ether(w3, sting_account.address)
    with open(puzzle_location, "rb") as f:
        puzzle = f.read()
    bounty = int(0.5 * ether_unit)
    abi, bytecode = parse_contract('Honeypot')
    receipt = transact(w3.eth.contract(
        abi=abi,
        bytecode=bytecode
    ).constructor(puzzle), w3, sting_account, bounty, k=123)
    contract_addr = receipt['contractAddress']
    print(f'Deployed to: {contract_addr}')

