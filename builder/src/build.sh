#!/usr/bin/env bash

cd /Sting-Flashbots/builder/src/
make clean
make SGX=${SGX} DEBUG=$DEBUG RA_TYPE=${RA_TYPE} RA_CLIENT_SPID=$RA_CLIENT_SPID RA_CLIENT_LINKABLE=0
