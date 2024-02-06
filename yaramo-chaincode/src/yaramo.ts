import {Object, Property} from 'fabric-contract-api';

@Object()
export class Topology {
    @Property()
    public ID: string;

    // Properties must be in alphabetical order!
    @Property()
    public edges: string;

    @Property()
    public nodes?: string;

    @Property()
    public objects: string;

    @Property()
    public routes: string;

    @Property()
    public signals: string;

    @Property()
    public vacancy_sections: string;
}
