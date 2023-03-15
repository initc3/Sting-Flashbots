pragma solidity ^0.5.0;

contract Honeypot {

    address public owner;
    bytes32 public puzzle;
    uint public bounty;
    bool public claimed;


    event BountyClaimed(address winner);


    constructor(bytes32 _puzzle) payable public {
        puzzle = _puzzle;
        owner = msg.sender;
        bounty = msg.value;
    }


    function claimBounty(uint preimage) public {
        assert(!claimed);
        claimed = true;
        assert(puzzle == keccak256(abi.encode(preimage)));
        msg.sender.transfer(bounty);
        emit BountyClaimed(msg.sender);
    }
}