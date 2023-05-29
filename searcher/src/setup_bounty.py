import auditee
import base64
import json
import os 
import time 
import socket
import subprocess
import sys 

import web3
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
from web3.middleware import construct_sign_and_send_raw_middleware
from eth_account.account import Account
import solcx
from solcx import compile_source

SOLIDITY_SOURCE = ("../solidity", "Honeypot.sol", [])
BOUNTY_AMT = 150000000000000

try:
    contract_address = open("contract_address").read()
except Exception as e:
    pass 

def setup_bounty_contract(w3):
    bounty_admin = get_account(w3, os.environ.get("BOUNTY_CONTRACT_ADMIN_PK", "0xc8ae83e52a1593ac42fc6868dbdbf9af7a09678b4f3331d191962e582133b78d"))
    # print(f'bounty_admin {bounty_admin.address} balance: {w3.eth.get_balance(bounty_admin.address)}')
    contract_address, contract, contract_id = deploy_contract(w3, bounty_admin.address, SOLIDITY_SOURCE)
    with open("contract_address", "w") as f:
        f.write(contract_address)

def submit_enclave(w3):
    contract = get_contract(w3)
    informant_account = get_account(w3, os.environ.get("INFORMANT_PK", "0x3b7cd6efb048079f7e5209c05d74369600df0d15fc177be631b3b4f9a84f8abc"))
    # print(f'informant_account {informant_account.address} balance: {w3.eth.get_balance(informant_account.address)}')
    enclave_address = open("/Sting-Flashbots/searcher/output_data/enclave_address").read()
    if int(os.environ.get("SGX", 1)) == 1:
        report = open("ias.report").read()
        report_json = json.loads(report)
        quote = base64.b64decode(report_json["isvEnclaveQuoteBody"])
        with open("ias.sig") as f:
            ias_sig_b64 = f.read()
        ias_sig = base64.b64decode(ias_sig_b64)
        assert enclave_address == Web3.toChecksumAddress(quote[368:388].hex())
    else:
        report = "ias report"
        ias_sig = b"ias sig"
    # print("enclave_address", enclave_address)
    # print("sgx report", bytes(json.dumps(report), 'utf-8'))
    send_tx(w3, contract.functions.submitEnclave(enclave_address, bytes(report, 'utf-8'), ias_sig), informant_account.address)

