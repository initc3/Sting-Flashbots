from enclave.utils import *


def gen_signingKey(w3):
    signing_account = setup_new_account(get_web3())

    with open(secret_key_path, "wb") as f:
        f.write(bytes(signing_account.privateKey))
    with open(os.path.join(output_dir, "enclave_address"), "w") as f:
        f.write(signing_account.address)

    print(f'enclave_addr {signing_account.address}')


if __name__ == '__main__':
    print('========================================================================= generating_signing_key')

    w3 = get_web3()
    gen_signingKey(w3)

    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
