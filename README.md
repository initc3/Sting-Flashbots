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

### Run demo
```
python3 -m src.apps.searcher_builder.main
```