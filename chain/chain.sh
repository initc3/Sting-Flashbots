#!/usr/bin/env bash

set -e
set -x

KEYSTORE=chain/keystores/admin
POADIR=chain/poa
DATADIR=$POADIR/data

pkill -f geth || true
pkill -f python || true

sleep 1

rm -rf $DATADIR
mkdir $DATADIR

geth --datadir $DATADIR init $POADIR/genesis.json

geth \
    --datadir $DATADIR \
    --keystore $KEYSTORE \
    --unlock 0 \
    --mine --allow-insecure-unlock \
    --password $POADIR/empty_password.txt \
    --http \
    --http.addr 0.0.0.0 \
    --http.corsdomain '*' \
    --http.api admin,debug,eth,miner,net,personal,shh,txpool,web3 \
    --ws \
    --ws.addr 0.0.0.0 \
    --ws.origins '*' \
    --ws.api admin,debug,eth,miner,net,personal,shh,txpool,web3 \
    --syncmode full \
    --ipcpath "$DATADIR/geth.ipc" \
    2>> $DATADIR/geth.log &

sleep 5