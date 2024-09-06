import {Context, Contract, Info, Returns, Transaction} from 'fabric-contract-api';
import stringify from "json-stringify-deterministic";
import sortKeysRecursive from 'sort-keys-recursive';
import {Options, PythonShell} from "python-shell";
import Long from "long";

const ClientIdentity = require('fabric-shim').ClientIdentity;

@Info({title: 'YaramoContract', description: 'Smart contract for managing yaramo instances'})
export class YaramoContract extends Contract {
    private ContainsApprovedState(topology) {
        for (const state in topology.status_information) {
            if (Number(state) > 2) {
                return true
            }
        }
        return false
    }

    @Transaction()
    public async CreateTopology(ctx: Context, id: string, topology_json: string): Promise<void> {
        const exists = await this.TopologyExists(ctx, id);
        const topology = JSON.parse(topology_json)
        if (exists) {
            throw new Error(`The topology ${id} already exists`);
        }

        if (topology.current_status > 2 || this.ContainsApprovedState(topology)) {
            throw new Error(`The topology may not be created in an approved state!`);
        }

        let cid = new ClientIdentity(ctx.stub);

        if (!await this.IsValidTopology(ctx, topology_json)) {
            throw new Error("The given topology is not valid!");
        }

        // we insert data in alphabetic order using 'json-stringify-deterministic' and 'sort-keys-recursive'
        await ctx.stub.putState(id, Buffer.from(stringify(sortKeysRecursive(topology))));
    }

    @Transaction(false)
    @Returns('boolean')
    public async IsValidTopology(ctx: Context, topology_json: string): Promise<boolean> {
        try {
            JSON.parse(topology_json);
        } catch(SyntaxError) {
            return false
        }

        let options = {
            mode: 'text',
            pythonPath: 'venv/bin/python',
            pythonOptions: ['-u'],
            args: [topology_json]
        };

        return PythonShell.run('verify_yaramo_instance.py', options as Options).then(messages => {
            console.log('results: %j', messages);
            return true
        }).catch(error => {console.log(error.message); return false;});
    }

    @Transaction(false)
    public async GetTopologyList(ctx: Context): Promise<any> {
        let results = [];
        const response = await ctx.stub.getStateByRangeWithPagination("", "", 10, "");
        while (true) {
            let item = await response.iterator.next()
            if (item.done) {
                break
            }
            results.push(item.value.key)
        }
        await response.iterator.close()
        return results;
    }

    @Transaction(false)
    public async ReadTopology(ctx: Context, id: string): Promise<string> {
        const topologyJSON = await ctx.stub.getState(id); // get the asset from chaincode state
        if (!topologyJSON || topologyJSON.length === 0) {
            throw new Error(`The topology ${id} does not exist`);
        }
        return topologyJSON.toString();
    }

    @Transaction(false)
    @Returns('boolean')
    public async TopologyExists(ctx: Context, id: string): Promise<boolean> {
        const topologyJSON = await ctx.stub.getState(id);
        return topologyJSON && topologyJSON.length > 0;
    }

    @Transaction()
    public async UpdateTopology(ctx: Context, id: string, topology_json: string): Promise<void> {
        const exists = await this.TopologyExists(ctx, id);
        const topology = JSON.parse(topology_json);
        if (!exists) {
            throw new Error(`The topology ${id} does not exist`);
        }

        if (topology.current_status > 2 || this.ContainsApprovedState(topology)) {
            throw new Error(`The topology may not be created in an approved state!`);
        }

        if (!await this.IsValidTopology(ctx, topology_json)) {
            throw new Error("The given topology is not valid!");
        }

        // we insert data in alphabetic order using 'json-stringify-deterministic' and 'sort-keys-recursive'
        await ctx.stub.putState(id, Buffer.from(stringify(sortKeysRecursive(topology))));
    }

    @Transaction()
    public async ApproveTopology(ctx: Context, id: string): Promise<void> {
        const topology = JSON.parse(await this.ReadTopology(ctx, id));

        const current_state = topology.current_status
        if (current_state > 2 || this.ContainsApprovedState(topology)) {
            throw new Error(`The topology ${id} is not in a state in which it could be approved`);
        }

        let cid = new ClientIdentity(ctx.stub);
        if (!cid.assertAttributeValue("planpruefer", "true")) {
            throw new Error(`Only users with the planpruefer attribute may approve topologies!`);
        }

        topology["current_status"] = 3
        topology.status_information[3] = {
            "name": cid.getID(),
            "organization": cid.getMSPID(),
            "date": new Date().toISOString().slice(0, 10)
        }

        // we insert data in alphabetic order using 'json-stringify-deterministic' and 'sort-keys-recursive'
        await ctx.stub.putState(id, Buffer.from(stringify(sortKeysRecursive(topology))));
    }

    @Transaction(false)
    public async GetHistory(ctx: Context, id: string): Promise<Array<[Long, string, string]>> {
        const exists = await this.TopologyExists(ctx, id);
        if (!exists) {
            throw new Error(`The topology ${id} does not exist`);
        }

        var item_history = await ctx.stub.getHistoryForKey(id);
        const allResults: Array<[Long, string, string]> = [];
        while (true) {
            const res = await item_history.next();
            if (res.done) {
                await item_history.close();
                return allResults;
            }
            allResults.push([res.value.timestamp.seconds, res.value.txId, res.value.value.toString()]);
        }
    }

    @Transaction(false)
    public async TestPython(ctx: Context, source: string): Promise<boolean> {

        let options = {
            mode: 'text',
            pythonPath: 'venv/bin/python',
            pythonOptions: ['-u'],
            args: [source]
        };

        return PythonShell.run('verify_yaramo_instance.py', options as Options).then(messages => {
            console.log('results: %j', messages);
            return true
        }).catch(error => {console.log(error.message); return false;});
    }
}
