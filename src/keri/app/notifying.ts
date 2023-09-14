import { SignifyClient } from "./clienting"
import {parseRangeHeaders} from "../core/httping"

/**
 * Notifications
 */
export class Notifications {
    client: SignifyClient

    /**
     * Notifications
     * @param {SignifyClient} client 
     */
    constructor(client: SignifyClient) {
        this.client = client
    }

    /**
     * List notifications
     * @async
     * @param {number} [start=0] Start index of list of notifications, defaults to 0
     * @param {number} [end=24] End index of list of notifications, defaults to 24
     * @returns {Promise<any>} A promise to the list of notifications
     */
    async list(start:number=0, end:number=24): Promise<any> {
        let extraHeaders = new Headers()
        extraHeaders.append('Range', `notes=${start}-${end}`)
        
        let path = `/notifications`
        let method = 'GET'
        let res = await this.client.fetch(path, method, null, extraHeaders)

        let cr = res.headers.get('content-range')
        let range = parseRangeHeaders(cr,"notes")
        let notes = await res.json()

        return {
            start: range.start,
            end: range.end,
            total: range.total,
            notes: notes
        }
    }

    /**
     * Mark a notification as read
     * @async
     * @param {string} said SAID of the notification
     * @returns {Promise<string>} A promise to the result of the marking
     */
    async mark(said:string): Promise<string> {
        let path = `/notifications/`+ said
        let method = 'PUT'
        let res = await this.client.fetch(path, method, null)
        return await res.text()
    }

    /**
     * Delete a notification
     * @async
     * @param {string} said SAID of the notification
     * @returns {Promise<any>} A promise to the result of the deletion
     */
    async delete(said:string): Promise<any> {
        let path = `/notifications/`+ said
        let method = 'DELETE'
        let res = await this.client.fetch(path, method, null)
        return await res.json()
    }

}
