// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

import { BytesUtils } from "../ens-contracts/dnssec-oracle/BytesUtils.sol";
import { RSAVerify } from "../ens-contracts/dnssec-oracle/algorithms/RSAVerify.sol";
import "./JSONBuilder.sol";
import { Base64 } from "../openzeppelin/utils/Base64.sol";

library RemoteAttestation {
    using BytesUtils for *;

    uint256 constant QUOTE_BODY_LENGTH = 432;
    uint256 constant MRENCLAVE_OFFSET = 112;
    uint256 constant MRSIGNER_OFFSET = 176;
    uint256 constant PAYLOAD_OFFSET = 368;
    uint256 constant PAYLOAD_SIZE = 64;

    /**
     * Bad report signature
     */
    error BadReportSignature();

    function verifyRemoteAttestation(
        bytes calldata report,
        bytes calldata sig,
        bytes memory signingMod,
        bytes memory signingExp,
        bytes32 mrenclave,
        bytes32 mrsigner
    ) internal view returns (bytes memory payload) {
        // Decode the encoded report JSON values to a Values struct and reconstruct the original JSON string
        (JSONBuilder.Values memory reportValues, bytes memory reportBytes) = _buildReportBytes(report);

        // Verify the report was signed by the SigningPK
        if (!verifyReportSignature(reportBytes, sig, signingMod, signingExp)) {
            revert BadReportSignature();
        }

        // Verify the report's contents match the expected
        payload = _verifyReportContents(reportValues, mrenclave, mrsigner);
    }

    function _buildReportBytes(bytes memory encodedReportValues)
        internal
        view
        returns (JSONBuilder.Values memory reportValues, bytes memory reportBytes)
    {
        // Decode the report JSON values
        (
            bytes memory id,
            bytes memory timestamp,
            bytes memory version,
            bytes memory advisoryURL,
            bytes memory advisoryIDs,
            bytes memory isvEnclaveQuoteStatus,
            bytes memory platformInfoBlob,
            bytes memory isvEnclaveQuoteBody
        ) = abi.decode(encodedReportValues, (bytes, bytes, bytes, bytes, bytes, bytes, bytes, bytes));

        // Assumes the quote body was already decoded off-chain
        bytes memory encBody = bytes(Base64.encode(isvEnclaveQuoteBody));

        // Pack values to struct
        reportValues = JSONBuilder.Values(
            id, timestamp, version, advisoryURL, advisoryIDs, isvEnclaveQuoteStatus, platformInfoBlob, encBody
        );

        // Reconstruct the JSON report that was signed
        reportBytes = bytes(JSONBuilder.buildJSON(reportValues));

        // Pass on the decoded value for later processing
        reportValues.isvEnclaveQuoteBody = isvEnclaveQuoteBody;
    }

    function verifyReportSignature(
        bytes memory report,
        bytes calldata sig,
        bytes memory signingMod,
        bytes memory signingExp
    ) public view returns (bool) {
        // Use signingPK to verify sig is the RSA signature over sha256(report)
        (bool success, bytes memory got) = RSAVerify.rsarecover(signingMod, signingExp, sig);
        // Last 32 bytes is recovered signed digest
        bytes32 recovered = got.readBytes32(got.length - 32);
        return success && recovered == sha256(report);
    }

    function _verifyReportContents(JSONBuilder.Values memory reportValues, bytes32 mrenclave, bytes32 mrsigner)
        internal
        pure
        returns (bytes memory payload)
    {
        // check enclave status
        bytes32 status = keccak256(reportValues.isvEnclaveQuoteStatus);
//        require(status == OK_STATUS || status == HARDENING_STATUS, "bad isvEnclaveQuoteStatus");

        // quote body is already base64 decoded
        bytes memory quoteBody = reportValues.isvEnclaveQuoteBody;
        assert(quoteBody.length == QUOTE_BODY_LENGTH);

        // Verify report's MRENCLAVE matches the expected
        bytes32 mre = quoteBody.readBytes32(MRENCLAVE_OFFSET);
        require(mre == mrenclave);

        // Verify report's MRSIGNER matches the expected
        bytes32 mrs = quoteBody.readBytes32(MRSIGNER_OFFSET);
        require(mrs == mrsigner);

        // Verify report's <= 64B payload matches the expected
        payload = quoteBody.substring(PAYLOAD_OFFSET, PAYLOAD_SIZE);
    }
}
