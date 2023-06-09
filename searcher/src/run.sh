#!/usr/bin/env bash

set -e
set -x

if [[ "$SGX" == 1 ]]; then
    GRAMINE="gramine-sgx ./python"
elif [[ "$SGX" == -1 ]]; then
    GRAMINE="python"
else
    GRAMINE="gramine-direct ./python"
fi

INPUT_PATH=/Sting-Flashbots/searcher/input_data
OUTPUT_PATH=/Sting-Flashbots/searcher/output_data

mkdir -p "${INPUT_PATH}/leak/"

if [[ "$SGX" != "-1" ]]; then
    echo "Waiting for builder cert..."

    if [ -z "$(ls -A /cert )" ]; then 
        sleep 350
    fi
    set +x
    while [ -z "$(ls -A /cert )" ]
    do  
        sleep 2
    done
    set -x

    cp /cert/tlscert.der "${INPUT_PATH}/tlscert.der"
fi 

rm -rf /shared/*

cd /Sting-Flashbots/searcher/src/

$GRAMINE -m enclave.gen_signing_key

# === SGX quote ===
if [[ "$SGX" == 1 ]]; then
    $GRAMINE -m enclave.sgx-report &> OUTPUT
    grep -q "Generated SGX report" OUTPUT && echo "[ Success SGX report ]"
    $GRAMINE -m enclave.sgx-quote &>> OUTPUT
    grep -q "Extracted SGX quote" OUTPUT && echo "[ Success SGX quote ]"
    cat OUTPUT
    gramine-sgx-ias-request report --api-key $RA_TLS_EPID_API_KEY --quote-path "${OUTPUT_PATH}/quote" --report-path ias.report --sig-path ias.sig
fi

python -m setup_bounty setup_bounty_contract
python -m setup_bounty submit_enclave
python -m setup_bounty approve_enclave

rm -rf ${INPUT_PATH}/leak/*

python -m setup_bounty generate_bundle

$GRAMINE -m enclave.create_stinger

set +x
while [ -z "$(ls -A /shared )" ]
do  
    sleep 2
done
set -x

mv /shared/* "${INPUT_PATH}/leak/"

python -m make_evidence
$GRAMINE -m enclave.verify_evidence

python -m setup_bounty collect_bounty

rm -rf ${INPUT_PATH}/leak/*

echo "done"
