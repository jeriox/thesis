import json
import os
from urllib.parse import urlencode, quote

from cryptography import x509
from datetime import datetime
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
org1_admin = cli.get_user('org1.example.com', 'user1')


# BCF-style Documents API
@app.post("/api/select-documents")
def select_documents():
    return app.json.response({
                                 "select_documents_url": f"{request.host_url}select-documents?callback={quote(request.get_json(force=True)["callback"]["url"])}",
                                 "expires_in": 60})


@app.get("/select-documents")
def select_documents_frontend():
    topology_list = json.loads(_query_chaincode("GetTopologyList", []))
    return render_template("api_select_documents.html", topology_list=topology_list)


def _get_document_version(id, version=1):
    current_version = json.loads(_query_chaincode("GetHistory", [id]))[0]
    return {
        "links": {
            "document_version": {
                "url": f"{request.host_url}api/documents/{id}/versions/v{version}.0"
            },
            "document_version_metadata": {
                "url": f"{request.host_url}api/documents/{id}/versions/v{version}.0/metadata"
            },
            "document_version_download": {
                "url": f"{request.host_url}api/documents/{id}/versions/v{version}.0/download"
            },
            "document_versions": {
                "url": f"{request.host_url}api/documents/{id}/versions"
            },
            "document_details": {
                "url": f"{request.host_url}topology/{id}/"
            }
        },
        "version_number": f"v{version}.0",
        "version_index": version,
        "creation_date": current_version[0],
        "title": "Sample Document",
        "file_description": {
            "name": f"{id}.ppxml",
            "size_in_bytes": 1234
        },
        "document_id": id
    }


@app.get("/api/documents/<id>/versions")
def document(id):
    data = {
        "documents": [
            _get_document_version(id)
        ]
    }
    return app.json.response(data)


@app.get("/api/documents/<id>/versions/<version>")
def document_version(id, version):
    return app.json.response(_get_document_version(id))


@app.get("/api/documents/<id>/versions/<version>/metadata")
def document_metadata(id, version):
    return app.json.response({})


@app.get("/api/documents/<id>/versions/<version>/download")
def document_download(id, version):
    return download_topology_json(id)


# Own frontend views
@app.route("/")
def home(error=None):
    topology_list = json.loads(_query_chaincode("GetTopologyList", []))
    return render_template("home.html", topology_list=topology_list, error=error)


@app.route("/api-client-callback")
def api_client_callback():
    return render_template("api_demo_callback.html", selected_documents_url=request.args.get("selected_documents_url"))


@app.get("/topology/<id>/")
def read_topology(id):
    topology_json = _query_chaincode("ReadTopology", [id])
    topology = Topology.from_json(topology_json)
    history = []
    for version in json.loads(_query_chaincode("GetHistory", [id])):
        dt = datetime.fromtimestamp(version[0])
        transaction = _query_transaction(version[1])
        cert = x509.load_pem_x509_certificate(
            transaction["transaction_envelope"]["payload"]["data"]["actions"][0]["header"]["creator"][
                "id_bytes"].encode())
        history.append((dt, cert.subject.rfc4514_string(), version[2]))
    return render_template("topology.html", id=id, topology=topology, topology_json=topology_json, history=history,
                           current_state_dict=topology.status_information.get(str(topology.current_status.value), None))


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


@app.post("/topology/<id>/approve/")
def approve_topology(id):
    if error := _invoke_chaincode("ApproveTopology", [id]):
        flash(error)
    return redirect(f"/topology/{id}")


@app.post("/topology/")
def create_topology():
    try:
        if "id_orm" in request.form:
            id = request.form["id_orm"]
            topology = ORMImporter().run(request.form["polygon"]).to_json()
            if _query_chaincode("TopologyExists", [id]) == "true":
                if error := _invoke_chaincode("UpdateTopology", [id, topology]):
                    raise Exception(error)
                # sleep(5)
            else:
                if error := _invoke_chaincode("CreateTopology", [id, topology]):
                    raise Exception(error)
            return redirect(f"/topology/{request.form["id_orm"]}/")
        file = request.files.get("planpro_file", None)
        if not (file and file.filename):
            raise Exception("No PlanPro file submitted!")
        filename = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
        file.save(filename)
        topology = PlanProReader(filename).read_topology_from_plan_pro_file().to_json()
        id = request.form["id_planpro"]
        if _query_chaincode("TopologyExists", [id]) == "true":
            if error := _invoke_chaincode("UpdateTopology", [id, topology]):
                raise Exception(error)
            # sleep(5)
        else:
            start = datetime.now()
            if error := _invoke_chaincode("CreateTopology", [request.form["id_planpro"], topology]):
                raise Exception(error)
            print(datetime.now() - start)
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


def _query_transaction(tx_id: str):
    return loop.run_until_complete(cli.query_transaction(
        requestor=org1_admin,
        channel_name="ch1",
        peers=['peer0.org1.example.com'],
        tx_id=tx_id
    ))
