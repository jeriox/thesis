import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument("yaramo_json")

args = parser.parse_args()
instance = json.loads(args.yaramo_json)
