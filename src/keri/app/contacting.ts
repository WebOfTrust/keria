import { SignifyClient } from "./clienting"
import { messagize} from "../core/eventing"
import {b, Ident, Ilks, Serials, versify} from "../core/core"
import {Saider} from "../core/saider"
import {Serder} from "../core/serder"
import {Siger} from "../core/siger"
import {TextDecoder} from "util"

/**
 * Contacts
 */
export class Contacts {
    client: SignifyClient
    /**
     * Contacts
     * @param {SignifyClient} client 
     */
    constructor(client: SignifyClient) {
        this.client = client
    }

    /**
     * List contacts
     * @async
     * @param {string} [group] Optional group name to filter contacts 
     * @param {string} [filterField] Optional field name to filter contacts
     * @param {string} [filterValue] Optional field value to filter contacts
     * @returns {Promise<any>} A promise to the list of contacts
     */
    async list(group?:string, filterField?:string, filterValue?:string): Promise<any> {
        let params = new URLSearchParams()
        if (group !== undefined) {params.append('group', group)}
        if (filterField !== undefined && filterValue !== undefined) {
            params.append("filter_field", filterField);
            params.append("filter_value", filterValue);
        }

        let path = `/contacts`+ '?' + params.toString()
        let method = 'GET'
        let res = await this.client.fetch(path, method, null)
        return await res.json()

    }

    /**
     * Get a contact
     * @async
     * @param {string} pre Prefix of the contact
     * @returns {Promise<any>} A promise to the contact
     */
    async get(pre:string): Promise<any> {

        let path = `/contacts/`+ pre
        let method = 'GET'
        let res = await this.client.fetch(path, method, null)
        return await res.json()

    }

    /**
     * Add a contact
     * @async
     * @param {string} pre Prefix of the contact
     * @param {any} info Information about the contact
     * @returns {Promise<any>} A promise to the result of the addition
     */
    async add(pre: string, info: any): Promise<any> {
        let path = `/contacts/`+ pre
        let method = 'POST'

        let res = await this.client.fetch(path, method, info)
        return await res.json()
    }

    /**
     * Delete a contact
     * @async
     * @param {string} pre Prefix of the contact
     * @returns {Promise<any>} A promise to the result of the deletion
     */
    async delete(pre: string): Promise<any> {
        let path = `/contacts/`+ pre
        let method = 'DELETE'

        let res = await this.client.fetch(path, method, null)
        return await res.json()
    }

    /**
     * Update a contact
     * @async
     * @param {string} pre Prefix of the contact
     * @param {any} info Updated information about the contact
     * @returns {Promise<any>} A promise to the result of the update
     */
    async update(pre: string, info: any): Promise<any> {
        let path = `/contacts/` + pre
        let method = 'PUT'

        let res = await this.client.fetch(path, method, info)
        return await res.json()
    }

}


/**
 * Challenges
 */
export class Challenges {
    client: SignifyClient
    /**
     * Challenges
     * @param {SignifyClient} client 
     */
    constructor(client: SignifyClient) {
        this.client = client
    }

    /**
     * Generate a random challenge word list based on BIP39
     * @async
     * @param {number} strength Integer representing the strength of the challenge. Typically 128 or 256
     * @returns {Promise<any>} A promise to the list of random words
     */
    async generate(strength: number = 128): Promise<any> {
        let path = `/challenges?strength=${strength.toString()}`
        let method = 'GET'
        let res = await this.client.fetch(path, method, null)
        return await res.json()
    }

    /**
     * Respond to a challenge by signing a message with the list of words
     * @async
     * @param {string} name Name or alias of the identifier
     * @param {string} recipient Prefix of the recipient of the response
     * @param {Array<string>} words List of words to embed in the signed response
     * @returns {Promise<Response>} A promise to the result of the response
     */
    async respond(name: string, recipient: string, words: string[]): Promise<Response> {
        let path = `/challenges/${name}`
        let method = 'POST'

        let hab = await this.client.identifiers().get(name)
        let pre: string = hab.prefix
        let data = {
            i: pre,
            words: words
        }

        const vs = versify(Ident.KERI, undefined, Serials.JSON, 0)

        const _sad = {
            v: vs,
            t: Ilks.exn,
            d: "",
            dt: new Date().toISOString().replace("Z","000+00:00"),
            r: "/challenge/response",
            q: {},
            a: data
        }
        const [, sad] = Saider.saidify(_sad)
        const exn = new Serder(sad)

        let keeper = this.client!.manager!.get(hab)

        let sig = keeper.sign(b(exn.raw),true)

        let siger = new Siger({qb64:sig[0]})
        let seal = ["SealLast" , {i:pre}]
        let ims = messagize(exn,[siger],seal, undefined, undefined, true)
        ims = ims.slice(JSON.stringify(exn.ked).length)

        let jsondata = {
            recipient: recipient,
            words: words,
            exn: exn.ked,
            sig: new TextDecoder().decode(ims)
        }

        return await this.client.fetch(path, method, jsondata)
    }

    /**
     * Accept a challenge response as valid (list of words are correct)
     * @param {string} name Name or alias of the identifier
     * @param {string} pre Prefix of the identifier that was challenged
     * @param {string} said SAID of the challenge response message
     * @returns {Promise<Response>} A promise to the result of the response
     */
    async accept(name: string, pre: string, said: string): Promise<Response> {
        let path = `/challenges/${name}`
        let method = 'PUT'
        let data = {
            aid: pre,
            said: said
        }
        let res = await this.client.fetch(path, method, data)

        return res
    }
}
