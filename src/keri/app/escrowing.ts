import { SignifyClient } from "./clienting"


/**
 * Escrows
 */
export class Escrows {
    client: SignifyClient

    /**
     * Escrows
     * @param {SignifyClient} client 
     */
    constructor(client: SignifyClient) {
        this.client = client
    }

    /**
     * List replay messages
     * @async
     * @param {string} [route] Optional route in the replay message 
     * @returns {Promise<any>} A promise to the list of replay messages
     */
    async listReply(route?:string): Promise<any> {
        let params = new URLSearchParams()
        if (route !== undefined) {params.append('route', route)}

        let path = `/escrows/rpy` + '?' + params.toString()
        let method = 'GET'
        let res =  await this.client.fetch(path, method, null)
        return await res.json()
    }
}
