#!/usr/bin/env python3

import os
import sys

from Crypto.PublicKey import RSA
from utils import *

if not os.path.exists("/dev/attestation/quote"):
    print("Cannot find `/dev/attestation/quote`; "
          "are you running under SGX, with remote attestation enabled?")
    sys.exit(1)

with open('/dev/attestation/attestation_type') as f:
    print(f"Detected attestation type: {f.read()}")


if os.path.isfile(secret_key_path):
    with open(secret_key_path, "rb") as f:
        signing_key = f.read()
    signing_address = Account.from_key(signing_key).address
else:
    signing_account = setup_new_account(get_web3())
    signing_address = signing_account.address
    with open(secret_key_path, "wb") as f:
        f.write(bytes(signing_account.privateKey))
with open("/dev/attestation/user_report_data", "wb") as f:
    f.write(bytes.fromhex(signing_address[2:]))

with open("/dev/attestation/quote", "rb") as f:
    quote = f.read()


with open(os.path.join(output_dir, "quote"), "wb") as f:
    f.write(quote)

print(f"Extracted SGX quote with size = {len(quote)} and the following fields:")
print(f"  ATTRIBUTES.FLAGS: {quote[96:104].hex()}  [ Debug bit: {quote[96] & 2 > 0} ]")
print(f"  ATTRIBUTES.XFRM:  {quote[104:112].hex()}")
print(f"  MRENCLAVE:        {quote[112:144].hex()}")
print(f"  MRSIGNER:         {quote[176:208].hex()}")
print(f"  ISVPRODID:        {quote[304:306].hex()}")
print(f"  ISVSVN:           {quote[306:308].hex()}")
print(f"  REPORTDATA:       {quote[368:400].hex()}")
print(f"                    {quote[400:432].hex()}")