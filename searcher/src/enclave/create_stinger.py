import json
from utils import *

def make_bundle_stinger(w3, signed_txs):
    print("make_bundle")
    k = sample()
    print(f'use randomly sampled k {k} in signature')
    
    stinger_tx, sender = generate_tx(w3)
    signed_stinger_tx = sign_tx(w3, stinger_tx, sender)
    print(f"generate stinger tx {signed_stinger_tx}")
    signed_txs.append(signed_stinger_tx)
    bundle = make_bundle(signed_txs)
    print(f"sending stinger bundle {bundle}")
    target_block = w3.eth.blockNumber+15
    send_bundle(w3, bundle, block=target_block, wait=False)
    stinger_data = {
        "target_block": target_block,
        "stinger_hash": signed_stinger_tx["hash"].hex(),
    }
    print("stinger_data", stinger_data)
    json.dump(stinger_data, open(stinger_data_path, "w"))
    print("target_block", target_block)

if __name__ == '__main__':
    w3 = get_web3()
    make_bundle_stinger(w3, [])


