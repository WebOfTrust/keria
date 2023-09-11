import { Agent, Controller } from "./controller"
import { Tier } from "../core/salter"
import { Authenticater } from "../core/authing"
import { KeyManager } from "../core/keeping"
import { Serder } from "../core/serder"

import { Identifier } from "./aiding"
import { Contacts, Challenges } from "./contacting"
import { Oobis, Operations, KeyEvents, KeyStates } from "./coring"
import { Credentials, Registries, Schemas, } from './credentialing'
import { Notifications } from "./notifying"
import { Escrows } from "./escrowing"
import { Groups } from "./grouping"
import { Exchanges } from "./exchanging"

const DEFAULT_BOOT_URL = "http://localhost:3903"

class State {
    agent: any | null
    controller: any | null
    ridx: number
    pidx: number

    constructor() {
        this.agent = null
        this.controller = null
        this.pidx = 0
        this.ridx = 0
    }
}

/** SignifyClient */
export class SignifyClient {
    public controller: Controller
    public url: string
    public bran: string
    public pidx: number
    public agent: Agent | null
    public authn: Authenticater | null
    public manager: KeyManager | null
    public tier: Tier
    public bootUrl: string

    /**
     * SignifyClient constructor
     * @param {string} url KERIA admin interface URL
     * @param {string} bran Base64 21 char string that is used as base material for seed of the client AID
     * @param {Tier} tier Security tier for generating keys of the client AID (high | mewdium | low)
     * @param {string} bootUrl KERIA boot interface URL
     */
    constructor(url: string, bran: string, tier: Tier = Tier.low, bootUrl: string = DEFAULT_BOOT_URL) {
        this.url = url
        if (bran.length < 21) {
            throw Error("bran must be 21 characters")
        }
        this.bran = bran
        this.pidx = 0
        this.controller = new Controller(bran, tier)
        this.authn = null
        this.agent = null
        this.manager = null
        this.tier = tier
        this.bootUrl = bootUrl
    }

    get data() {
        return [this.url, this.bran, this.pidx, this.authn]
    }

    /** 
     * Boot a KERIA agent
     * @async
     * @returns {Promise<Response>} A promise to the result of the boot
     */
    async boot(): Promise<Response> {
        const [evt, sign] = this.controller?.event ?? [];
        const data = {
            icp: evt.ked,
            sig: sign.qb64,
            stem: this.controller?.stem,
            pidx: 1,
            tier: this.controller?.tier
        };

        return await fetch(this.bootUrl + "/boot", {
            method: "POST",
            body: JSON.stringify(data),
            headers: {
                "Content-Type": "application/json"
            }
        });

    }

    /** 
     * Get state of the agent and the client
     * @async
     * @returns {Promise<Response>} A promise to the state
     */
    async state(): Promise<State> {
        const caid = this.controller?.pre

        let res = await fetch(this.url + `/agent/${caid}`);
        if (res.status == 404) {
            throw new Error(`agent does not exist for controller ${caid}`);
        }

        const data = await res.json();
        let state = new State();
        state.agent = data.agent ?? {};
        state.controller = data.controller ?? {};
        state.ridx = data.ridx ?? 0;
        state.pidx = data.pidx ?? 0;
        return state;
    }

    /**  Connect to a KERIA agent
    * @async
    */
    async connect() {
        const state = await this.state()
        this.pidx = state.pidx
        //Create controller representing the local client AID
        this.controller = new Controller(this.bran, this.tier, 0, state.controller)
        this.controller.ridx = state.ridx !== undefined ? state.ridx : 0
        // Create agent representing the AID of KERIA cloud agent
        this.agent = new Agent(state.agent)
        if (this.agent.anchor != this.controller.pre) {
            throw Error("commitment to controller AID missing in agent inception event")
        }
        if (this.controller.serder.ked.s == 0) {
            await this.approveDelegation()
        }
        this.manager = new KeyManager(this.controller.salter, null)
        this.authn = new Authenticater(this.controller.signer, this.agent.verfer!)
    }

