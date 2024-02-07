import json
from time import sleep

from flask import flash, Flask, render_template, request, redirect
import asyncio

from hfc.fabric import Client
from orm_importer.importer import ORMImporter

app = Flask(__name__)
app.secret_key = "secret"
loop = asyncio.get_event_loop()
cli = Client(net_profile="network.json")
cli.new_channel("ch1")
org1_admin = cli.get_user('org1.example.com', 'Admin')


@app.route("/")
def home(error=None):
    topology_list = json.loads(_query_chaincode("GetTopologyList", []))
    return render_template("home.html", topology_list=topology_list, error=error)


@app.get("/topology/<id>/")
def read_topology(id):
    topology = _query_chaincode("ReadTopology", [id])
    return render_template("topology.html", id=id, topology=topology)


@app.post("/topology/")
def create_topology():
    try:
        if "id_orm" in request.form:
            topology = ORMImporter().run(request.form["polygon"]).to_json()
            if error := _invoke_chaincode("CreateTopology", [request.form["id_orm"], topology]):
                raise Exception(error)
            sleep(1000)
            return redirect(f"/topology/{request.form["id_orm"]}/")
        return None
    except Exception as e:
        flash(f"Error creating topology: {e}")
        return redirect("/")


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
