from enclave.utils import *


def make_bundle_stinger(w3, signed_txs):
    k = sample(2**256)
    print(f'use {k} as nonce in ECDSA signature')

    unsigned_stinger_tx, sender = generate_tx(w3)
    signed_stinger_tx = sign_tx(w3, unsigned_stinger_tx, sender, k)
    print(f'generate stinger tx {signed_stinger_tx}')

    signed_txs.append(signed_stinger_tx)
    bundle = make_bundle(signed_txs)
    print(f'sending stinger bundle {bundle}')

    target_block_num = w3.eth.blockNumber + 5
    send_bundle(w3, bundle, SEARCHER_KEY.address, block=target_block_num, wait=False)

    stinger_data = {
        'target_block_num': target_block_num,
        'stinger_tx_hash': signed_stinger_tx.hash.hex(),
    }
    print('stinger_data', stinger_data)
    json.dump(stinger_data, open(stinger_data_path, 'w'))
    open(stinger_tx_path, "wb").write(signed_stinger_tx.rawTransaction)


if __name__ == '__main__':
    print('========================================================================= create_stinger')

    w3 = get_web3()
    make_bundle_stinger(w3, signed_txs=[])

    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
