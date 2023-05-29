from lib.mkp.proveth import verify_tx_proof
from utils import *


def verify_evidence(w3):
    verify_data = json.load(open(verify_data_path))
    unsigned_adv_tx, signed_adv_tx = verify_tx_proof(w3, verify_data['target_block_num'], hex_to_bytes(verify_data['adv_prf']))
    print(f'unsigned_adv_tx {unsigned_adv_tx}')
    print(f'signed_adv_tx {signed_adv_tx}')
    _, signed_victim_tx = verify_tx_proof(w3, verify_data['target_block_num'], hex_to_bytes(verify_data['victim_prf']))
    print(f'signed_victim_tx {signed_victim_tx}')

    r = verify_data['r']
    C = compute_pedersen_commitment(bytes_to_int(keccak(b''.join([int_to_bytes(signed_victim_tx.v), str_to_bytes(hex((signed_victim_tx.r))), str_to_bytes(hex(signed_victim_tx.s))]))), r)
    print(f'make_evidence use commitment {C} as nonce in signature')

    adv_account = Account.from_key(verify_data['adv_private_key'])
    adv_tx_computed = sign_tx(w3, unsigned_adv_tx, adv_account, k=C)
    print(f'adv_tx_computed {adv_tx_computed}')

    assert(signed_adv_tx.v == adv_tx_computed.v)
    assert(signed_adv_tx.r == adv_tx_computed.r)
    assert(signed_adv_tx.s == int(hex(adv_tx_computed.s), 16))

    target_block = w3.eth.get_block(verify_data['target_block_num'])
    print('target block hash', target_block.hash.hex())

    proof_blob = rlp.encode([
         verify_data['target_block_num'],
         target_block.hash,
    ])
    secret_key = open(secret_key_path, "rb").read()
    sig = sign_eth_data(w3, secret_key, proof_blob)
    print(f'proof_sig {sig}')
    open(os.path.join(output_dir, "proof_blob"), "wb").write(proof_blob)
    open(os.path.join(output_dir, "proof_sig"), "wb").write(sig)


if __name__ == '__main__':
    print('verify_evidence =========================================================================')

    w3 = get_web3()
    verify_evidence(w3)
