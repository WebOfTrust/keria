import { SignifyClient } from "./clienting"
import libsodium from "libsodium-wrappers-sumo";
import { Salter } from "../core/salter";
import { Matter, MtrDex } from '../core/matter';

export function randomPasscode(): string {
    let raw = libsodium.randombytes_buf(16);
    let salter = new Salter({ raw: raw })

    return salter.qb64.substring(2)
}

export function randomNonce(): string {
    let seed = libsodium.randombytes_buf(libsodium.crypto_sign_SEEDBYTES);
    let seedqb64 = new Matter({ raw: seed, code: MtrDex.Ed25519_Seed });
    return seedqb64.qb64;
}

export class Oobis {
    public client: SignifyClient
    /**
     * Oobis
     * @param {SignifyClient} client 
     */
    constructor(client: SignifyClient) {
        this.client = client
    }

    /**
     * Get the OOBI(s) for a managed indentifier for a given role
     * @param {string} name Name or alias of the identifier
     * @param {string} role Authorized role
     * @returns {Promise<any>} A promise to the OOBI(s)
     */
    async get(name: string, role: string = 'agent'): Promise<any> {
        let path = `/identifiers/${name}/oobis?role=${role}`
        let method = 'GET'
        let res = await this.client.fetch(path, method, null)
        return await res.json()

    }

    /**
     * Resolve an OOBI
     * @async
     * @param {string} oobi The OOBI to be resolver
     * @param {string} [alias] Optional name or alias to link the OOBI resolution to a contact 
     * @returns {Promise<any>} A promise to the long-running operation
     */
    async resolve(oobi: string, alias?: string): Promise<any> {
        let path = `/oobis`
        let data: any = {
            url: oobi
        }
        if (alias !== undefined) {
            data.oobialias = alias
        }
        let method = 'POST'
        let res = await this.client.fetch(path, method, data)
        return await res.json()

    }
}

/**
 * Operations
 * @remarks
 * Operations represent the status and result of long running tasks performed by KERIA agent
 */
export class Operations {
    public client: SignifyClient
    /**
     * Operations
     * @param {SignifyClient} client 
     */
    constructor(client: SignifyClient) {
        this.client = client
    }

    /**
     * Get operation status
     * @async
     * @param {string} name Name of the operation
     * @returns {Promise<any>} A promise to the status of the operation
     */
    async get(name: string): Promise<any> {
        let path = `/operations/${name}`
        let data = null
        let method = 'GET'
        let res = await this.client.fetch(path, method, data)
        return await res.json()

    }
}

/**
 * KeyEvents
 */
export class KeyEvents {
    public client: SignifyClient
    /**
     * KeyEvents
     * @param {SignifyClient} client 
     */
    constructor(client: SignifyClient) {
        this.client = client
    }

    /**
     * Retrieve key events for an identifier
     * @async
     * @param {string} pre Identifier prefix
     * @returns {Promise<any>} A promise to the key events
     */
    async get(pre: string): Promise<any> {
        let path = `/events?pre=${pre}`
        let data = null
        let method = 'GET'
        let res = await this.client.fetch(path, method, data)
        return await res.json()

    }
}

/**
 * KeyStates
 */
export class KeyStates {
    public client: SignifyClient
    /**
     * KeyStates
     * @param {SignifyClient} client 
     */
    constructor(client: SignifyClient) {
        this.client = client
    }

    /**
     * Retriene the key state for an identifier
     * @async
     * @param {string} pre Identifier prefix
     * @returns {Promise<any>} A promise to the key states
     */
    async get(pre: string): Promise<any> {
        let path = `/states?pre=${pre}`
        let data = null
        let method = 'GET'
        let res = await this.client.fetch(path, method, data)
        return await res.json()

    }

    /**
     * Retrieve the key state for a list of identifiers
     * @async
     * @param {Array<string>} pres List of identifier prefixes
     * @returns {Promise<any>} A promise to the key states
     */
    async list(pres: string[]): Promise<any> {
        let path = `/states?${pres.map(pre => `pre=${pre}`).join('&')}`
        let data = null
        let method = 'GET'
        let res = await this.client.fetch(path, method, data)
        return await res.json()

    }

    /**
     * Query the key state of an identifier for a given sequence number or anchor SAID
     * @async
     * @param {string} pre Identifier prefix
     * @param {number} [sn] Optional sequence number
     * @param {string} [anchor] Optional anchor SAID
     * @returns {Promise<any>} A promise to the long-running operation
     */
    async query(pre: string, sn?: number, anchor?: string): Promise<any> {
        let path = `/queries`
        let data: any = {
            pre: pre
        }
        if (sn !== undefined) {
            data.sn = sn
        }
        if (anchor !== undefined) {
            data.anchor = anchor
        }

        let method = 'POST'
        let res = await this.client.fetch(path, method, data)
        return await res.json()
    }
}

