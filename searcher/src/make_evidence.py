from lib.mkp.proveth import generate_proof_blob
from utils import *


def make_evidence(w3):
    stinger_data = json.load(open(stinger_data_path))

    subv_files = os.listdir(subversionservice_path)
    for file in subv_files:
        tx_filepath = os.path.join(subversionservice_path, file)
        with open(tx_filepath, 'rb') as f:
            buff = f.read()
        raw_transaction = buff.hex()
        tx = decode_raw_tx(w3, raw_transaction)
        if tx['hash'].hex() == stinger_data['stinger_tx_hash']:
            leaked_tx = tx
            break
    print(f'leaked_tx {leaked_tx}')

    leaked_tx_sig_hash = keccak(b''.join([int_to_bytes(leaked_tx.v), str_to_bytes(leaked_tx.r), str_to_bytes(leaked_tx.s)]))
    print(f'make commitment to leaked_tx_hash {leaked_tx_sig_hash}')

    C, r = make_pedersen_commitment(bytes_to_int(leaked_tx_sig_hash))
    print(f'use commitment {C} as nonce in ECDSA signature')

    unsigned_adv_tx, sender = generate_tx(w3, w3.eth.gas_price * 10)
    print(f'unsigned_adv_tx {unsigned_adv_tx}')
    signed_adv_tx = sign_tx(w3, unsigned_adv_tx, sender, k=C)
    print(f'signed_adv_tx {signed_adv_tx}')
    new_bundle = make_bundle([signed_adv_tx])

    print(f'currect block {w3.eth.block_number}')
    target_block_num = stinger_data['target_block_num']
    print(f'target block {target_block_num}')
    assert w3.eth.block_number < target_block_num

    send_bundle(w3, new_bundle, SEARCHER_KEY.address, block=target_block_num)

    adv_receipt = w3.eth.get_transaction_receipt(signed_adv_tx.hash)
    print(f'adv_receipt {adv_receipt}')
    adv_prf = generate_proof_blob(w3, adv_receipt['blockNumber'], adv_receipt['transactionIndex'])

    victim_receipt = w3.eth.get_transaction_receipt(leaked_tx.hash)
    print(f'victim_receipt {victim_receipt}')
    victim_prf = generate_proof_blob(w3, victim_receipt['blockNumber'], victim_receipt['transactionIndex'])

    verify_data = {
        'r': r,
        'adv_private_key': sender.privateKey.hex(),
        'target_block_num': target_block_num,
        'adv_prf': adv_prf.hex(),
        'victim_prf': victim_prf.hex(),
    }
    print(f'verify_data {verify_data}')
    json.dump(verify_data, open(verify_data_path, 'w'))


if __name__ == '__main__':
    print('========================================================================= generating_signing_key')

    w3 = get_web3()
    make_evidence(w3)

    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
