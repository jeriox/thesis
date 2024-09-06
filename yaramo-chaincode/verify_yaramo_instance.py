import argparse
from railml_exporter.exporter import Exporter
from yaramo.topology import Topology
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("yaramo_json")

args = parser.parse_args()
topology = Topology.from_json(args.yaramo_json)
railml_filename = f"data/topology_{topology.uuid}.xml"
Exporter(topology).to_file(railml_filename)
result = subprocess.run(["java", "-jar", "railml2b.jar", railml_filename], capture_output=True, encoding="utf-8")
result.check_returncode()
