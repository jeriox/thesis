import json
import os
from time import sleep

from flask import flash, Flask, render_template, request, redirect
import asyncio

from hfc.fabric import Client
from orm_importer.importer import ORMImporter
from planproexporter.generator import Generator
from planpro_importer.reader import PlanProReader
from yaramo.topology import Topology
from werkzeug.utils import secure_filename

# flask setup
app = Flask(__name__)
app.secret_key = "secret"
app.config["UPLOAD_FOLDER"] = "data"

# hyperledger setup
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


@app.get("/topology/<id>/json/")
def download_topology_json(id):
    topology = _query_chaincode("ReadTopology", [id])
    return app.response_class(topology, mimetype="text/json")


@app.get("/topology/<id>/planpro/")
def download_topology_planpro(id):
    topology_string = _query_chaincode("ReadTopology", [id])
    topology = Topology.from_json(topology_string)
    planpro = Generator().generate(topology)
    return app.response_class(planpro, mimetype="text/xml")


@app.post("/topology/")
def create_topology():
    try:
        if "id_orm" in request.form:
            topology = ORMImporter().run(request.form["polygon"]).to_json()
            if error := _invoke_chaincode("CreateTopology", [request.form["id_orm"], topology]):
                raise Exception(error)
            sleep(1000)
            return redirect(f"/topology/{request.form["id_orm"]}/")
        file = request.files.get("planpro_file", None)
        if not (file and file.filename):
            raise Exception("No PlanPro file submitted!")
        filename = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
        file.save(filename)
        topology = PlanProReader(filename).read_topology_from_plan_pro_file().to_json()
        if error := _invoke_chaincode("CreateTopology", [request.form["id_planpro"], topology]):
            raise Exception(error)
        sleep(1000)
        return redirect(f"/topology/{request.form["id_planpro"]}/")
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
