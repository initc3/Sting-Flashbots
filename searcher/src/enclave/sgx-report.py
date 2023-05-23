#!/usr/bin/env python3

import os
import sys

from Crypto.PublicKey import RSA
from utils import *

if not os.path.exists("/dev/attestation/report"):
    print("Cannot find `/dev/attestation/report`; are you running under SGX?")
    sys.exit(1)

with open("/dev/attestation/my_target_info", "rb") as f:
    my_target_info = f.read()

with open("/dev/attestation/target_info", "wb") as f:
    f.write(my_target_info)

if os.path.isfile(secret_key_path):
    with open(secret_key_path, "rb") as f:
        signing_key = f.read()
    signing_address = Account.from_key(signing_key).address
else:
    signing_account = setup_new_account(get_web3()) #TODO auto web3
    signing_address = signing_account.address
    with open(secret_key_path, "wb") as f:
        f.write(bytes(signing_account.privateKey))
with open("/dev/attestation/user_report_data", "wb") as f:
    f.write(bytes.fromhex(signing_address[2:]))

with open("/dev/attestation/report", "rb") as f:
    report = f.read()

with open(os.path.join(output_dir, "report"), "wb") as f:
    f.write(report)

print(f"Generated SGX report with size = {len(report)} and the following fields:")
print(f"  ATTRIBUTES.FLAGS: {report[48:56].hex()}  [ Debug bit: {report[48] & 2 > 0} ]")
print(f"  ATTRIBUTES.XFRM:  {report[56:64].hex()}")
print(f"  MRENCLAVE:        {report[64:96].hex()}")
print(f"  MRSIGNER:         {report[128:160].hex()}")
print(f"  ISVPRODID:        {report[256:258].hex()}")
print(f"  ISVSVN:           {report[258:260].hex()}")
print(f"  REPORTDATA:       {report[320:352].hex()}")
print(f"                    {report[352:384].hex()}")