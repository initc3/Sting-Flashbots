#!/usr/bin/env bash

cd /Sting-Flashbots/relayer/src/
make clean
make SGX=$SGX DEBUG=$DEBUG RA_TYPE=epid RA_CLIENT_SPID=$RA_CLIENT_SPID RA_CLIENT_LINKABLE=0
