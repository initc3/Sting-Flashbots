# Sting-Flashbots

## Prerequisites

### Set Intel IAS SPID

```
export RA_CLIENT_SPID=<spid>
export RA_TYPE=<dcap or epid>
export RA_CLIENT_LINKABLE=<0 or 1>
export RA_TLS_EPID_API_KEY=<api key>
```

or add it in a `.env` file, at the root of this repository, e.g.:

```env
# .env file
RA_CLIENT_SPID=0123456789abcdefghijklmnopqrstuv
RA_TYPE=dcap
RA_CLIENT_LINKABLE=0
RA_TLS_EPID_API_KEY=vutsrqponmlkjihgfedcba9876543210
```

### Set SGX driver environment variables
Set `SGX_DRIVER` and `GRAMINE_IMG_TAG` in your `.env` file or via `export` statements.

For the out-of-tree (legacy) driver set `SGX_DRIVER` to `oot`, and for the in-kernel
(dcap) driver set `SGX_DRIVER` to `inkernel`.

The `GRAMINE_IMG_TAG` refers to the tag of an image hosted at
https://github.com/initc3/docker-gramine/pkgs/container/gramine. For instance, to use
`ghcr.io/initc3/gramine:dcap-f160357` set `GRAMINE_IMG_TAG` to `dcap-f160357`.

**Example of a `.env` file for the out-of-tree driver:**

```env
# .env file
SGX_DRIVER=oot
GRAMINE_IMG_TAG=legacy-f160357
```

**Example of a `.env` file for the in-kernel driver:**

```env
# .env file
SGX_DRIVER=inkernel
GRAMINE_IMG_TAG=dcap-f160357
```

### Running in SGX Simulation mode or without SGX

**To run in simulation mode, set in `.env` or environment**

```env
# .env file
SGX=0
```

**To run without SGX use `docker-compose-nosgx.yml` file**

Add `--file docker-compose-nosgx.yml` to the `docker compose` commands., e.g.:
```
docker compose --file docker-compose-nosgx.yml build
```


### Build docker image

```
docker compose build 
```

## Run demo

### Create docker containers for blockchain network, builder, and relayer

```
docker compose up -d
```

### Look at Searcher container logs

```
docker compose logs -f searcher 
```

### Stop containers and delete volumes

```
docker compose down -v
```

## Running on Sepolia

### Setup 

* Add Sepolia private keys and address to `.env` file

```env
# .env file
...
SEARCHER_ADDRESS=<address for $SEARCHER_KEY>
SEARCHER_KEY=<Sepolia account private key for searcher>
STINGER_KEY=<Another Sepolia account private key for sending the stinger>
POF_KEYS=[<list of Sepolia account private keys to use for private order flow transaction simulations>] #optional
```

* Generate jwt secret 

```bash
mkdir -p sepolia
openssl rand -hex 32 | sudo tee ./sepolia/jwtsecret
```

## Running on Sepolia without SGX

* build images for Sepolia

```bash
docker compose -f docker-compose-sepolia-nosgx.yml build
```

* Start containers
```bash
docker compose -f docker-compose-sepolia-nosgx.yml up -d
```

* Look at searcher logs

```bash
docker compose -f docker-compose-sepolia-nosgx.yml logs -f searcher 
```

* Delete containers and volume

```bash
docker compose -f docker-compose-sepolia-nosgx.yml down -v
```

## Running on Sepolia with SGX

### Download network snapshot

* Build non-sgx docker containers for downloading snapshot

```bash
docker compose -f docker-compose-nosgx.yml build builder beacon-chain
```

* create docker network 

```bash
docker network create sting-sync-net
```

* Set environment variables for an account 

```env
export PRIVATE_KEY=<private key for account with balance on Sepolia>
```

* start builder

