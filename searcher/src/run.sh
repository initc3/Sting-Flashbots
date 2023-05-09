#!/usr/bin/env bash

set -e
set -x

if [[ "$SGX" == 1 ]]; then
    GRAMINE=gramine-sgx
else
    GRAMINE=gramine-direct
fi
mkdir -p /Sting-Flashbots/searcher/input_data/leak/

cd /Sting-Flashbots/searcher/src/enclave/


# $GRAMINE ./python ./enclave/main.py & 
python main.py &
PID=$!

while [ -z "$(ls -A /shared )" ]
do  
    sleep 2
done
mv /shared/* /Sting-Flashbots/searcher/input_data/leak/

wait $PID
echo "done"