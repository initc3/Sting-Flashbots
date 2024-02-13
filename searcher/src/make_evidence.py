from enclave.lib.mkp.proveth import generate_proof_blob
from enclave.utils import *


def make_evidence(w3):

    stinger_data = json.load(open(stinger_data_path))

    tx_filepath = os.path.join(subversionservice_path, stinger_data['stinger_tx_hash'])

    with open(tx_filepath, 'rb') as f:
        buff = f.read()

    raw_transaction = buff.hex()
    leaked_tx = decode_raw_tx(w3, raw_transaction)
    # print(f'leaked_tx {leaked_tx}')

    leaked_tx_sig_hash = keccak(b''.join([int_to_bytes(leaked_tx.v), str_to_bytes(leaked_tx.r), str_to_bytes(leaked_tx.s)]))
    # print(f'make commitment to leaked_tx_hash {leaked_tx_sig_hash}')

    C, r = make_pedersen_commitment(bytes_to_int(leaked_tx_sig_hash))
    # print(f'use commitment {C} as nonce in ECDSA signature')
    # unsigned_adv_tx, adv_sender = generate_tx(w3, sender=None, gas_price=w3.eth.gas_price * GAS_MUL * 2)

    adv_sender = setup_new_account(w3)
    receiver = setup_new_account(w3)
    amt = sample(10000)
    unsigned_adv_tx = transfer_tx(w3, adv_sender.address, receiver.address, amt=amt, gas_price=w3.eth.gas_price * GAS_MUL * 2)

    refill_tx = transfer_tx(w3, ADMIN_ACCOUNT.address, adv_sender.address, amt=amt+int(3e18))
    signed_refill_tx = sign_tx(w3, refill_tx, ADMIN_ACCOUNT)

    # print(f'unsigned_adv_tx {unsigned_adv_tx}')
    signed_adv_tx = sign_tx(w3, unsigned_adv_tx, adv_sender, k=C)

    # print(f'signed_adv_tx {signed_adv_tx}')
    # new_bundle = stinger_data['sting_bundle']
    # for i in range(len(new_bundle)):
    #     new_bundle[i]["signed_transaction"] = HexBytes(new_bundle[i]["signed_transaction"])
    # new_bundle.append({
    #         "signed_transaction": signed_adv_tx.rawTransaction
    # })
    new_bundle = list()
    new_bundle.append({
        "signed_transaction": signed_refill_tx.rawTransaction
    })
    new_bundle.append({
        "signed_transaction": signed_adv_tx.rawTransaction
    })
    # print(f'current block {w3.eth.block_number}')
    target_block_num = stinger_data['target_block_num']

    # print(f'target block {target_block_num}')
    assert w3.eth.block_number < target_block_num
    # target_block_num = w3.eth.blockNumber + 2

    with open('benchmark/benchmark_latency_critical_loop.csv', 'a') as f:
        f.write(f"{time.time()}\n")

    send_bundle(w3, new_bundle, adv_sender.address, block=target_block_num)

    victim_receipt = w3.eth.get_transaction_receipt(leaked_tx.hash)
    print(f'victim_receipt {victim_receipt}')
    adv_receipt = w3.eth.get_transaction_receipt(signed_adv_tx.hash)
    print(f'adv_receipt {adv_receipt}')

    return
    victim_prf = generate_proof_blob(w3, victim_receipt['blockNumber'], victim_receipt['transactionIndex'])
    adv_prf = generate_proof_blob(w3, adv_receipt['blockNumber'], adv_receipt['transactionIndex'])

    verify_data = {
        'r': r,
        'adv_private_key': adv_sender.privateKey.hex(),
        'target_block_num': target_block_num,
        'adv_prf': adv_prf.hex(),
        'victim_prf': victim_prf.hex(),
    }
    print(f'verify_data {verify_data}')
    json.dump(verify_data, open(verify_data_path, 'w'))


if __name__ == '__main__':
    print('========================================================================= making_evidence')

    w3 = get_web3()
    make_evidence(w3)

    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
