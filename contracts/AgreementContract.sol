// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

contract AgreementContract {
    address payable public partyA;
    address payable public partyB;
    uint256 public contractValue;
    uint256 public contractExpirationDate;
    bool public partyAConfirmed;
    bool public partyBConfirmed;
    bool public contractExecuted;

    struct PartyHistory {
        uint256 partyNextTransactionMean;
    }

    mapping(address => PartyHistory) public partyHistories;

    constructor(
        address payable _partyA,
        address payable _partyB,
        uint256 _contractValue,
        uint256 _contractDuration,

        uint256 _partyANextTransactionMean,
        uint256 _partyBNextTransactionMean
) {
        partyA = _partyA;
        partyB = _partyB;
        contractValue = _contractValue;
        contractExpirationDate = block.timestamp + _contractDuration;

        partyHistories[partyA].partyNextTransactionMean = _partyANextTransactionMean;
        partyHistories[partyB].partyNextTransactionMean = _partyBNextTransactionMean;
    }

    function confirmAgreement() public payable {
        require(msg.sender == partyA || msg.sender == partyB, "Only parties to the contract can confirm the agreement");
        require(msg.value == contractValue, "The value sent does not match the contract value");

        if (msg.sender == partyA) {
            partyAConfirmed = true;
        } else {
            partyBConfirmed = true;
        }

        if (partyAConfirmed && partyBConfirmed && !contractExecuted) {
            executeContract();
        }
    }

    function cancelContract() public {
        require(msg.sender == partyA || msg.sender == partyB, "Only parties to the contract can cancel the agreement");
        require(!partyAConfirmed || !partyBConfirmed, "The contract has already been confirmed");
        require(!contractExecuted, "The contract has already been executed");

        if (partyAConfirmed && !partyBConfirmed) {
            partyA.transfer(contractValue);
        } else if (!partyAConfirmed && partyBConfirmed) {
            partyB.transfer(contractValue);
        } else {
            partyA.transfer(contractValue / 2);
            partyB.transfer(contractValue / 2);
        }

        selfdestruct(partyA);
    }

    function executeContract() internal {
        require(block.timestamp <= contractExpirationDate, "Contract has expired");
        // Check if both parties are trustworthy
        bool partyATrustworthy = analyzeParty(partyA);
        bool partyBTrustworthy = analyzeParty(partyB);
        require(partyATrustworthy && partyBTrustworthy, "One or both parties are not trustworthy");

        partyA.transfer(address(this).balance);
        contractExecuted = true;
    }

    // Define a function to analyze a party's transaction history and determine if they are trustworthy
    function analyzeParty(address party) internal view returns (bool) {
        // Get the transaction history for the party
        PartyHistory memory history = partyHistories[party];

        // Check if the party's next transaction mean is greater than or equal to the contract value
        return history.partyNextTransactionMean >= contractValue;
    }
}
