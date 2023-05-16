import json 
import os 
from utils import *

def make_evidence(w3):
    stinger_data = json.load(open(stinger_data_path))
    target_block= stinger_data["target_block"]
    subv_files = os.listdir(subversionservice_path)
    leaked_txs = []
    for file in subv_files:
        tx_filepath = os.path.join(subversionservice_path, file)
        with open(tx_filepath, "rb") as f:
            buff = f.read()
        raw_transaction = buff.hex()
        tx = decode_raw_tx(w3, raw_transaction)
        if tx['hash'].hex() == stinger_data["stinger_hash"]:
            leaked_txs.append(tx)
            print("read subversion service path",tx_filepath)

    print("leaked_txs", leaked_txs)
    tx_hashes = []
    for tx in leaked_txs:
        tx_hashes.append(bytes(tx['hash'].hex(), 'utf-8'))
    print(f'make_evidence tx_hashes {tx_hashes}')
    leak_data_hash = bytes_to_int(keccak(b''.join(tx_hashes)))
    print(f'make_evidence leak_data_hash {leak_data_hash}')

    C, r = make_pedersen_commitment(leak_data_hash)

    print(f'make_evidence use commitment {C} as k in signature')

    unsigned_adv_tx, sender = generate_tx(w3)
    adv_tx = sign_tx(w3, unsigned_adv_tx, sender, k=C)
    print(f'make_evidence adv_tx {adv_tx}')

    new_bundle = make_bundle([adv_tx])


    verify_data = {
        "r": r,
        "target_block_num": target_block,
        "stinger_bundle_hashes": list(map(lambda x: x.decode('utf-8'), tx_hashes)),
        "unsigned_adv_tx": unsigned_adv_tx,
        "sender": sender.privateKey.hex()
    }
    print("verify_data", verify_data)
    print("currect block", w3.eth.block_number)
    assert w3.eth.block_number < target_block
    json.dump(verify_data, open(verify_data_path, "w"))

    send_bundle(w3, new_bundle, block=target_block)

    return new_bundle, r, sender, tx_hashes, unsigned_adv_tx

if __name__ == '__main__':
    w3 = get_web3()
    make_evidence(w3)


