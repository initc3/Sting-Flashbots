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

    // function collectBounty(address enclave_address, bytes proof, bytes sig) public {
    //     bool found_address;
    //     for (uint i = 0; i < approved_enclaves.length; i++) {
    //         if (approved_enclaves[i] == enclave_address) {
    //             found = True;
    //         }
    //     }
    //     require(verify_sig(enclave_address, proof, sig));
    // }
}