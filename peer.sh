#! /bin/bash
fabric_path=/home/julian/fabric/fabric
export PATH=$fabric_path/build/bin:$PATH
export FABRIC_CFG_PATH=config/
export CORE_OPERATIONS_LISTENADDRESS=127.0.0.1:9444
FABRIC_LOGGING_SPEC=chaincode=debug CORE_PEER_CHAINCODELISTENADDRESS=0.0.0.0:7052 peer node start --peer-chaincodedev=true
