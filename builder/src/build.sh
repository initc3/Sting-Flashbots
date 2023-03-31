#!/usr/bin/env bash

cd /Sting-Flashbots/builder/src/
make clean
make SGX=1 DEBUG=$DEBUG RA_TYPE=epid RA_CLIENT_SPID=$RA_CLIENT_SPID RA_CLIENT_LINKABLE=0
