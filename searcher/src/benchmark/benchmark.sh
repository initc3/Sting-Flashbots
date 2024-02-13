#!/usr/bin/env bash

set -e
set -x
NUM_TRAILS=10
#NUM_TRAILS=1
#SGX=-1

if [[ "$SGX" == 1 ]]; then
    GRAMINE="gramine-sgx ./python"
elif [[ "$SGX" == -1 ]]; then
    GRAMINE="python"
else
    GRAMINE="gramine-direct ./python"
fi

make clean
make SGX=$SGX RA_CLIENT_LINKABLE=$RA_CLIENT_LINKABLE DEBUG=$DEBUG RA_TYPE=$RA_TYPE RA_CLIENT_SPID=$RA_CLIENT_SPID

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


#    rm -rf /shared/0x*
#
#        start=`date +%s.%N`
#    echo "$i,gen_signing_key,$($GRAMINE -m enclave.gen_signing_key)" >> benchmark/benchmark_latency_pure_python.csv
#        end=`date +%s.%N`
#        runtime_gen_signing_key=$( echo "$end - $start" | bc -l )
#        echo "$i,gen_signing_key,$runtime_gen_signing_key" >> benchmark/benchmark_latency.csv
#
#
#    # === SGX quote ===
#    if [[ "$SGX" == 1 ]]; then
#            start=`date +%s.%N`
##        $GRAMINE -m enclave.sgx-report &> OUTPUT
#        echo "$i,gen_enclave_report,$($GRAMINE -m enclave.sgx-report)" >> benchmark/benchmark_latency_pure_python.csv
#            end=`date +%s.%N`
#            runtime_gen_enclave_report=$( echo "$end - $start" | bc -l )
#            echo "$i,gen_enclave_report,$runtime_gen_enclave_report" >> benchmark/benchmark_latency.csv
#
##        grep -q "Generated SGX report" OUTPUT && echo "[ Success SGX report ]"
#
#            start=`date +%s.%N`
##        $GRAMINE -m enclave.sgx-quote &>> OUTPUT
#        echo "$i,gen_enclave_quote,$($GRAMINE -m enclave.sgx-quote)" >> benchmark/benchmark_latency_pure_python.csv
#            end=`date +%s.%N`
#            runtime_gen_enclave_quote=$( echo "$end - $start" | bc -l )
#            echo "$i,gen_enclave_quote,$runtime_gen_enclave_quote" >> benchmark/benchmark_latency.csv
#
##        grep -q "Extracted SGX quote" OUTPUT && echo "[ Success SGX quote ]"
#
##        cat OUTPUT
#
#            start=`date +%s.%N`
#        gramine-sgx-ias-request report --api-key $RA_TLS_EPID_API_KEY --quote-path "${OUTPUT_PATH}/quote" --report-path ias.report --sig-path ias.sig -c ias.cert -v
#            end=`date +%s.%N`
#            runtime_ias_proof=$( echo "$end - $start" | bc -l )
#            echo "$i,ias_proof,$runtime_ias_proof" >> benchmark_latency.csv
#    fi
#
#    cd /Sting-Flashbots/searcher/src
#
#    if [[ "$SGX" == 1 ]]; then
#        python -m setup_bounty setup_bounty_contract
#        python -m setup_bounty submit_enclave
#    fi

    rm -rf ${INPUT_PATH}/leak/*

    echo "$i," >> benchmark/benchmark_latency_critical_loop.csv

    python -m setup_bounty generate_bundle

        start=`date +%s.%N`
#    $GRAMINE -m enclave.create_stinger
    echo "$i,create_stinger,$($GRAMINE -m enclave.create_stinger)" >> benchmark/benchmark_latency_pure_python.csv
        end=`date +%s.%N`
        runtime_create_stinger=$( echo "$end - $start" | bc -l )
        echo "$i,create_stinger,$runtime_create_stinger" >> benchmark/benchmark_latency.csv

#        critical_loop_start=`date +%s.%N`

    set +x
    while [ -z "$(ls -A /shared/0x* )" ]
    do
        sleep 0.01
    done
    set -x
#        critical_loop_end=`date +%s.%N`
#        runtime_critical_loop=$( echo "$critical_loop_end - $critical_loop_start" | bc -l )
#        echo "$i,critical_loop,$runtime_critical_loop" >> benchmark/benchmark_latency_critical_loop.csv
#

    mv /shared/0x* ${INPUT_PATH}/leak/

    python -m make_evidence

    sleep 5

#        start=`date +%s.%N`
##    $GRAMINE -m enclave.verify_evidence
#    echo "$i,verify_evidence,$($GRAMINE -m enclave.verify_evidence)" >> benchmark/benchmark_latency_pure_python.csv
#        end=`date +%s.%N`
#        runtime_verify_evidence=$( echo "$end - $start" | bc -l )
#        echo "$i,verify_evidence,$runtime_verify_evidence" >> benchmark/benchmark_latency.csv
#
#    if [[ "$SGX" == 1 ]]; then
#        python -m setup_bounty collect_bounty
#    fi

done

#rm -rf ${INPUT_PATH}/leak/*

echo "done"