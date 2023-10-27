// SPDX-License-Identifier: Apache-2.0
pragma solidity >=0.8.0 <0.9.0;

library JSONBuilder {
    struct Values {
//        bytes id;
//        bytes timestamp;
//        bytes version;
//        bytes epidPseudonym;
//        bytes advisoryURL;
//        bytes advisoryIDs;
//        bytes isvEnclaveQuoteStatus;
//        bytes isvEnclaveQuoteBody;
        bytes id;
        bytes timestamp;
        bytes version;
        bytes advisoryURL;
        bytes advisoryIDs;
        bytes isvEnclaveQuoteStatus;
        bytes platformInfoBlob;
        bytes isvEnclaveQuoteBody;
    }

    function buildJSON(Values memory values) internal pure returns (string memory json) {
//        json = string(
//            abi.encodePacked(
//                '{"id":"',
//                values.id,
//                '","timestamp":"',
//                values.timestamp,
//                '","version":',
//                values.version,
//                ',"epidPseudonym":"',
//                values.epidPseudonym
//            )
//        );
//        json = string(
//            abi.encodePacked(
//                json,
//                '","advisoryURL":"',
//                values.advisoryURL,
//                '","advisoryIDs":',
//                values.advisoryIDs,
//                ',"isvEnclaveQuoteStatus":"',
//                values.isvEnclaveQuoteStatus,
//                '","isvEnclaveQuoteBody":"',
//                values.isvEnclaveQuoteBody,
//                '"}'
//            )
//        );
        json = string(
            bytes.concat(
                abi.encodePacked(
                    '{',
                    '"id":"',
                    values.id,
                    '","timestamp":"',
                    values.timestamp,
                    '","version":',
                    values.version,
                    ',"advisoryURL":"',
                    values.advisoryURL
                ),
                abi.encodePacked(
                    '","advisoryIDs":',
                    values.advisoryIDs,
                    ',"isvEnclaveQuoteStatus":"',
                    values.isvEnclaveQuoteStatus,
                    '","platformInfoBlob":"',
                    values.platformInfoBlob,
                    '","isvEnclaveQuoteBody":"',
                    values.isvEnclaveQuoteBody,
                    '"',
                    '}'
                )
            )
        );
    }
}