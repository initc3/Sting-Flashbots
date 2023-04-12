
def str_to_bytes(st):
    return bytes(st, encoding='utf-8')


def bytes_to_str(bt):
    return bt.decode(encoding='utf-8')


def bytes_to_int(x):
    return int.from_bytes(x, 'big')


def int_to_bytes(x):
    return x.to_bytes((x.bit_length() + 7) // 8, 'big')


def bytes_to_hex(bt):
    return '0x' + bt.hex()


def hex_to_bytes(hx):
    return bytes.fromhex(hx)
