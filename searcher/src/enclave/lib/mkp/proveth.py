### Source: https://raw.githubusercontent.com/lorenzb/proveth/master/offchain/proveth.py

import argparse
import eth
import math

from typing import cast
from eth_typing import Hash32
from eth_hash.auto import (
    keccak,
)
from eth_utils import to_canonical_address, decode_hex, big_endian_to_int, encode_hex
from trie import HexaryTrie
from trie.constants import (
    BLANK_NODE,
    BLANK_NODE_HASH,
    NODE_TYPE_BLANK,
    NODE_TYPE_LEAF,
    NODE_TYPE_EXTENSION,
    NODE_TYPE_BRANCH,
    BLANK_HASH,
)
from trie.utils.nodes import *
from trie.utils.nibbles import encode_nibbles, decode_nibbles, bytes_to_nibbles


MODULE_DEBUG = False
TX_ROOT_HASH_INDEX = 4


def rec_hex(x):
    if isinstance(x, list):
        return [rec_hex(elem) for elem in x]
    else:
        return encode_hex(x)


def rec_bin(x):
    if isinstance(x, list):
        return [rec_bin(elem) for elem in x]
    elif isinstance(x, int):
        return x
    elif isinstance(x, str):
        if x.startswith("0x"):
            if len(x) != 2:
                return utils.decode_hex(x[2:])
            else:
                return 0
        else:
            return utils.decode_hex(x)
    elif x is None:
        return 0


def normalize_bytes(hash):
    if isinstance(hash, str):
        if hash.startswith("0x"):
            hash = hash[2:]
        if len(hash) % 2 != 0:
            hash = '0' + hash
        return decode_hex(hash)
    elif isinstance(hash, int):
        return hash.to_bytes(length=(math.ceil(hash.bit_length() / 8)),
                             byteorder="big",
                             signed=False)
    else:
        return bytes(hash)


def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def get_args():
    parser = argparse.ArgumentParser(
        description="Patricia Merkle Trie Proof Generating Tool",
        formatter_class=argparse.RawTextHelpFormatter)
    # TODO add stuff around adding a block header and then generating proofs of
    # inclusion / exclusion etc etc etc
    blockInfoGroup = parser.add_mutually_exclusive_group(required=True)
    blockInfoGroup.add_argument('-n', '--block-number',
                        default="",
                        help="Block number that transaction exists in")
    blockInfoGroup.add_argument('-b', '--block-hash',
                        default="",
                        help="Block hash that transaction exists in")
    parser.add_argument('-tr', '--transaction_receipt_mode', required=False,
                        type=str2bool, default="False",
                        help="If the proof should be for a transaction receipt")
    parser.add_argument('-i', '--transaction_index', required=True, type=int,
                        default="",
                        help="Zero-based index of the transaction in the "
                        "block (e.g. the third transaction in the block is at "
                        "index 2)")
    parser.add_argument('-r', '--rpc', required=True,
                        default="",
                        help="URL of web3 rpc node. (e.g. "
                        "http://localhost:8545)")
    parser.add_argument('-v', '--verbose', required=False, action='store_true',
                        help="Print verbose output")
    return parser.parse_args()


def block_header(block_dict: dict):
    b = eth.rlp.headers.BlockHeader(
        int(block_dict['difficulty']),
        int(block_dict['number']),
        int(block_dict['gasLimit']),
        int(block_dict['timestamp']),
        to_canonical_address(block_dict["miner"]),
        cast(Hash32, block_dict["parentHash"]),
        cast(Hash32, block_dict["sha3Uncles"]),
        cast(Hash32, block_dict["stateRoot"]),
        cast(Hash32, block_dict["transactionsRoot"]),
        cast(Hash32, block_dict["receiptsRoot"]),
        big_endian_to_int(block_dict["logsBloom"]),
        int(block_dict['gasUsed']),
        normalize_bytes(block_dict["extraData"]),
        cast(Hash32, block_dict["mixHash"]),
        normalize_bytes(block_dict["nonce"]),
        int(block_dict['baseFeePerGas']),
        cast(Hash32, normalize_bytes(block_dict["withdrawalsRoot"] or '')),
    )
    if normalize_bytes(block_dict["hash"]) != b.hash:
        raise ValueError(
            """Blockhash does not match.
            Received invalid block header? {} vs {}""".format(
                str(normalize_bytes(block_dict["hash"]).hex()),
                str(b.hash.hex())))
    return b


