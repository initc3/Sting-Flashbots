#!/usr/bin/env bash

set -e
set -x
NUM_TRAILS=5

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


cd /Sting-Flashbots/searcher/src/
for i in $(eval echo "{1..$NUM_TRAILS}")
do


    rm -rf /shared/0x*

        start=`date +%s.%N`
    $GRAMINE -m enclave.gen_signing_key
        end=`date +%s.%N`
        runtime_gen_signing_key=$( echo "$end - $start" | bc -l )
        echo "$i,gen_signing_key,$runtime_gen_signing_key\n" >> benchmark_latency.csv

    # === SGX quote ===
    if [[ "$SGX" == 1 ]]; then
            start=`date +%s.%N`
        $GRAMINE -m enclave.sgx-report &> OUTPUT
            end=`date +%s.%N`
            runtime_gen_enclave_report=$( echo "$end - $start" | bc -l )
            echo "$i,gen_enclave_report,$runtime_gen_enclave_report\n" >> benchmark_latency.csv

        grep -q "Generated SGX report" OUTPUT && echo "[ Success SGX report ]"

            start=`date +%s.%N`
        $GRAMINE -m enclave.sgx-quote &>> OUTPUT
            end=`date +%s.%N`
            runtime_gen_enclave_quote=$( echo "$end - $start" | bc -l )
            echo "$i,gen_enclave_quote,$runtime_gen_enclave_quote\n" >> benchmark_latency.csv

        grep -q "Extracted SGX quote" OUTPUT && echo "[ Success SGX quote ]"

        cat OUTPUT

            start=`date +%s.%N`
        gramine-sgx-ias-request report --api-key $RA_TLS_EPID_API_KEY --quote-path "${OUTPUT_PATH}/quote" --report-path ias.report --sig-path ias.sig -c ias.cert -v
            end=`date +%s.%N`
            runtime_ias_proof=$( echo "$end - $start" | bc -l )
            echo "$i,ias_proof,$runtime_ias_proof\n" >> benchmark_latency.csv
    fi

    cd /Sting-Flashbots/searcher/solidity/
    rm -rf ./build
    truffle compile
    cd /Sting-Flashbots/searcher/src

    python -m setup_bounty setup_bounty_contract
    python -m setup_bounty submit_enclave

    rm -rf ${INPUT_PATH}/leak/*

    python -m setup_bounty generate_bundle

        start=`date +%s.%N`
    $GRAMINE -m enclave.create_stinger
        end=`date +%s.%N`
        runtime_create_stinger=$( echo "$end - $start" | bc -l )
        echo "$i,create_stinger,$runtime_create_stinger\n" >> benchmark_latency.csv

    set +x
    while [ -z "$(ls -A /shared/0x* )" ]
    do  
        sleep 2
    done
    set -x

    mv /shared/0x* "${INPUT_PATH}/leak/"

    python -m make_evidence

        start=`date +%s.%N`
    $GRAMINE -m enclave.verify_evidence
        end=`date +%s.%N`
        runtime_verify_evidence=$( echo "$end - $start" | bc -l )
        echo "$i,verify_evidence,$runtime_verify_evidence\n" >> benchmark_latency.csv


    python -m setup_bounty collect_bounty
done 

rm -rf ${INPUT_PATH}/leak/*

echo "done"
cat benchmark_latency.csv
cat benchmark_gas.csv
