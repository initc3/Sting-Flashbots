### Set Intel IAS SPID

```
export RA_CLIENT_SPID=<spid>
```

### Build docker image

```
docker compose -f docker-compose-builder-relayer.yml build 
```

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