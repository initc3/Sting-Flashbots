import json

local_url = 'http://127.0.0.1:8545'

contract_addr_dict = {
    'Honeypot': '0x2ACe51b358Aa73b3D85C1962e8D2A9cD8e6349c7',
}

ether_unit = 10**18

relayer_key_path = f'src/relayer/enclave/'


class Block:
    def __init__(self, tx_list):
        self.tx_list = tx_list

    def serialize(self):
        serialized_tx_list = list()
        for tx in self.tx_list:
            serialized_tx_list.append(serialize_signed_tx(tx))
        return str(serialized_tx_list)

    def deserialize(serialized_block):
        serialized_tx_list = eval(serialized_block)
        tx_list = list()
        for serialized_tx in serialized_tx_list:
            tx_list.append(deserialize_signed_tx(serialized_tx))
        return Block(tx_list)

    def apply(self, w3):
        for tx in self.tx_list:
            receipt = send_tx(tx, w3)
            print(receipt)
            contract = instantiate_contract('Honeypot', w3)
            log = contract.events.BountyClaimed().processReceipt(receipt)
            print(f'winner {log[0]["args"]["winner"]}')


def parse_contract(contract_name):
    contract = json.load(open(f'chain/build/contracts/{contract_name}.json'))
    return contract['abi'], contract['bytecode']


def instantiate_contract(contract_name, w3):
    abi, bytecode = parse_contract(contract_name)
    return w3.eth.contract(address=contract_addr_dict[contract_name], abi=abi)

