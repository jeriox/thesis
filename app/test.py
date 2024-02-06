import asyncio

from hfc.fabric import Client
from orm_importer.importer import ORMImporter

loop = asyncio.get_event_loop()
cli = Client(net_profile="network.json")
cli.new_channel("ch1")
org1_admin = cli.get_user('org1.example.com', 'Admin')
polygon = "52.396710577108536 13.136837482452394 52.394982231507285 13.135807514190676 52.39248124796051 13.11572313308716 52.39436681938324 13.114843368530275"
topology = ORMImporter().run(polygon)
response = loop.run_until_complete(cli.chaincode_query(
               requestor=org1_admin,
               channel_name='ch1',
               peers=['peer0.org1.example.com'],
               fcn="TestPython",
               args=[topology.to_json()],
               cc_name='yaramo'
               ))
print(response)
