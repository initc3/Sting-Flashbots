#!/usr/bin/env bash

set -e
set -x

if [[ "$SGX" == 1 ]]; then
    GRAMINE=gramine-sgx
else
    GRAMINE=gramine-direct
fi

INPUT_PATH=/Sting-Flashbots/searcher/input_data

mkdir -p "${INPUT_PATH}/leak/"

while [ -z "$(ls -A /cert )" ]
do  
    sleep 2
done
rm -rf /shared/*

cp /cert/tlscert.der "${INPUT_PATH}/tlscert.der"

cd /Sting-Flashbots/searcher/src/

$GRAMINE ./python ./enclave/create_stinger.py 

# set +x
while [ -z "$(ls -A /shared )" ]
do  
    sleep 2
done
# set -x

mv /shared/* "${INPUT_PATH}/leak/"
$GRAMINE ./python ./enclave/make_evidence.py 
$GRAMINE ./python ./enclave/verify_evidence.py 
# $GRAMINE ./python ./enclave/sgx-quote.py 
# $GRAMINE ./python ./enclave/sgx-report.py 

echo "done"