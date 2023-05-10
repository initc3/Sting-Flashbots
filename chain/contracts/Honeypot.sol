pragma solidity ^0.5.0;

import "./EllipticCurve.sol";

contract Honeypot {

    address public owner;
    bytes32 public MREnclave;
    uint public bounty;

    bool public claimed;

    uint public constant confirmation = 0; //TODO: change parameter later


    event BountyClaimed(address winner);


    constructor(bytes32 _MREnclave) payable public {
        MREnclave = _MREnclave;
        owner = msg.sender;
        bounty = msg.value;
    }


    function claimBounty(uint r, uint h, bytes32 victim_tx_hash, bytes32 unsigned_adv_tx_hash, bytes memory adv_tx_sig) public {
        require(!claimed, "Bounty has already claimed!!!");


        require(block.number - h > confirmation, "Not enough confirmations!!!");
        bytes32 hs = blockhash(h);

        uint C = _toUint(_toBytes(victim_tx_hash), 0) ^ r;

        (bytes32 sig_r, bytes32 sig_s, uint8 sig_v) = _splitSignature(adv_tx_sig);

        address signer =  ecrecover(unsigned_adv_tx_hash, sig_v, sig_r, sig_s);

        require(signer != address(0), "ECDSA: invalid signature");
        require(signer == msg.sender, "signer is not the msg.sender");


        _verify(C, _toUint(_toBytes(sig_r), 0));

        claimed = true;
        msg.sender.transfer(bounty);
        emit BountyClaimed(msg.sender);
    }


    function _verify(uint nonce, uint r) internal pure returns (uint) {
        uint GX = 55066263022277343669578718895168534326250603453777594175500187360389116729240;
        uint GY = 32670510020758816978083085130507043184471273380659243275938904335757337482424;
        uint A = 0;
        uint P = 115792089237316195423570985008687907853269984665640564039457584007908834671663;

        (uint256 x1, uint256 y1, uint256 z1) = EllipticCurve.jacMul(nonce, GX, GY, 1, A, P);
        (uint _r, uint _) = EllipticCurve.toAffine(x1, y1, z1, P);

        require(_r == r, "ECDSA nonce verification failed!");

        return 0;
    }


    function _getEthSignedMessageHash(
        bytes32 _messageHash
    ) internal pure returns (bytes32) {
        /*
        Signature is produced by signing a keccak256 hash with the following format:
        "\x19Ethereum Signed Message\n" + len(msg) + msg
        */
        return
            keccak256(
                abi.encodePacked("\x19Ethereum Signed Message:\n32", _messageHash)
            );
    }

    function _splitSignature(
        bytes memory sig
    ) internal pure returns (bytes32 r, bytes32 s, uint8 v) {
        require(sig.length == 65, "invalid signature length");

        assembly {
            /*
            First 32 bytes stores the length of the signature

            add(sig, 32) = pointer of sig + 32
            effectively, skips first 32 bytes of signature

            mload(p) loads next 32 bytes starting at the memory address p into memory
            */

            // first 32 bytes, after the length prefix
            r := mload(add(sig, 32))
            // second 32 bytes
            s := mload(add(sig, 64))
            // final byte (first byte of the next 32 bytes)
            v := byte(0, mload(add(sig, 96)))
        }

        // implicitly return (r, s, v)
    }


    function _toUint(bytes memory _bytes, uint _start) internal pure returns (uint256) {
        require(_bytes.length >= (_start + 32));
        uint256 tempUint;
        assembly {
          tempUint := mload(add(add(_bytes, 0x20), _start))
        }
        return tempUint;
    }


    function _toBytes(bytes32 data) internal pure returns (bytes memory) {
        return abi.encodePacked(data);
    }
}