```bash
docker run --publish 8551:8551 --publish 8545:8545 --net sting-sync-net --name builder \
  -e BUILDER_SECRET_KEY=$PRIVATE_KEY \
  -e BUILDER_TX_SIGNING_KEY=$PRIVATE_KEY \
  -v $PWD/sepolia:/root/sepolia  \
  --rm flashbots-builder:local --sepolia \
  --http --http.api=engine,eth,web3,net,debug,flashbots \
  --http.corsdomain=* \
  --http.addr=0.0.0.0 \
  --ws --ws.api=engine,eth,web3,net,debug \
  --authrpc.jwtsecret=/root/sepolia/jwtsecret \
  --authrpc.vhosts=* --authrpc.addr=0.0.0.0 \
  --datadir=/root/sepolia/synced
```

* start beacon-chain (in seperate terminal)

```bash
docker run --publish 4000:4000 --publish 3500:3500 --publish 8080:8080 --net sting-sync-net --name beacon-chain \
  -v $PWD/sepolia:/root/sepolia \
  --rm ghcr.io/initc3/flashbots-prysm:cecd2d9cb \
  --datadir=/root/sepolia/beacondata --sepolia \
  --checkpoint-sync-url=https://sepolia.beaconstate.info \
  --genesis-beacon-api-url=https://sepolia.beaconstate.info \
  --grpc-gateway-host=0.0.0.0 \
  --execution-endpoint=http://builder:8551 \
  --accept-terms-of-use \
  --jwt-secret=/root/sepolia/jwtsecret 
```

* wait for sync to complete

```bash

docker logs builder # | grep "Snap sync complete"
...
...
INFO [06-02|11:18:23.743] Syncing: chain download in progress      synced=100.00% chain=12.23GiB   headers=3,609,948@1.16GiB    bodies=3,609,948@9.37GiB    receipts=3,609,948@1.71GiB    eta=0s
INFO [06-02|11:18:23.743] Snap sync complete, auto disabling 
INFO [06-02|11:18:23.747] Upgrading chain index                    type=bloombits               percentage=0
INFO [06-02|11:18:24.390] New local node record                    seq=1,685,715,593,349 id=9b35988b6158e5af ip=38.65.223.112 udp=30303 tcp=30303
INFO [06-02|11:18:24.396] Resuming state snapshot generation       root=aa662a..06f1ed in=087068..71eb36 at=a1228e..84f3fc accounts=168,867              slots=654,628              storage=59.48MiB dangling=0 elapsed=6.167s        eta=3m0.938s
INFO [06-02|11:18:24.398] Imported new potential chain segment     number=3,609,949 hash=5428a4..d8898d blocks=1   txs=113  mgas=11.586  elapsed=63.766ms      mgasps=181.691 dirty=34.11MiB
INFO [06-02|11:18:24.411] Chain head was updated                   number=3,609,949 hash=5428a4..d8898d root=2d6bc9..202ecf elapsed=2.04271ms
INFO [06-02|11:18:24.411] Entered PoS stage 
...
...
```

* check state root against other sources e.g. [https://checkpoint-sync.sepolia.ethpandaops.io/](https://checkpoint-sync.sepolia.ethpandaops.io/)

```bash
curl -s http://localhost:3500/eth/v1/beacon/headers/finalized | jq .'data.header.message'
```

* stop containers and delete network

```bash
docker stop builder beacon-chain
docker network rm sting-sync-net
```

### Run demo

* add Fake propose to environment (or create a new [geth-sgx-gramine](https://github.com/flashbots/geth-sgx-gramine/tree/main/examples/confidential-builder-boost-relay))

```bash
export FAKE_PROPOSER=$(cat sepolia/validator_data.json)
```

* build images for Sepolia

```bash
docker compose -f docker-compose-sepolia.yml build
```

* if you have less than 64G memory on the machine increase the swap file size to 64G

* Start containers

```bash
docker compose -f docker-compose-sepolia.yml up -d
```

* Look at searcher logs

```bash
docker compose -f docker-compose-sepolia.yml logs -f searcher 
```

* Delete containers and volume

```bash
docker compose -f docker-compose-sepolia.yml down -v
```