    /**
    * Fetch a resource from the KERIA agent
    * @async
    * @param {string} path Path to the resource
    * @param {string} method HTTP method
    * @param {any} data Data to be sent in the body of the resource
    * @param {Headers} [extraHeaders] Optional extra headers to be sent with the request
    * @returns {Promise<Response>} A promise to the result of the fetch
    */
    async fetch(path: string, method: string, data: any, extraHeaders?: Headers): Promise<Response> {
        let headers = new Headers()
        let signed_headers = new Headers()
        let final_headers = new Headers()

        headers.set('Signify-Resource', this.controller.pre)
        headers.set('Signify-Timestamp', new Date().toISOString().replace('Z', '000+00:00'))
        headers.set('Content-Type', 'application/json')

        let _body = method == 'GET' ? null : JSON.stringify(data)
        if (_body !== null) {
            headers.set('Content-Length', String(_body.length))
        }
        if (this.authn) {
            signed_headers = this.authn.sign(headers, method, path.split('?')[0])
        } else {
            throw new Error('client need to call connect first')
        }

        signed_headers.forEach((value, key) => {
            final_headers.set(key, value)
        })
        if (extraHeaders !== undefined) {
            extraHeaders.forEach((value, key) => {
                final_headers.append(key, value)
            })
        }
        let res = await fetch(this.url + path, {
            method: method,
            body: _body,
            headers: final_headers
        });
        if (!(res.status == 200 || res.status == 202 || res.status == 206)) {
            const error = await res.text()
            throw new Error(error)
        }
        const isSameAgent = this.agent?.pre === res.headers.get('signify-resource');
        if (!isSameAgent) {
            throw new Error('message from a different remote agent');
        }

        const verification = this.authn.verify(res.headers, method, path.split('?')[0]);
        if (verification) {
            return res;
        } else {
            throw new Error('response verification failed');
        }
    }

    /**
     * Fetch a resource from from an external URL with headers signed by an AID
     * @async
     * @param {string} url URL of the resource 
     * @param {string} path Path to the resource
     * @param {string} method HTTP method 
     * @param {any} data Data to be sent in the body of the resource
     * @param {string} aidName Name or alias of the AID to be used for signing
     * @returns {Promise<Response>} A promise to the result of the fetch
     */
    async signedFetch(url: string, path: string, method: string, data: any, aidName: string): Promise<Response> {
        const hab = await this.identifiers().get(aidName)
        const keeper = this.manager!.get(hab)

        const authenticator = new Authenticater(keeper.signers[0], keeper.signers[0].verfer)

        let headers = new Headers()
        headers.set('Signify-Resource', hab.prefix)
        headers.set('Signify-Timestamp', new Date().toISOString().replace('Z', '000+00:00'))

        if (data !== null) {
            headers.set('Content-Length', data.length)
        }
        else {
            headers.set('Content-Length', '0')
        }
        let signed_headers = authenticator.sign(headers, method, path.split('?')[0])
        let _body = null
        if (method != 'GET') {
            if (data instanceof FormData) {
                _body = data
                // do not set the content type, let the browser do it
                // headers.set('Content-Type', 'multipart/form-data')
            } else {
                _body = JSON.stringify(data)
                headers.set('Content-Type', 'application/json')
            }
        } else {
            headers.set('Content-Type', 'application/json')
        }

        return await fetch(url + path, {
            method: method,
            body: _body,
            headers: signed_headers
        });

    }

    /**
     * Approve the delegation of the client AID to the KERIA agent
     * @async
     * @returns {Promise<Response>} A promise to the result of the approval
     */
    async approveDelegation(): Promise<Response> {
        let sigs = this.controller.approveDelegation(this.agent!)

        let data = {
            ixn: this.controller.serder.ked,
            sigs: sigs
        }

        return await fetch(this.url + "/agent/" + this.controller.pre + "?type=ixn", {
            method: "PUT",
            body: JSON.stringify(data),
            headers: {
                "Content-Type": "application/json"
            }
        })
    }

