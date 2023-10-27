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

if [[ "$TLS" == "1" ]]; then
    echo "Waiting for builder cert..."

    if [ -z "$(ls -A /cert )" ]; then
        sleep 60
    fi
    set +x
    while [ -z "$(ls -A /cert )" ]
    do
        sleep 2
    done
    set -x

    cp /cert/tlscert.der "${INPUT_PATH}/tlscert.der"
    cp /shared/builder_enclave.json builder_enclave.json
    export RA_TLS_MRENCLAVE=$(cat builder_enclave.json | jq -r .mr_enclave )
fi

rm -rf /shared/0x*

cd /Sting-Flashbots/searcher/src/

$GRAMINE -m enclave.gen_signing_key

# === SGX quote ===
if [[ "$SGX" == 1 ]]; then
    $GRAMINE -m enclave.sgx-report &> OUTPUT
    grep -q "Generated SGX report" OUTPUT && echo "[ Success SGX report ]"
    $GRAMINE -m enclave.sgx-quote &>> OUTPUT
    grep -q "Extracted SGX quote" OUTPUT && echo "[ Success SGX quote ]"
    cat OUTPUT
    gramine-sgx-ias-request report --api-key $RA_TLS_EPID_API_KEY --quote-path "${OUTPUT_PATH}/quote" --report-path ias.report --sig-path ias.sig -c ias.cert -v
fi

cd /Sting-Flashbots/searcher/solidity/
rm -rf ./build
truffle compile
cd /Sting-Flashbots/searcher/src

python -m setup_bounty setup_bounty_contract
python -m setup_bounty submit_enclave

rm -rf ${INPUT_PATH}/leak/*

python -m setup_bounty generate_bundle

$GRAMINE -m enclave.create_stinger

set +x
while [ -z "$(ls -A /shared/0x* )" ]
do  
    sleep 2
done
set -x

mv /shared/0x* "${INPUT_PATH}/leak/"

python -m make_evidence
$GRAMINE -m enclave.verify_evidence

python -m setup_bounty collect_bounty

rm -rf ${INPUT_PATH}/leak/*

echo "done"
