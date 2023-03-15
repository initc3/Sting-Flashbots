from src.utils import get_private_key, bytes_to_str, Block, bytes_to_int, hex_to_bytes, relayer_key_path, asym_decrypt


def decrypt_block(encrypted_block):
    private_key = get_private_key(relayer_key_path)
    return Block.deserialize(bytes_to_str(asym_decrypt(encrypted_block, private_key)))


def deliver_block(w3, encrypted_block):
    decrypt_block(encrypted_block).apply(w3)


def steal_preimage(encrypted_block):
    block = decrypt_block(encrypted_block)
    for signed_tx in block.tx_list:
        raw_tx = signed_tx.rawTransaction.hex()
        hex_preimage = raw_tx[80: 80+64]
        preimage = bytes_to_int(hex_to_bytes(hex_preimage))
        return preimage


