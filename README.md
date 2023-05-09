# Sting-Flashbots

## Prerequisites

### Set Intel IAS SPID

```
export RA_CLIENT_SPID=<spid>
```

or add it in a `.env` file, at the root of this repository, e.g.:

```env
# .env file
RA_CLIENT_SPID=0123456789abcdefghijklmnopqrstuv
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
SGX_DRIVER=oot
GRAMINE_IMG_TAG=legacy-f160357
```

**Example of a `.env` file for the in-kernel driver:**

```env
SGX_DRIVER=inkernel
GRAMINE_IMG_TAG=dcap-f160357
```

### Running in SGX mode versus Simulation mode

> **Note**: To run in simulation mode, substitute add `--file docker-compose-sim.yml`
to the `docker compose` commands., e.g.:
> ```console
> docker compose --file docker-compose-sim.yml build
> ```

### Build docker image

```
docker compose -f docker-compose-builder-relayer.yml build 
```

## Run demo
> **Note**: To run in simulation mode, substitute add `--file docker-compose-sim.yml`
to the `docker compose` commands., e.g.:
> ```console
> docker compose --file docker-compose-sim.yml build
> ```

### Create docker containers for blockchain network, builder, and relayer

```
docker compose -f docker-compose-builder-relayer.yml up -d
```

### Enter Relayer container

```
docker compose -f docker-compose-builder-relayer.yml exec relayer bash
```

### Enter Builder container in *seperate terminal*

```
docker compose -f docker-compose-builder-relayer.yml exec builder bash
```


### Generate the relayer public/private key and SGX quote & report
```
./setup.sh
```


### Deploy Honeypot contract and setup puzzle

* Create puzzle
* Setup Honeypot contract
* Claim Bounty

```
./run.sh
```

### Honest relayer delivers the block picked

```
./honest.sh
```


### Malicious relayer steal the preimage and replace the bounty claim tx

*Address of the HoneyPot contract is hardcoded and you can only claim the bounty once so restart the network and rerun the protocol the other relayer*
```
docker compose -f docker-compose-builder-relayer.yml exec eth ./chain/chain.sh
docker compose -f docker-compose-builder-relayer.yml exec relayer ./setup.sh
docker compose -f docker-compose-builder-relayer.yml exec builder ./run.sh
```


```
docker compose -f docker-compose-builder-relayer.yml exec relayer ./malicious.sh
```
