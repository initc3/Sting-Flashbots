### Build docker image
```
docker-compose build
```

### Create docker container and enter the container environment
```
docker-compose up -d
docker exec -it sting-flashbots-dev-1 bash
```

### Compile Solidity contracts in `chain/contracts`
```
bash chain/compile.sh
```

### Start localnet
```
bash chain/chain.sh
```

### Deploy Honeypot contract and setup puzzle
```
python3 -m src.builder.sting.setup_bounty
```

### Create bounty claim tx and wrap in an encrypted block
```
python3 -m src.builder.sting.claim_bounty
```

### Honest relayer deliver the block picked
```
python3 -m src.relayer.honest
```


### Malicious relayer steal the preimage and replace the bounty claim tx
```
python3 -m src.relayer.malicious
```