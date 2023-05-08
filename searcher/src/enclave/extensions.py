
def sign_transaction(transaction_dict, private_key, k=0):
    if not isinstance(transaction_dict, Mapping):
        raise TypeError("transaction_dict must be dict-like, got %r" % transaction_dict)

    account = self.from_key(private_key)

    # allow from field, *only* if it matches the private key
    if 'from' in transaction_dict:
        if transaction_dict['from'] == account.address:
            sanitized_transaction = dissoc(transaction_dict, 'from')
        else:
            raise TypeError("from field must match key's %s, but it was %s" % (
                account.address,
                transaction_dict['from'],
            ))
    else:
        sanitized_transaction = transaction_dict

    # sign transaction
    (
        v,
        r,
        s,
        encoded_transaction,
    ) = sign_transaction_dict(account._key_obj, sanitized_transaction, k)
    transaction_hash = keccak(encoded_transaction)

    return SignedTransaction(
        rawTransaction=HexBytes(encoded_transaction),
        hash=HexBytes(transaction_hash),
        r=r,
        s=s,
        v=v,
    )

def sign_transaction_dict(eth_key, transaction_dict, k=0):
    # generate RLP-serializable transaction, with defaults filled
    unsigned_transaction = serializable_unsigned_transaction_from_dict(transaction_dict)

    transaction_hash = unsigned_transaction.hash()

    # detect chain
    if isinstance(unsigned_transaction, UnsignedTransaction):
        chain_id = None
        (v, r, s) = sign_transaction_hash(eth_key, transaction_hash, chain_id)
    elif isinstance(unsigned_transaction, Transaction):
        chain_id = unsigned_transaction.v
        (v, r, s) = sign_transaction_hash(eth_key, transaction_hash, chain_id, k)
    elif isinstance(unsigned_transaction, TypedTransaction):
        # Each transaction type dictates its payload, and consequently,
        # all the funky logic around the `v` signature field is both obsolete && incorrect.
        # We want to obtain the raw `v` and delegate to the transaction type itself.
        (v, r, s) = eth_key.sign_msg_hash(transaction_hash).vrs
    else:
        # Cannot happen, but better for code to be defensive + self-documenting.
        raise TypeError("unknown Transaction object: %s" % type(unsigned_transaction))

    # serialize transaction with rlp
    encoded_transaction = encode_transaction(unsigned_transaction, vrs=(v, r, s))

    return (v, r, s, encoded_transaction)

def sign_transaction_hash(account, transaction_hash, chain_id, k=0):
    signature = ecdsa_sign(transaction_hash, k)
    (v_raw, r, s) = signature.vrs
    v = to_eth_v(v_raw, chain_id)
    return (v, r, s)

def ecdsa_sign(msg_hash: bytes,
                private_key: PrivateKey, k=0) -> Signature:
    signature_vrs = ecdsa_raw_sign(msg_hash, private_key.to_bytes(), k)
    signature = Signature(vrs=signature_vrs, backend=self)
    return signature


def ecdsa_raw_sign(msg_hash: bytes,
                   private_key_bytes: bytes, k=0) -> Tuple[int, int, int]:
    z = big_endian_to_int(msg_hash)
    if k == 0:
        k = deterministic_generate_k(msg_hash, private_key_bytes)

    print(f'!!!! k used in signature: {k}')

    r, y = fast_multiply(G, k)
    s_raw = inv(k, N) * (z + r * big_endian_to_int(private_key_bytes)) % N

    v = 27 + ((y % 2) ^ (0 if s_raw * 2 < N else 1))
    s = s_raw if s_raw * 2 < N else N - s_raw

    return v - 27, r, s