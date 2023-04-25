from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes


target_key_path = 'src/SF/Targer_Application'


def gen_keypair(key_path):
    key = RSA.generate(2048)
    private_key = key.export_key()
    with open(f'{key_path}/private.pem', 'wb') as f:
        f.write(private_key)

    public_key = key.publickey().export_key()
    with open(f'{key_path}/receiver.pem', 'wb') as f:
        f.write(public_key)

    return key, key.publickey()


def get_private_key(key_path):
    try:
        private_key = RSA.import_key(open(f'{key_path}/private.pem').read())
    except Exception as _:
        private_key, _ = gen_keypair(key_path)

    return private_key


def get_public_key(key_path):
    try:
        recipient_key = RSA.import_key(open(f'{key_path}/receiver.pem').read())
    except Exception as _:
        _, recipient_key = gen_keypair(key_path)

    return recipient_key

def asym_encrypt(plaintext, recipient_key):
    session_key = get_random_bytes(16)

    # Encrypt the session key with the public RSA key
    cipher_rsa = PKCS1_OAEP.new(recipient_key)
    enc_session_key = cipher_rsa.encrypt(session_key)

    # Encrypt the data with the AES session key
    cipher_aes = AES.new(session_key, AES.MODE_EAX)
    ciphertext, tag = cipher_aes.encrypt_and_digest(plaintext)

    return enc_session_key, cipher_aes.nonce, tag, ciphertext


def asym_decrypt(ciphertext, private_key):
    enc_session_key, nonce, tag, ciphertext = ciphertext

    # Decrypt the session key with the private RSA key
    cipher_rsa = PKCS1_OAEP.new(private_key)
    session_key = cipher_rsa.decrypt(enc_session_key)

    # Decrypt the data with the AES session key
    cipher_aes = AES.new(session_key, AES.MODE_EAX, nonce)
    return cipher_aes.decrypt_and_verify(ciphertext, tag)
