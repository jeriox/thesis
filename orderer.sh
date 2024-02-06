#! /bin/bash
fabric_path=/home/julian/fabric/fabric
export PATH=$fabric_path/build/bin:$PATH
export FABRIC_CFG_PATH=$fabric_path/sampleconfig
ORDERER_GENERAL_GENESISPROFILE=SampleDevModeSolo orderer
