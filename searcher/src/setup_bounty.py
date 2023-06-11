import base64
import subprocess
import sys 

from eth_account.account import Account
import solcx
from solcx import compile_source
from enclave.utils import *


SOLIDITY_SOURCE = ("../solidity", "Honeypot.sol", [])


def setup_bounty_contract(w3):
    bounty_admin = get_account(w3, os.environ.get("BOUNTY_CONTRACT_ADMIN_PK", "0xc8ae83e52a1593ac42fc6868dbdbf9af7a09678b4f3331d191962e582133b78d"))
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
    contract_address = open("contract_address").read()
    contract = w3.eth.contract(abi=abis, bytecode=bins, address=contract_address)
    enclave_address = open("/Sting-Flashbots/searcher/output_data/enclave_address").read()
    balance_before = w3.eth.get_balance(informant_account.address)
    send_tx(w3, contract.functions.collectBounty(enclave_address, proof, sig), informant_account.address)
    balance_after = w3.eth.get_balance(informant_account.address)
    print("profit", balance_after - balance_before)
    assert contract.functions.claimed().call()
    assert balance_after > balance_before


def generate_bundle(w3):
    stinger_sender = get_account(w3, os.environ.get("STINGER_PK"))
    sting_tx, _ = generate_tx(w3, sender=stinger_sender, gas_price=w3.eth.gas_price * GAS_MUL)
    bundle_txs = private_order_flow(w3, POF_TXS)
    sting_bundle = make_bundle(bundle_txs)
    for i in range(len(sting_bundle)):
        sting_bundle[i]["signed_transaction"] = sting_bundle[i]["signed_transaction"].hex()

    json.dump(sting_bundle, open("/Sting-Flashbots/searcher/input_data/sting_bundle.json", "w"))
    json.dump(sting_tx, open("/Sting-Flashbots/searcher/input_data/sting_tx.json", "w"))
    json.dump(sting_tx, open("sting_tx.json", "w"))
    print(f'generate stinger tx {sting_tx}')
    print(f'generate stinger bundle {sting_bundle}')


def private_order_flow(w3, num_txs):
    keys = os.environ.get("POF_KEYS")
    if keys is not None:
        keys = json.loads(keys)
        print("POF_KEYS", keys)
        senders = [get_account(w3, pk) for pk in keys]
    else:
        senders = None
    print("w3.eth.gas_price", w3.eth.gas_price)
    return generate_signed_txs(w3, num_txs, senders=senders, gas_price=w3.eth.gas_price * GAS_MUL)

def get_contract(w3):
    _, abis, bins = compile_source_file(SOLIDITY_SOURCE)
    contract_address = open("contract_address").read()
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
    print(f'========================================================================= {sys.argv[1]}')

    w3 = get_web3()
    solcx.install_solc()
    globals()[sys.argv[1]](w3)

    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
