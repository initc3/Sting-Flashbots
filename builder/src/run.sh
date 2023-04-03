#!/usr/bin/env bash

set -e
set -x

./build.sh

if [[ "$SGX" == 1 ]]; then
    GRAMINE=gramine-sgx
else
    GRAMINE=gramine-direct
fi

cd /Sting-Flashbots/builder/src/

make reset

cp /Sting-Flashbots/chain/build/contracts/Honeypot.json /Sting-Flashbots/builder/input_data/Honeypot.json
cp -r /Sting-Flashbots/chain/keystores/sting/ /Sting-Flashbots/builder/input_data/sting/


$GRAMINE ./python ./enclave/create_puzzle.py

# === SGX quote ===
if [[ "$SGX" == 1 ]]; then
    $GRAMINE ./python ./enclave/sgx-report.py &> OUTPUT
    grep -q "Generated SGX report" OUTPUT && echo "[ Success SGX report ]"
    $GRAMINE ./python ./enclave/sgx-quote.py &>> OUTPUT
    grep -q "Extracted SGX quote" OUTPUT && echo "[ Success SGX quote ]"
    make SGX=1 check
fi 

python3 -m setup_bounty

cp /shared_data/relayer_key.pem /Sting-Flashbots/builder/input_data/relayer_key.pem
$GRAMINE ./python ./enclave/claim_bounty.py | tee CLAIM_BOUNTY
cp /Sting-Flashbots/builder/output_data/enc_block.txt /shared_data/enc_block.txt

if [[ "$SGX" == 1 ]]; then
    cat OUTPUT
fi
cat CLAIM_BOUNTY | grep sting_addr
echo "done"

