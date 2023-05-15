#!/usr/bin/env bash

set -e
if [[ "$SGX" == 1 ]]; then
    GRAMINE="gramine-sgx"
else
    GRAMINE="gramine-direct"
fi

$GRAMINE ./geth