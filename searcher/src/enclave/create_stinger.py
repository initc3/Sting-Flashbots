import time

from enclave.utils import *


# def private_order_flow(w3, num_txs):
#     keys = os.environ.get("POF_KEYS")
#     if keys is not None and keys != "":
#         print("POF_KEYS", keys)
#         keys = json.loads(keys)
#         senders = [get_account(w3, pk) for pk in keys]
#     else:
#         senders = None
#     return generate_signed_txs(w3, num_txs, senders=senders, gas_price=w3.eth.gas_price * GAS_MUL)


def make_bundle_stinger(w3):
    k = sample(2**256)
    # print(f'use {k} as nonce in ECDSA signature')

    bundle = json.load(open(sting_bundle_path))
    for i in range(len(bundle)):
        bundle[i]["signed_transaction"] = HexBytes(bundle[i]["signed_transaction"])
    unsigned_stinger_tx = json.load(open(sting_tx_path))
    stinger_sender = get_account(w3, os.environ.get("STINGER_PK"))
    signed_stinger_tx = sign_tx(w3, unsigned_stinger_tx, stinger_sender, k)
    bundle.append({
            "signed_transaction": signed_stinger_tx.rawTransaction
    })

    # print(f'stinger_sender {stinger_sender.address}')

    # print(f'sending stinger bundle {bundle}')

    target_block_num = w3.eth.blockNumber + 3

    # bundles = []
    # for _ in range(1, PREC_BUNDLE):
    #     bundle_txs = private_order_flow(w3, POF_TXS)
    #     bundles.append(make_bundle(bundle_txs))
    #
    # for b in bundles:
    #     print('*')
    #     send_bundle(w3, b, ADMIN_ACCOUNT.address, block=target_block_num, wait=False)

    send_bundle(w3, bundle, SEARCHER_KEY.address, block=target_block_num, wait=False)

    with open('/Sting-Flashbots/searcher/src/benchmark/benchmark_latency_critical_loop.csv', 'a') as f:
        f.write(f"{time.time()}\n")

    # print(f'SEARCHER_KEY.address {SEARCHER_KEY.address}')

    for i in range(len(bundle)):
        bundle[i]["signed_transaction"] = bundle[i]["signed_transaction"].hex()

    stinger_data = {
        'target_block_num': target_block_num,
        'stinger_tx_hash': signed_stinger_tx.hash.hex(),
        'sting_bundle': bundle
    }
    # print('stinger_data', stinger_data)
    json.dump(stinger_data, open(stinger_data_path, 'w'))
    open(stinger_tx_path, "wb").write(signed_stinger_tx.rawTransaction)


if __name__ == '__main__':
    # print('========================================================================= create_stinger')

    start = perf_counter()

    w3 = get_web3()
    make_bundle_stinger(w3)

    end = perf_counter()
    print(f'{end - start}')

    # print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