def rlp_transaction(tx_dict: dict):
    if tx_dict['type'] == '0x0':
        t = eth.vm.forks.london.transactions.LondonLegacyTransaction(
            tx_dict['nonce'],
            tx_dict['gasPrice'],
            tx_dict['gas'],
            normalize_bytes(tx_dict['to'] or ''),
            tx_dict['value'],
            normalize_bytes(tx_dict['input'] or ''),
            tx_dict['v'],
            big_endian_to_int(tx_dict['r']),
            big_endian_to_int(tx_dict['s']),
        )
        tx_hash = t.hash
        encoding = rlp.encode(t)
    elif tx_dict['type'] == '0x2':
        t = eth.vm.forks.london.transactions.DynamicFeeTransaction(
            big_endian_to_int(normalize_bytes(tx_dict['chainId'])),
            tx_dict['nonce'],
            tx_dict['maxPriorityFeePerGas'],
            tx_dict['maxFeePerGas'],
            tx_dict['gas'],
            normalize_bytes(tx_dict['to'] or ''),
            tx_dict['value'],
            normalize_bytes(tx_dict['input'] or ''),
            tx_dict['accessList'],
            tx_dict['v'],
            big_endian_to_int(tx_dict['r']),
            big_endian_to_int(tx_dict['s']),
        )
        encoding = normalize_bytes('0x2') + t.encode()
        tx_hash = cast(Hash32, keccak(encoding))
    else:
        raise AssertionError("unsupported tx type")
    if normalize_bytes(tx_dict['hash']) != tx_hash:
        raise ValueError("""Tx hash does not match. Received invalid transaction?
        hashes:         {} {}
        nonce:          {}
        gasPrice:       {}
        gas:            {}
        to:             {}
        value:          {}
        input:          {}
        v:              {}
        r:              {}
        s:              {}
        """.format(
            tx_dict['hash'], tx_hash,
            tx_dict['nonce'],
            tx_dict['gasPrice'],
            tx_dict['gas'],
            normalize_bytes(tx_dict['to'] or ''),
            tx_dict['value'],
            normalize_bytes(tx_dict['input'] or ''),
            tx_dict['v'],
            big_endian_to_int(tx_dict['r']),
            big_endian_to_int(tx_dict['s']),
        ))
    return encoding


def generate_proof(mpt, mpt_key_nibbles: bytes):
    if not all(0 <= nibble < 16 for nibble in mpt_key_nibbles):
        raise ValueError("mpt_key_nibbles has non-nibble elements {}".format(str(mpt_key_nibbles)))
    EMPTY = 128
    stack_indexes = []
    stack = []

    def aux(node_hash, mpt_key_nibbles):
        nonlocal stack_indexes
        nonlocal stack

        node = mpt.get_node(node_hash)
        if get_node_type(node) == NODE_TYPE_BLANK:
            if MODULE_DEBUG:
                print("Hit an empty node, returning")
            return
        elif get_node_type(node) == NODE_TYPE_BRANCH:
            if MODULE_DEBUG:
                print("Hit a branch node")
            if mpt_key_nibbles:
                i = mpt_key_nibbles[0]
                stack_indexes.append(i)
                stack.append(node)
                aux(node[i], mpt_key_nibbles[1:])
            else:
                i = 16
                stack_indexes.append(i)
                stack.append(node)
        elif get_node_type(node) in [NODE_TYPE_EXTENSION, NODE_TYPE_LEAF]:
            if MODULE_DEBUG:
                print("Hit an extension/branch node")
            key = extract_key(node)
            prefix, key_remainder, mpt_key_nibbles_remainder = \
                    consume_common_prefix(key, mpt_key_nibbles)
            if not key_remainder:
                if MODULE_DEBUG:
                    print("Non-divergent leaf/extension")
                stack_indexes.append(1)
                stack.append(node)
                if get_node_type(node) == NODE_TYPE_EXTENSION:
                    aux(node[1], mpt_key_nibbles_remainder)
            else:
                if MODULE_DEBUG:
                    print("Divergent leaf/extension")
                stack_indexes.append(0xff)
                stack.append(node)
        else:
            raise ValueError("Unknown node type: {}".format(
                get_node_type(node)))

    root_node = mpt.get_node(mpt.root_hash)
    if get_node_type(root_node) == NODE_TYPE_BLANK:
        if MODULE_DEBUG:
            print("Blank root node")
    else:
        aux(mpt.root_hash, mpt_key_nibbles)

    if MODULE_DEBUG:
        print('key nibbles: ', mpt_key_nibbles)
        print('Stack:       ', rec_hex(stack))
        print('StackIndexes:', stack_indexes)

    return stack


def construct_proof_from_mpt(mpt, header, tx_index):
    mpt_key_nibbles = bytes_to_nibbles(rlp.encode(tx_index))
    stack = generate_proof(mpt, mpt_key_nibbles)

    proof_blob = rlp.encode([
        header,
        tx_index,
        stack,
    ])
    return proof_blob


