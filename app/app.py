from flask import Flask, render_template
import asyncio

from hfc.fabric import Client
from orm_importer.importer import ORMImporter

app = Flask(__name__)
loop = asyncio.get_event_loop()
cli = Client(net_profile="network.json")
cli.new_channel("ch1")
org1_admin = cli.get_user('org1.example.com', 'Admin')


@app.route("/")
def home():
    return render_template("home.html")


@app.get("/topology/<id>")
def read_topology(id):
    return _query_chaincode("ReadTopology", [id])


@app.get("/topology/new/")
def create_topology():
    polygon = "52.396710577108536 13.136837482452394 52.394982231507285 13.135807514190676 52.39248124796051 13.11572313308716 52.39436681938324 13.114843368530275"
    topology = ORMImporter().run(polygon).to_json()
    return _invoke_chaincode("CreateTopology", ["id3", topology])


@app.get("/topology/")
def topology_list():
    return _query_chaincode("GetTopologyList", [])

def _query_chaincode(func, args):
    return loop.run_until_complete(cli.chaincode_query(
        requestor=org1_admin,
        channel_name='ch1',
        peers=['peer0.org1.example.com'],
        fcn=func,
        args=args,
        cc_name='yaramo'
    ))


def _invoke_chaincode(func, args):
    return loop.run_until_complete(cli.chaincode_invoke(
        requestor=org1_admin,
        channel_name='ch1',
        peers=['peer0.org1.example.com'],
        fcn=func,
        args=args,
        cc_name='yaramo'
    ))
