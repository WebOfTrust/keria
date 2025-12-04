import { SignifyClient } from './clienting.ts';
import { components } from '../../types/keria-api-schema.ts';

export type Rpy = components['schemas']['Rpy'];
/**
 * Escrows
 */
export class Escrows {
    client: SignifyClient;

    /**
     * Escrows
     * @param {SignifyClient} client
     */
    constructor(client: SignifyClient) {
        this.client = client;
    }

    /**
     * List replay messages
     * @async
     * @param {string} [route] Optional route in the replay message
     * @returns {Promise<Rpy[]>} A promise to the list of replay messages
     */
    async listReply(route?: string): Promise<Rpy[]> {
        const params = new URLSearchParams();
        if (route !== undefined) {
            params.append('route', route);
        }

        const path = `/escrows/rpy` + '?' + params.toString();
        const method = 'GET';
        const res = await this.client.fetch(path, method, null);
        return await res.json();
    }
}