def generate_proof_blob(w3, block_num, tx_index):
    block_dict = w3.eth.get_block(block_num)
    header = block_header(block_dict)

    mpt = HexaryTrie(db={})
    for tx_hash in block_dict["transactions"]:
        tx_dict = w3.eth.get_transaction(tx_hash)
        key = rlp.encode(tx_dict['transactionIndex'])
        value = rlp_transaction(tx_dict)
        mpt.set(key, value)

    if mpt.root_hash != normalize_bytes(block_dict['transactionsRoot']):
        raise ValueError(
            "Tx trie root hash does not match. Calculated: {} Sent: {}"
            .format(mpt.root_hash.hex(),
                    normalize_bytes(block_dict['transactionsRoot']).hex()))

    return construct_proof_from_mpt(mpt, header, tx_index)


def decode_compact(compact):
    assert len(compact)

    first_nibble = int(compact[0]) >> 4 & 0xF

    if first_nibble == 0:
        skip_nibbles = 2
        is_leaf = False
    elif first_nibble == 1:
        skip_nibbles = 1
        is_leaf = False
    elif first_nibble == 2:
        skip_nibbles = 2
        is_leaf = True
    elif first_nibble == 3:
        skip_nibbles = 1
        is_leaf = True
    else:
        assert False

    length = len(compact) * 2
    assert skip_nibbles <= length
    length -= skip_nibbles

    nibbles = list()
    for i in range(skip_nibbles, skip_nibbles + length):
        if i % 2 == 0:
            nibbles.append((int(compact[i // 2]) >> 4) & 0xF)
        else:
            nibbles.append((int(compact[i // 2]) >> 0) & 0xF)

    return is_leaf, bytearray(nibbles)


def shared_prefix_length(xs_offset, xs, ys):
    for i in range(len(ys)):
        if i + xs_offset >= len(xs):
            break
        if xs[i + xs_offset] != ys[i]:
            return i
    return len(ys)


def verify_mpt_proof(root_hash, mpt_key_nibbles, stack):
    mpt_key_offset = 0

    target_hash = root_hash

    for i in range(len(stack)):
        rlp_node = rlp.encode(stack[i])
        assert target_hash == keccak(rlp_node)

        node = stack[i]

        if len(node) == 17:
            if MODULE_DEBUG:
                print("Hit a branch node")

            if mpt_key_offset != len(mpt_key_nibbles):
                # we haven't consumed the entire path, so we need to look at a child
                nibble = mpt_key_nibbles[mpt_key_offset]
                mpt_key_offset += 1
                assert nibble <= 16

                if len(node[nibble]) == 0:
                    assert i == len(stack) - 1
                else:
                    target_hash = node[nibble]
            else:
                # we have consumed the entire mptKey, so we need to look at what's contained in this node.
                assert i == len(stack) - 1

                return node[16]

        elif len(node) == 2:
            if MODULE_DEBUG:
                print("Hit an extension/leaf node")

            is_leaf, node_key = decode_compact(rlp.encode(node[0]))

            prefix_length = shared_prefix_length(mpt_key_offset, mpt_key_nibbles, node_key)
            mpt_key_offset += prefix_length

            if prefix_length < len(node_key):
                assert i >= len(stack)

            if is_leaf:
                assert i >= len(stack) - 1
                assert mpt_key_offset >= len(mpt_key_nibbles)

                rlp_value = node[1]
                tx = rlp.decode(rlp_value)
                return tx

            else:
                assert i != len(stack) - 1

                target_hash = node[1]

        else:
            raise ValueError("Unknown node type: {}".format(node))


def verify_tx_proof(w3, block_num, prf):
    header, tx_index, stack = tuple(rlp.decode(prf))

    block_hash = w3.eth.get_block(block_num)['hash']
    assert block_hash == keccak(rlp.encode(header))
    tx_root_hash = header[4]

    tx_index = big_endian_to_int(tx_index)
    mpt_key_nibbles = bytes_to_nibbles(rlp.encode(tx_index))

    tx = verify_mpt_proof(tx_root_hash, mpt_key_nibbles, stack)

    nonce = big_endian_to_int(tx[0])
    gas_price = big_endian_to_int(tx[1])
    gas = big_endian_to_int(tx[2])
    to = tx[3]
    value = big_endian_to_int(tx[4])
    input = tx[5]
    v = big_endian_to_int(tx[6])
    r = big_endian_to_int(tx[7])
    s = big_endian_to_int(tx[8])
    unsigned_tx = {
        'nonce': nonce,
        'gasPrice': gas_price,
        'gas': gas,
        'to': to,
        'value': value,
        'data': input,
        'chainId': w3.eth.chain_id,
    }
    signed_tx = eth.vm.forks.london.transactions.LondonLegacyTransaction(
        nonce,
        gas_price,
        gas,
        to,
        value,
        input,
        v,
        r,
        s,
    )
    return unsigned_tx, signed_tx
