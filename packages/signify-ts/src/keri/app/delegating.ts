import { EventResult } from './aiding.ts';
import { SignifyClient } from './clienting.ts';

export class Delegations {
    public client: SignifyClient;
    /**
     * Delegations
     * @param {SignifyClient} client
     */
    constructor(client: SignifyClient) {
        this.client = client;
    }

    /**
     * Approve the delegation via interaction event
     * @async
     * @param {string} name Name or alias of the identifier
     * @param {any} [data] The anchoring interaction event
     * @returns {Promise<EventResult>} A promise to the delegated approval result
     */
    async approve(name: string, data?: any): Promise<EventResult> {
        const { serder, sigs, jsondata } = await this.client
            .identifiers()
            .createInteract(name, data);

        const res = await this.client.fetch(
            '/identifiers/' + name + '/delegation',
            'POST',
            jsondata
        );
        return new EventResult(serder, sigs, res);
    }
}
