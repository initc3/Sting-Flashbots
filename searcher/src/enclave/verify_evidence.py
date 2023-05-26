import json 

from lib.mkp.proveth import verify_tx_proof
from utils import *


def verify_evidence(w3):
    verify_data = json.load(open(verify_data_path))
    unsigned_adv_tx, signed_adv_tx = verify_tx_proof(w3, verify_data['target_block_num'], hex_to_bytes(verify_data['adv_prf']))
    print(f'unsigned_adv_tx {unsigned_adv_tx}')
    print(f'signed_adv_tx {signed_adv_tx}')
    _, signed_victim_tx = verify_tx_proof(w3, verify_data['target_block_num'], hex_to_bytes(verify_data['victim_prf']))

    r = verify_data['r']
    C = compute_pedersen_commitment(bytes_to_int(signed_victim_tx.hash), r)
    print(f'make_evidence use commitment {C} as nonce in signature')

    adv_account = Account.from_key(verify_data['adv_private_key'])
    adv_tx_computed = sign_tx(w3, unsigned_adv_tx, adv_account, k=C)
    print(f'adv_tx_computed {adv_tx_computed}')

    assert(signed_adv_tx.v == adv_tx_computed.v)
    assert(signed_adv_tx.r == adv_tx_computed.r)
    assert(signed_adv_tx.s == adv_tx_computed.s)

    target_block = w3.eth.get_block(verify_data['target_block_num'])
    print('target block hash', target_block.hash.hex())

    proof = bytes(target_block.hash) + verify_data['target_block_num'].to_bytes(32, 'big')
    secret_key = open(secret_key_path, "rb").read()
    sig = sign_eth_data(w3, secret_key, proof)
    print("sig",sig)
    print("proof",proof)
    open(os.path.join(output_dir, "proof"), "wb").write(proof)
    open(os.path.join(output_dir, "proof.sig"), "wb").write(sig)

if __name__ == '__main__':
    print('verify_evidence =========================================================================')

    w3 = get_web3()
    verify_evidence(w3)
