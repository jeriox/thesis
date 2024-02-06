#! /bin/bash
fabric_path=/home/julian/fabric/fabric
export PATH=$fabric_path/build/bin:$PATH
export FABRIC_CFG_PATH=$fabric_path/sampleconfig
echo $1
CORE_PEER_ADDRESS=127.0.0.1:7051 peer chaincode invoke -o 127.0.0.1:7050 -C ch1 -n yaramo -c $1