def approve_enclave(w3):
    contract = get_contract(w3)
    bounty_admin = Account.from_key(os.environ.get("BOUNTY_CONTRACT_ADMIN_PK", "0xc8ae83e52a1593ac42fc6868dbdbf9af7a09678b4f3331d191962e582133b78d"))
    w3.middleware_onion.add(construct_sign_and_send_raw_middleware(bounty_admin))
    print(f'bounty_admin {bounty_admin.address} balance: {w3.eth.get_balance(bounty_admin.address)}')

    contract_enclave_addr = open("/Sting-Flashbots/searcher/output_data/enclave_address").read()
    sgx_data = contract.functions.enclaveData(contract_enclave_addr).call()
    report = sgx_data[0].decode("utf-8")
    ias_sig = sgx_data[1]
    if int(os.environ.get("SGX", 1)) == 1:
        report_json = json.loads(report)
        quote = base64.b64decode(report_json["isvEnclaveQuoteBody"])

        mrenclave = quote[112:144].hex()
        report_data = quote[368:432]
        enclave_address = Web3.toChecksumAddress(report_data[:20].hex())
        assert contract_enclave_addr == enclave_address
        APPROVED_MRENCLAVE = mrenclave #TODO reporoducible builds
        # assert mrenclave == APPROVED_MRENCLAVE
        # auditee.verify_mrenclave(
        #     'enclave/',
        #     'python.manifest.sgx',
        #     ias_report=report_path,
        #     APPROVED_MRENCLAVE
        # )

        report_path = "contract.report"
        sig_path = "contract.sig"
        open(report_path, "w").write(report)
        ias_sig_b64 = base64.b64encode(ias_sig).decode("ascii")
        open(sig_path, "w").write(ias_sig_b64)

        verify_report_cmd = 'gramine-sgx-ias-verify-report ' + \
            f'--mr-enclave {APPROVED_MRENCLAVE} ' + \
            f'--report-data {report_data.hex()} ' + \
            f'--report-path {report_path} ' + \
            f'--sig-path {sig_path} ' + \
            '--allow-debug-enclave --allow-outdated-tcb' 
        print(verify_report_cmd)
        res = subprocess.run(verify_report_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        if res.returncode != 0:
            print(f"gramine-sgx-ias-verify-report failed with code {res.returncode}\n{res.stdout.decode('utf-8')}{res.stderr.decode('utf-8')}")
            exit(res.returncode)

    send_tx(w3, contract.functions.approveEnclave(contract_enclave_addr), bounty_admin.address)

def collect_bounty(w3):
    informant_account = get_account(w3, os.environ.get("INFORMANT_PK", "0x3b7cd6efb048079f7e5209c05d74369600df0d15fc177be631b3b4f9a84f8abc"))
    proof = open("/Sting-Flashbots/searcher/output_data/proof_blob", "rb").read()
    sig = open("/Sting-Flashbots/searcher/output_data/proof_sig", "rb").read()
    _, abis, bins = compile_source_file(SOLIDITY_SOURCE)
    contract = w3.eth.contract(abi=abis, bytecode=bins, address=contract_address)
    enclave_address = open("/Sting-Flashbots/searcher/output_data/enclave_address").read()
    balance_before = w3.eth.get_balance(informant_account.address)
    send_tx(w3, contract.functions.collectBounty(enclave_address, proof, sig), informant_account.address)
    balance_after = w3.eth.get_balance(informant_account.address)
    print("profit", balance_after - balance_before)
    assert contract.functions.claimed().call()
    assert balance_after > balance_before

def get_account(w3, secret_key):
    account = Account.from_key(secret_key)
    w3.middleware_onion.add(construct_sign_and_send_raw_middleware(account)) 
    return account   

def get_contract(w3):
    _, abis, bins = compile_source_file(SOLIDITY_SOURCE)
    return w3.eth.contract(abi=abis, bytecode=bins, address=contract_address)

def compile_source_file(contract_paths):
    base_path, contract_source_path, allowed = contract_paths
    with open(os.path.join(base_path, contract_source_path), 'r') as f:
        contract_source = f.read()
    compiled_sol = compile_source(contract_source,
                                  output_values=['abi', 'bin'],
                                  base_path=base_path,
                                  allow_paths=[allowed])
    abis = []
    bins = ""
    contract_id = ""
    for x in compiled_sol:
        contract_id += x
        contract_interface=compiled_sol[x]
        abis = abis + contract_interface['abi']
        bins = bins + contract_interface['bin']
    return contract_id, abis, bins

def deploy_contract(w3, admin_addr, contract_paths):
    contract_id,abis,bins = compile_source_file(contract_paths)
    contract = w3.eth.contract(abi=abis, bytecode=bins)
    tx_hash = contract.constructor().transact({"from": admin_addr, "value": BOUNTY_AMT})
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    contract_address = receipt['contractAddress']
    contract = w3.eth.contract(address=contract_address, abi=abis)
    print(f'Deployed {contract_id} to: {contract_address} with hash  {tx_hash.hex()}')
    return contract_address, contract, contract_id

def get_web3():
    while True:
        try:
            HOST = socket.gethostbyname('builder')
            PORT = 8545
            if int(os.environ.get("TLS", 0)) == 1:
                endpoint = f"https://{HOST}:{PORT}"
                from enclave.ra_tls import get_ra_tls_session
                s = get_ra_tls_session(HOST, PORT, "/cert/tlscert.der")
                w3 = Web3(HTTPProvider(endpoint, session=s))
            else:
                endpoint = f"http://{HOST}:{PORT}"
                w3 = Web3(HTTPProvider(endpoint))
            block = w3.eth.block_number
            break
        except Exception as e:
            time.sleep(5)
            print(f'waiting to connect to builder...', e)
            raise e
    while block < 26:
        print(f'waiting for block number {block} > 25...')
        time.sleep(5)
        block = w3.eth.block_number
    return w3

def send_tx(w3, foo, user_addr, value=0):
    print(f"send_tx from address: {user_addr} {foo}")
    try:
        gas_estimate = foo.estimateGas()  # for some reason this fails sometimes when it shouldn't
    except Exception as e:
        print(f"estimate gas error {e}")
        gas_estimate = 0
        pass

    if gas_estimate < 10000000:
        tx_hash = foo.transact({"from": user_addr, "value": value})
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"transaction receipt mined: {receipt}")
        return receipt.gasUsed
    else:
        print(f"send_tx error Gas cost exceeds 10000000 < {gas_estimate}")
        exit(1)

if __name__ == '__main__':
    w3 = get_web3()
    solcx.install_solc()
    globals()[sys.argv[1]](w3)
