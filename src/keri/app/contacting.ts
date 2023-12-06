import { SignifyClient } from './clienting';
import { Operation } from './coring';

/**
 * Contacts
 */
export class Contacts {
    client: SignifyClient;
    /**
     * Contacts
     * @param {SignifyClient} client
     */
    constructor(client: SignifyClient) {
        this.client = client;
    }

    /**
     * List contacts
     * @async
     * @param {string} [group] Optional group name to filter contacts
     * @param {string} [filterField] Optional field name to filter contacts
     * @param {string} [filterValue] Optional field value to filter contacts
     * @returns {Promise<any>} A promise to the list of contacts
     */
    async list(
        group?: string,
        filterField?: string,
        filterValue?: string
    ): Promise<any> {
        const params = new URLSearchParams();
        if (group !== undefined) {
            params.append('group', group);
        }
        if (filterField !== undefined && filterValue !== undefined) {
            params.append('filter_field', filterField);
            params.append('filter_value', filterValue);
        }

        const path = `/contacts` + '?' + params.toString();
        const method = 'GET';
        const res = await this.client.fetch(path, method, null);
        return await res.json();
    }

    /**
     * Get a contact
     * @async
     * @param {string} pre Prefix of the contact
     * @returns {Promise<any>} A promise to the contact
     */
    async get(pre: string): Promise<any> {
        const path = `/contacts/` + pre;
        const method = 'GET';
        const res = await this.client.fetch(path, method, null);
        return await res.json();
    }

    /**
     * Add a contact
     * @async
     * @param {string} pre Prefix of the contact
     * @param {any} info Information about the contact
     * @returns {Promise<any>} A promise to the result of the addition
     */
    async add(pre: string, info: any): Promise<any> {
        const path = `/contacts/` + pre;
        const method = 'POST';

        const res = await this.client.fetch(path, method, info);
        return await res.json();
    }

    /**
     * Delete a contact
     * @async
     * @param {string} pre Prefix of the contact
     * @returns {Promise<any>} A promise to the result of the deletion
     */
    async delete(pre: string): Promise<any> {
        const path = `/contacts/` + pre;
        const method = 'DELETE';

        const res = await this.client.fetch(path, method, null);
        return await res.json();
    }

    /**
     * Update a contact
     * @async
     * @param {string} pre Prefix of the contact
     * @param {any} info Updated information about the contact
     * @returns {Promise<any>} A promise to the result of the update
     */
    async update(pre: string, info: any): Promise<any> {
        const path = `/contacts/` + pre;
        const method = 'PUT';

        const res = await this.client.fetch(path, method, info);
        return await res.json();
    }
}

/**
 * Challenges
 */
export class Challenges {
    client: SignifyClient;
    /**
     * Challenges
     * @param {SignifyClient} client
     */
    constructor(client: SignifyClient) {
        this.client = client;
    }

    /**
     * Generate a random challenge word list based on BIP39
     * @async
     * @param {number} strength Integer representing the strength of the challenge. Typically 128 or 256
     * @returns {Promise<any>} A promise to the list of random words
     */
    async generate(strength: number = 128): Promise<any> {
        const path = `/challenges?strength=${strength.toString()}`;
        const method = 'GET';
        const res = await this.client.fetch(path, method, null);
        return await res.json();
    }

    /**
     * Respond to a challenge by signing a message with the list of words
     * @async
     * @param {string} name Name or alias of the identifier
     * @param {string} recipient Prefix of the recipient of the response
     * @param {Array<string>} words List of words to embed in the signed response
     * @returns {Promise<Response>} A promise to the result of the response
     */
    async respond(
        name: string,
        recipient: string,
        words: string[]
    ): Promise<Response> {
        const hab = await this.client.identifiers().get(name);
        const exchanges = this.client.exchanges();
        const resp = await exchanges.send(
            name,
            'challenge',
            hab,
            '/challenge/response',
            { words: words },
            {},
            [recipient]
        );
        return resp;
    }

    /**
     * Ask Agent to verify a given sender signed the provided words
     * @param {string} name Name or alias of the identifier
     * @param {string} source Prefix of the identifier that was challenged
     * @param {Array<string>} words List of challenge words to check for
     * @returns A promise to the long running operation
     */
    async verify(
        name: string,
        source: string,
        words: string[]
    ): Promise<Operation<unknown>> {
        const path = `/challenges/${name}/verify/${source}`;
        const method = 'POST';
        const data = {
            words: words,
        };
        const res = await this.client.fetch(path, method, data);

        return await res.json();
    }

    /**
     * Mark challenge response as signed and accepted
     * @param {string} name Name or alias of the identifier
     * @param {string} source Prefix of the identifier that was challenged
     * @param {string} said qb64 AID of exn message representing the signed response
     * @returns {Promise<Response>} A promise to the result
     */
    async responded(
        name: string,
        source: string,
        said: string
    ): Promise<Response> {
        const path = `/challenges/${name}/verify/${source}`;
        const method = 'PUT';
        const data = {
            said: said,
        };
        const res = await this.client.fetch(path, method, data);
        return res;
    }
}
