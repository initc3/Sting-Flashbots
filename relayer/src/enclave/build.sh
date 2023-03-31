#!/usr/bin/env bash

make clean
make SGX=1 DEBUG=0 RA_TYPE=epid RA_CLIENT_SPID=$RA_CLIENT_SPID RA_CLIENT_LINKABLE=0

exit 0 