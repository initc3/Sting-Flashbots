import os 

from utils import *


def setup(w3, sender, receiver):
    print(f"block {w3.eth.block_number}")
    print(f"sender initial balance: {get_balance(w3, sender.address)}")
    refill_ether(w3, sender.address)
    print(f"sender updated balance: {get_balance(w3, sender.address)}")
    print(f"receiver initial balance: {get_balance(w3, receiver.address)}")
    amt = w3.toWei("0.001", "ether")
    tx = transfer_tx(w3, sender.address, receiver.address, amt)
    signed_tx = sign_tx(w3, tx, sender)
    send_tx(w3, signed_tx)
    print(f"receiver updated balance: {get_balance(w3, receiver.address)}")

def make_bundle_stinger(w3, signed_txs):
    k = sample()
    print(f'use randomly sampled k {k} in signature')
    
    stinger_tx, sender = generate_tx(w3)
    signed_stinger_tx = sign_tx(w3, stinger_tx, sender, k=k)
    print(f"generate stinger tx {signed_stinger_tx}")
    signed_txs.append(signed_stinger_tx)
    bundle = make_bundle(signed_txs)
    print(f"sending stinger bundle {bundle}")
    target_block = w3.eth.blockNumber+5
    send_bundle(w3, bundle, block=target_block, wait=False)
    with open(secret_path, 'wb') as f:
        f.write(int_to_bytes(k))

    with open(subversionservice_path, 'wb') as f: #todo delete and replave with subversion service
        f.write(serialize_tx_list(signed_txs))

    while True:
        try:
            with open(subversionservice_path, "rb") as f:
                leak_data = deserialize_tx_list(f.read())
            break
        except:            pass
    new_bundle, r, sting_sender, stinger_hashes, unsigned_adv_tx = make_evidence(w3, leak_data)
    print(f'sending evidence bundle {new_bundle} in block {target_block} cuurent block {w3.eth.block_number}')
    send_bundle(w3, new_bundle, block=target_block)
    verify_evidence(w3, r, target_block, sting_sender, stinger_hashes, unsigned_adv_tx)

     
def make_evidence(w3, leak_data):
    print(leak_data)
    tx_hashes = []
    for tx in leak_data:
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

    return new_bundle, r, sender, tx_hashes, unsigned_adv_tx

def verify_evidence(w3, r, target_block_num, sender, stinger_bundle_hashes, unsigned_adv_tx):
    print(f'verify_evidence target_block_num {target_block_num}')
    print(f'verify_evidence stinger_bundle_hashes {stinger_bundle_hashes}')

    target_block = w3.eth.get_block(target_block_num)
    print(f'verify_evidence target_block {target_block}')
    tx_hashes = list(map(lambda x: bytes(x.hex(), 'utf-8') if bytes(x.hex(), 'utf-8') in stinger_bundle_hashes else b'' , target_block['transactions']))
    print(f'verify_evidence tx_hashes {tx_hashes}')
    leak_data_hash = bytes_to_int(keccak(b''.join(tx_hashes)))
    print(f'verify_evidence leak_data_hash {leak_data_hash}')

    C = compute_pedersen_commitment(leak_data_hash, r)
    adv_tx_computed = sign_tx(w3, unsigned_adv_tx, sender, k=C)
    print(f'verify_evidence adv_tx_computed {adv_tx_computed}')
    assert(adv_tx_computed.hash in target_block['transactions'])
    adv_tx_block = w3.eth.get_transaction(adv_tx_computed.hash)
    print(f'verify_evidence adv_tx_block {adv_tx_block}')

    assert(adv_tx_block.v == adv_tx_computed.v)
    assert(adv_tx_block.r.hex() == hex(adv_tx_computed.r))
    assert(adv_tx_block.s.hex() == hex(adv_tx_computed.s))


if __name__ == '__main__':
    w3 = get_web3()
    # setup(w3, sender, receiver)
    # bundle_txs = generate_signed_txs(w3, 1)
    # bundle = make_bundle(bundle_txs)
    # send_bundle(w3, bundle)
    make_bundle_stinger(w3, [])