    /**
    * Save old client passcode in KERIA agent
    * @async
    * @param {string} passcode Passcode to be saved
    * @returns {Promise<Response>} A promise to the result of the save
    */
    async saveOldPasscode(passcode: string): Promise<Response> {
        const caid = this.controller?.pre;
        const body = { salt: passcode };
        return await fetch(this.url + "/salt/" + caid, {
            method: "PUT",
            body: JSON.stringify(body),
            headers: {
                "Content-Type": "application/json"
            }
        })
    }

    /**
    * Delete a saved passcode from KERIA agent
    * @async
    * @returns {Promise<Response>} A promise to the result of the deletion
    */
    async deletePasscode(): Promise<Response> {
        const caid = this.controller?.pre;
        return await fetch(this.url + "/salt/" + caid, {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json"
            }
        })
    }

    /**
    * Rotate the client AID
    * @async
    * @param {string} nbran Base64 21 char string that is used as base material for the new seed
    * @param {Array<string>} aids List of managed AIDs to be rotated
    * @returns {Promise<Response>} A promise to the result of the rotation
    */
    async rotate(nbran: string, aids: string[]): Promise<Response> {
        let data = this.controller.rotate(nbran, aids)
        return await fetch(this.url + "/agent/" + this.controller.pre, {
            method: "PUT",
            body: JSON.stringify(data),
            headers: {
                "Content-Type": "application/json"
            }
        })
    }

    /**
    * Get identifiers resource
    * @returns {Identifier} 
    */
    identifiers(): Identifier {
        return new Identifier(this)
    }

    /**
    * Get OOBIs resource
    * @returns {Oobis}
    */
    oobis(): Oobis {
        return new Oobis(this)
    }

    /**
    * Get operations resource
    * @returns {Operations}
    */
    operations(): Operations {
        return new Operations(this)
    }

    /**
    * Get keyEvents resource
    * @returns {KeyEvents}
    */
    keyEvents(): KeyEvents {
        return new KeyEvents(this)
    }

    /**
    * Get keyStates resource
    * @returns {KeyStates}
    */
    keyStates(): KeyStates {
        return new KeyStates(this)
    }

    /**
    * Get credentials resource
    * @returns {Credentials}
    */
    credentials(): Credentials {
        return new Credentials(this)
    }

    /**
    * Get registries resource
    * @returns {Registries}
    */
    registries(): Registries {
        return new Registries(this)
    }

    /**
    * Get schemas resource
    * @returns {Schemas}
    */
    schemas(): Schemas {
        return new Schemas(this)
    }

    /**
    * Get challenges resource
    * @returns {Challenges}
    */
    challenges(): Challenges {
        return new Challenges(this)
    }

    /**
    * Get contacts resource
    * @returns {Contacts}
    */
    contacts(): Contacts {
        return new Contacts(this)
    }

    /**
    * Get notifications resource
    * @returns {Notifications}
    */
    notifications(): Notifications {
        return new Notifications(this)
    }

    /**
    * Get escrows resource
    * @returns {Escrows}
    */
    escrows(): Escrows {
        return new Escrows(this)
    }

    /**
    * Get groups resource
    * @returns {Groups}
    */
    groups(): Groups {
        return new Groups(this)
    }

    /**
    * Get exchange resource
    * @returns {Exchanges}
    */
    exchanges(): Exchanges {
        return new Exchanges(this)
    }
}

export class EventResult {
    private readonly _serder: Serder
    private readonly _sigs: string[]
    private readonly promise: Promise<Response>

    constructor(serder: Serder, sigs: string[], promise: Promise<Response>) {
        this._serder = serder
        this._sigs = sigs
        this.promise = promise
    }

    get serder() {
        return this._serder
    }

    get sigs() {
        return this._sigs
    }

    async op(): Promise<any> {
        let res = await this.promise
        return await res.json()
    }
}