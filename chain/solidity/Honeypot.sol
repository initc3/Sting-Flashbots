// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;
contract Honeypot {

    address public owner;
    uint public bounty;
    bool public claimed;

    struct EnclaveData {
        bytes sgx_report;
        bytes ias_sig;
    }
    mapping (address => EnclaveData) public requested_enclaves_data;
    address[] public requested_enclaves;
    address[] public approved_enclaves;

    event BountyClaimed(address winner);


    constructor() payable public {
        owner = msg.sender;
        bounty = msg.value;
    }

    function setupEnclave(address enclave_address, bytes memory sgx_report, bytes memory ias_sig) public {
        for (uint i = 0; i < approved_enclaves.length; i++) {
            require(approved_enclaves[i] != enclave_address, "address already approved");
        }
        require(sgx_report.length > 0, "sgx_report is empty");
        require(ias_sig.length > 0, "ias_sig is empty");
        requested_enclaves_data[enclave_address] = EnclaveData(sgx_report, ias_sig);
        requested_enclaves.push(enclave_address);
    }

    function approveEnclave(address enclave_address) public {
        require(msg.sender == owner, "not authorized");
        approved_enclaves.push(enclave_address);
        for (uint i = 0; i < requested_enclaves.length; i++) {
            delete requested_enclaves[i];
        }
    }

    function collectBounty(address enclave_address, bytes memory proof, bytes memory sig) public {
        require(claimed == false, "bounty already claimed");
        bool found_address = false;
        for (uint i = 0; i < approved_enclaves.length; i++) {
            if (approved_enclaves[i] == enclave_address) {
                found_address = true;
            }
        }
        require(found_address, "enclave_address not approved");
        // verify_proof(proof);
        bytes32 hash = hash_data(proof);
        address signer = recover(hash, sig);
        require(signer == enclave_address, "proof must be signed by enclave_address");
        claimed = true;
        payable(msg.sender).transfer(bounty);
        emit BountyClaimed(msg.sender);
    }

    function hash_data(bytes memory data) internal returns (bytes32) {
        bytes memory eth_prefix = '\x19Ethereum Signed Message:\n';
        bytes memory packed = abi.encodePacked(eth_prefix,uint2str(data.length),data);
        return keccak256(packed);
    }

    function recover(bytes32 hash, bytes memory signature) internal pure returns (address) {
        if (signature.length == 65) {
            bytes32 r;
            bytes32 s;
            uint8 v;
            // ecrecover takes the signature parameters, and the only way to get them
            // currently is to use assembly.
            /// @solidity memory-safe-assembly
            assembly {
                r := mload(add(signature, 0x20))
                s := mload(add(signature, 0x40))
                v := byte(0, mload(add(signature, 0x60)))
            }
            if (uint256(s) > 0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF5D576E7357A4501DDFE92F46681B20A0) {
                revert("ECDSA: invalid signature 's' value");
            }
            address signer = ecrecover(hash, v, r, s);
            if (signer == address(0)) {
                revert("ECDSA: invalid signature");
            }
            return signer;
        } else {
            revert("ECDSA: invalid signature length");
        }
    }

    function uint2str( uint256 _i ) internal pure returns (string memory str) {
        if (_i == 0)
        {
            return "0";
        }
        uint256 j = _i;
        uint256 length;
        while (j != 0)
        {
            length++;
            j /= 10;
        }
        bytes memory bstr = new bytes(length);
        uint256 k = length;
        j = _i;
        while (j != 0)
        {
            bstr[--k] = bytes1(uint8(48 + j % 10));
            j /= 10;
        }
        str = string(bstr);
    }
}