import {Context, Contract, Info, Returns, Transaction} from 'fabric-contract-api';
import stringify from "json-stringify-deterministic";
import sortKeysRecursive from 'sort-keys-recursive';
import {Options, PythonShell} from "python-shell";

@Info({title: 'YaramoContract', description: 'Smart contract for managing yaramo instances'})
export class YaramoContract extends Contract {
    @Transaction()
    public async CreateTopology(ctx: Context, id: string, topology_json: string): Promise<void> {
        const exists = await this.TopologyExists(ctx, id);
        if (exists) {
            throw new Error(`The topology ${id} already exists`);
        }

        if (!await this.IsValidTopology(ctx, topology_json)) {
            throw new Error("The given topology is not valid!");
        }

        // we insert data in alphabetic order using 'json-stringify-deterministic' and 'sort-keys-recursive'
        await ctx.stub.putState(id, Buffer.from(stringify(sortKeysRecursive(JSON.parse(topology_json)))));
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
    public async UpdateAsset(ctx: Context, id: string, edges: string, nodes: string, objects: string, routes: string, signals: string, vacancy_sections: string): Promise<void> {
        const exists = await this.TopologyExists(ctx, id);
        if (!exists) {
            throw new Error(`The topology ${id} does not exist`);
        }

        const updatedTopology = {
            edges: edges,
            nodes: nodes,
            routes: routes,
            signals: signals,
            vacancy_sections: vacancy_sections,
        };
        // we insert data in alphabetic order using 'json-stringify-deterministic' and 'sort-keys-recursive'
        return ctx.stub.putState(id, Buffer.from(stringify(sortKeysRecursive(updatedTopology))));
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
