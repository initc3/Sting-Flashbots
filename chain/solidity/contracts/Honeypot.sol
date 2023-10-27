// SPDX-License-Identifier: UNLICENSED
pragma solidity >=0.5.10 <0.9.0;

import "./RLPReader.sol";
import { X509Verifier } from "./rave/X509Verifier.sol";
import "./rave/RemoteAttestation.sol";

contract Honeypot {

    using RLPReader for RLPReader.RLPItem;
    using RLPReader for bytes;

    address public owner;
    uint public bounty;
    bool public claimed;

    mapping (address => bool) public enclaveApproved;

    event BountyClaimed(address winner);

    bytes public constant intelRootModulus = hex"9F3C647EB5773CBB512D2732C0D7415EBB55A0FA9EDE2E649199E6821DB910D53177370977466A6A5E4786CCD2DDEBD4149D6A2F6325529DD10CC98737B0779C1A07E29C47A1AE004948476C489F45A5A15D7AC8ECC6ACC645ADB43D87679DF59C093BC5A2E9696C5478541B979E754B573914BE55D32FF4C09DDF27219934CD990527B3F92ED78FBF29246ABECB71240EF39C2D7107B447545A7FFB10EB060A68A98580219E36910952683892D6A5E2A80803193E407531404E36B315623799AA825074409754A2DFE8F5AFD5FE631E1FC2AF3808906F28A790D9DD9FE060939B125790C5805D037DF56A99531B96DE69DE33ED226CC1207D1042B5C9AB7F404FC711C0FE4769FB9578B1DC0EC469EA1A25E0FF9914886EF2699B235BB4847DD6FF40B606E6170793C2FB98B314587F9CFD257362DFEAB10B3BD2D97673A1A4BD44C453AAF47FC1F2D3D0F384F74A06F89C089F0DA6CDB7FCEEE8C9821A8E54F25C0416D18C46839A5F8012FBDD3DC74D256279ADC2C0D55AFF6F0622425D1B";
    bytes public constant intelRootExponent = hex"010001";

    modifier onlyOwner() {
        require(msg.sender == owner);
        _;
    }


    constructor() payable public {
        owner = msg.sender;
        bounty = msg.value;
    }

    function submitEnclave(bytes calldata report,
        bytes calldata sig,
        bytes memory cert,
        bytes32 mrenclave,
        bytes32 mrsigner
    ) public {
        // Verify the leafX509Cert was signed with signingMod and signingExp
        (bytes memory leafCertModulus, bytes memory leafCertExponent) =
            X509Verifier.verifySignedX509(cert, intelRootModulus, intelRootExponent);

        // Verify report has expected fields then extract its payload
        bytes memory payload = RemoteAttestation.verifyRemoteAttestation(report, sig, leafCertModulus, leafCertExponent, mrenclave, mrsigner);

        address enclaveAddr = address(bytes20(payload));

        require(!enclaveApproved[enclaveAddr], "address already approved");
        enclaveApproved[enclaveAddr] = true;
    }

    function collectBounty(address enclaveAddr, bytes memory proofBlob, bytes memory sig) public {
        require(!claimed, "bounty already claimed");
        require(enclaveApproved[enclaveAddr], "address not approved");

        bytes32 hash = hash_data(proofBlob);
        address signer = recover(hash, sig);
        require(signer == enclaveAddr, "incorrect signature");

        RLPReader.RLPItem[] memory items = proofBlob.toRlpItem().toList();
        uint blockNum = items[0].toUint();
        bytes32 blockHash = toBytes32(items[1].toBytes());
        require(blockhash(blockNum) == blockHash, "block hash does not match block number");

        claimed = true;
        payable(msg.sender).transfer(bounty);
        emit BountyClaimed(msg.sender);
    }

    function hash_data(bytes memory data) internal pure returns (bytes32) {
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

    function toBytes32(bytes memory b) internal pure returns (bytes32) {
        bytes32 out;
        for (uint i = 0; i < 32; i++) {
          out |= bytes32(b[i] & 0xFF) >> (i * 8);
        }
        return out;
    }

}