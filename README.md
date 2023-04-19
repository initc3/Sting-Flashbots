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

> **Note**: To run in simulation mode, substitute add `--file docker-compose-sim.yml`
to the `docker compose` commands., e.g.:
> ```console
> docker compose --file docker-compose-sim.yml build
> ```

### Build docker image

```
docker compose build
```

## Run demo
> **Note**: To run in simulation mode, substitute add `--file docker-compose-sim.yml`
to the `docker compose` commands., e.g.:
> ```console
> docker compose --file docker-compose-sim.yml build
> ```

### Create docker containers for blockchain network, builder, and relayer

```
docker compose up -d
```

### Enter Relayer container

```
docker compose exec relayer bash
```

### Enter Builder container in *seperate terminal*

```
docker compose exec builder bash
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
docker compose exec eth ./chain/chain.sh
docker compose exec relayer ./setup.sh
docker compose exec builder ./run.sh
```


```
docker compose exec relayer ./malicious.sh
```
