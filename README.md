### Build docker image
```
docker-compose build
```

### Create docker container and enter the container environment
```
mkdir data
docker-compose up -d
docker-compose exec dev bash
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


### Test with malicious relayer steal the preimage and replace the bounty claim tx
```
bash chain/chain.sh
python3 -m src.builder.sting.setup_bounty
python3 -m src.builder.sting.claim_bounty
python3 -m src.relayer.malicious
```