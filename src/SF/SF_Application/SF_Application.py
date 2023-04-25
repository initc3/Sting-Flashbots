from src.utils.asym_enc import asym_encrypt
from src.utils.sym_enc import get_sym_key, sym_encrypt


_sealed_data_location = f'src/SF/SF_Application/sealed_data.txt'
_key_location = f'src/SF/SF_Application/key.pem'


def _store_secret(secret):
    key = get_sym_key(_key_location)
    sealed_data = sym_encrypt(secret, key)

    with open(_sealed_data_location, 'w') as f:
        f.write(f'{sealed_data}')


def generate_stinger(func, args, target_public_key):
    e, s = func(args)
    _store_secret(e)
    return asym_encrypt(s, target_public_key)


def generate_proof():
    pass