#!/usr/bin/env bash

set -e
set -x

./build.sh

if [[ "$SGX" == 1 ]]; then
    GRAMINE=gramine-sgx
else
    GRAMINE=gramine-direct
fi

cd /Sting-Flashbots/relayer/src/

make reset

cp /Sting-Flashbots/chain/build/contracts/Honeypot.json /Sting-Flashbots/relayer/input_data/Honeypot.json
cp -r /Sting-Flashbots/chain/keystores/relayer/ /Sting-Flashbots/relayer/input_data/relayer/

$GRAMINE ./python ./enclave/gen_key.py

# === SGX quote ===
if [[ "$SGX" == 1 ]];
then
    $GRAMINE ./python ./enclave/sgx-report.py &> OUTPUT
    grep -q "Generated SGX report" OUTPUT && echo "[ Success SGX report ]"
    $GRAMINE ./python ./enclave/sgx-quote.py &>> OUTPUT
    grep -q "Extracted SGX quote" OUTPUT && echo "[ Success SGX quote ]"
    make SGX=$SGX check
fi

cp /Sting-Flashbots/relayer/output_data/relayer_key.pem /shared_data/relayer_key.pem

if [[ "$SGX" == 1 ]];
then
    cat OUTPUT
fi 

echo "done"
