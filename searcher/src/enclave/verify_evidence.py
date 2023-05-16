import json 


from utils import *

def verify_evidence(w3):
    verify_data = json.load(open(verify_data_path))
    target_block_num = verify_data["target_block_num"]
    r = verify_data["r"]
    stinger_bundle_hashes = verify_data["stinger_bundle_hashes"]
    unsigned_adv_tx = verify_data["unsigned_adv_tx"]
    sender = Account.from_key(verify_data["sender"])

    print(f'verify_evidence target_block_num {target_block_num}')
    print(f'verify_evidence stinger_bundle_hashes {stinger_bundle_hashes}')

    target_block = w3.eth.get_block(target_block_num)
    print(f'verify_evidence target_block {target_block}')
    tx_hashes = list(map(lambda x: bytes(x.hex(), 'utf-8') if x.hex() in stinger_bundle_hashes else b'' , target_block['transactions']))
    print(f'verify_evidence tx_hashes {tx_hashes}')
    leak_data_hash = bytes_to_int(keccak(b''.join(tx_hashes)))
    print(f'verify_evidence leak_data_hash {leak_data_hash}')

    C = compute_pedersen_commitment(leak_data_hash, r)
    print(f'make_evidence use commitment {C} as k in signature')
    adv_tx_computed = sign_tx(w3, unsigned_adv_tx, sender, k=C)
    print(f'verify_evidence adv_tx_computed {adv_tx_computed}')
    assert(adv_tx_computed.hash in target_block['transactions'])
    adv_tx_block = w3.eth.get_transaction(adv_tx_computed.hash)
    print(f'verify_evidence adv_tx_block {adv_tx_block}')

    assert(adv_tx_block.v == adv_tx_computed.v)
    assert(adv_tx_block.r.hex() == hex(adv_tx_computed.r))
    assert(adv_tx_block.s.hex() == hex(adv_tx_computed.s))
    print("target block hash", target_block["hash"].hex())
    with open(verify_info_path, "wb") as f:
        f.write(bytes(target_block["hash"]))

if __name__ == '__main__':
    w3 = get_web3()
    verify_evidence(w3)


