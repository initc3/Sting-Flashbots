import itertools

from eth_account._utils.legacy_transactions import Transaction, UNSIGNED_TRANSACTION_FIELDS
from eth_account.datastructures import SignedTransaction
from hexbytes import HexBytes


def serialize_signed_tx(signed_tx):
    return str({
        'rawTransaction': signed_tx.rawTransaction.hex(),
        'hash': signed_tx.hash.hex(),
        'r': signed_tx.r,
        's': signed_tx.s,
        'v': signed_tx.v,
    })


def deserialize_signed_tx(st):
    data = eval(st)
    return SignedTransaction(
        rawTransaction=HexBytes(data['rawTransaction']),
        hash=HexBytes(data['hash']),
        r=data['r'],
        s=data['s'],
        v=data['v'],
    )


def serialize_tx_list(tx_list):
    serialized_tx_list = list()
    for tx in tx_list:
        serialized_tx_list.append(serialize_signed_tx(tx))
    return str(serialized_tx_list)


def deserialize_tx_list(serialized_tx_list):
    serialized_tx_list = eval(serialized_tx_list)
    tx_list = list()
    for serialized_tx in serialized_tx_list:
        tx_list.append(deserialize_signed_tx(serialized_tx))
    return tx_list


def recover_tx(raw_tx):
    tx_bytes = HexBytes(raw_tx)
    tx = Transaction.from_bytes(tx_bytes)
    return tx


def strip_signature(tx):
    return dict(itertools.islice(tx.as_dict().items(), len(UNSIGNED_TRANSACTION_FIELDS)))
