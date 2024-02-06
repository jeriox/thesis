#! /bin/bash
CORE_CHAINCODE_LOGLEVEL=debug CORE_PEER_TLS_ENABLED=false CORE_CHAINCODE_ID_NAME=yaramo:1.0 npm start -- --peer.address 127.0.0.1:7052
