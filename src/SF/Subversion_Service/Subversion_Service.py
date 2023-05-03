from src.utils.asym_enc import get_private_key, target_key_path


def leak_data(func, s):
    private_key = get_private_key(target_key_path)
    return func(s, private_key)


def tamper():
    pass
