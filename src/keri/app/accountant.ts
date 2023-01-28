import {Manager} from "../core/manager";


export class Accountant {
    private readonly _agentKey: string
    private readonly _mgr: Manager
    private readonly _ready: Promise<void>

    /*
    *   Accountant is responsible for managing signing keys for the client and agent.  The client
    *   signing key represents the Account for the client on the agent
    *
    */
    constructor(mgr: Manager, agentKey: string) {
        this._mgr = mgr
        this._agentKey = agentKey
        this._ready = new Promise<void>(()=>{})
    }

    get ready(): Promise<void> {
        return this._ready
    }


    sign() {
        return this._mgr

    }

    verify() {
        return this._agentKey
    }


}