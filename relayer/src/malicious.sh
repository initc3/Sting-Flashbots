#!/usr/bin/env bash

set -e
set -x

if [[ "$SGX" == 1 ]]; then
    GRAMINE=gramine-sgx
else
    GRAMINE=gramine-direct
fi
cd /Sting-Flashbots/relayer/src/

cp /shared_data/enc_block.txt /Sting-Flashbots/relayer/input_data/enc_block.txt 

python -m refill_ether_relayer

$GRAMINE ./python ./enclave/steal_preimage.py

echo "done"
