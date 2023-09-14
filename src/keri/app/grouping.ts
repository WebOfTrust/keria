import { SignifyClient } from "./clienting"
import { Dict} from "../core/core"

/**
 * Groups
 */
export class Groups {
    client: SignifyClient

    /**
     * Groups
     * @param {SignifyClient} client
     */
    constructor(client: SignifyClient) {
        this.client = client
    }

    /**
     * Get group request messages
     * @async
     * @param {string} [said] SAID of exn message to load
     * @returns {Promise<any>} A promise to the list of replay messages
     */
    async getRequest(said:string): Promise<any> {

        let path = `/multisig/request/` + said
        let method = 'GET'
        let res =  await this.client.fetch(path, method, null)
        return await res.json()
    }

    /**
     * Send multisig exn request  messages to other group members
     * @async
     * @param {string} [name] human readable name of group AID
     * @param {Dict<any>} [exn] exn message to send to other members
     * @param {string[]} [sigs] signature of the participant over the exn
     * @param {string} [atc] additional attachments from embedded events in exn
     * @returns {Promise<any>} A promise to the list of replay messages
     */
    async sendRequest(name: string, exn:Dict<any>, sigs: string[], atc: string): Promise<any> {

        let path = `/identifiers/${name}/multisig/request`
        let method = 'POST'
        let data = {
            exn: exn,
            sigs: sigs,
            atc: atc
        }
        let res = await this.client.fetch(path, method, data)
        return await res.json()
    }
}
