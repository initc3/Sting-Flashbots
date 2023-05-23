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

# === SGX quote ===
if [[ "$SGX" == 1 ]]; then
    $GRAMINE ./enclave/sgx-report.py &> OUTPUT
    grep -q "Generated SGX report" OUTPUT && echo "[ Success SGX report ]"
    $GRAMINE ./enclave/sgx-quote.py &>> OUTPUT
    grep -q "Extracted SGX quote" OUTPUT && echo "[ Success SGX quote ]"
    cat OUTPUT
    gramine-sgx-ias-request report --msb --api-key $RA_TLS_EPID_API_KEY --quote-path "${OUTPUT_PATH}/quote" --report-path ias.report --sig-path ias.sig -v
fi

python setup_bounty.py setup_bounty_contract
python setup_bounty.py submit_enclave
python setup_bounty.py approve_enclave


$GRAMINE enclave/create_stinger.py

set +x
while [ -z "$(ls -A /shared )" ]
do  
    sleep 2
done
set -x

mv /shared/* "${INPUT_PATH}/leak/"
$GRAMINE ./enclave/make_evidence.py 
$GRAMINE ./enclave/verify_evidence.py 


python setup_bounty.py collect_bounty

rm -rf "${INPUT_PATH}/leak/*"

echo "done"