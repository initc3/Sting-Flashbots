#!/usr/bin/env bash

set -e
if [[ "$SGX" == 1 ]]; then
    GRAMINE="gramine-sgx"
else
    GRAMINE="gramine-direct"
fi
gramine-sgx-sigstruct-view --output-format json geth.sig > /shared/builder_enclave.json

$GRAMINE ./geth
