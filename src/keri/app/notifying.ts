import { SignifyClient } from './clienting';
import { parseRangeHeaders } from '../core/httping';

/**
 * Notifications
 */
export class Notifications {
    client: SignifyClient;

    /**
     * Notifications
     * @param {SignifyClient} client
     */
    constructor(client: SignifyClient) {
        this.client = client;
    }

    /**
     * List notifications
     * @async
     * @param {number} [start=0] Start index of list of notifications, defaults to 0
     * @param {number} [end=24] End index of list of notifications, defaults to 24
     * @returns {Promise<any>} A promise to the list of notifications
     */
    async list(start: number = 0, end: number = 24): Promise<any> {
        const extraHeaders = new Headers();
        extraHeaders.append('Range', `notes=${start}-${end}`);

        const path = `/notifications`;
        const method = 'GET';
        const res = await this.client.fetch(path, method, null, extraHeaders);

        const cr = res.headers.get('content-range');
        const range = parseRangeHeaders(cr, 'notes');
        const notes = await res.json();

        return {
            start: range.start,
            end: range.end,
            total: range.total,
            notes: notes,
        };
    }

    /**
     * Mark a notification as read
     * @async
     * @param {string} said SAID of the notification
     * @returns {Promise<string>} A promise to the result of the marking
     */
    async mark(said: string): Promise<string> {
        const path = `/notifications/` + said;
        const method = 'PUT';
        const res = await this.client.fetch(path, method, null);
        return await res.text();
    }

    /**
     * Delete a notification
     * @async
     * @param {string} said SAID of the notification
     * @returns {Promise<void>}
     */
    async delete(said: string): Promise<void> {
        const path = `/notifications/` + said;
        const method = 'DELETE';
        await this.client.fetch(path, method, undefined);
    }
}
