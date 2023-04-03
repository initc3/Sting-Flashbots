#!/usr/bin/env python3

from eth_utils import keccak
from eth_abi import encode

from utils import sample, int_to_bytes, sealed_preimage_localtion, puzzle_path

output_location = f'/output/puzzle.txt'

def ecall_create_puzzle():
    preimage = sample()
    print(f'preimage: {preimage}')

    puzzle = keccak(encode(['uint'], [preimage]))
    print(f'puzzle {puzzle}')

    bytes_preimage = int_to_bytes(preimage)
    with open(sealed_preimage_localtion, 'w') as f:
        f.write(f'{bytes_preimage}')

    with open(output_location, "wb") as f:
        f.write(puzzle)
    with open(puzzle_path, "wb") as f:
        f.write(puzzle)

ecall_create_puzzle()