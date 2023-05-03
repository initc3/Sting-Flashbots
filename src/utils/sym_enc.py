from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


key_length = 16


def get_sym_key(key_location):
    try:
        with open(key_location, 'r') as f:
            key = eval(f.readline())
    except Exception as e:
        key = get_random_bytes(key_length)
        with open(key_location, 'w') as f:
            f.write(str(key))
    return key


def sym_encrypt(plaintext, key):
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    return cipher.nonce, tag, ciphertext


def sym_decrypt(ciphertext, key):
    nonce, tag, ciphertext = ciphertext
    cipher = AES.new(key, AES.MODE_EAX, nonce)
    return cipher.decrypt_and_verify(ciphertext, tag)
