# thesis
This repository contains the prototype implementation for my master thesis. It is divided into the startscripts for the
nodes (orderer.sh and peer.sh), the channel configuration (/config), the web interface (/app) and the chaincode (/yaramo-chaincode).

In order to run the code, you need to set up the network first:

1. Install [Hyperledger Fabric](https://hyperledger-fabric.readthedocs.io/en/release-2.5/install.html). Enter the location into peer.sh and orderer.sh
2. Set up [Hyperledger CA](https://hyperledger-fabric-ca.readthedocs.io/en/latest/) and create key material. Alternatively, you can use the keys provided in the fabric-ca directory for testing. Make sure the config files in the config directory point to the correct path to the certificate.
2. Follow the [Hyperledger Fabric Tutorial](https://hyperledger-fabric.readthedocs.io/en/release-2.5/peer-chaincode-devmode.html), but make sure to point `FABRIC_CFG_PATH` to the config folder of this repository.
3. All changes to the config files also need to be reflected in the network.json in the app directory.
4. Make sure to have Python and a JRE available.
5. Install the python requirements in the chaincode directory and download railml2b.jar to there.

Afterwards, you can start the peer, orderer and chaincode with the respective scripts in this repository.

When all network components are running, you can start the flask app from the app directory and visit it on localhost:5000