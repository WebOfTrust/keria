import { SignifyClient } from './clienting';
import { Dict } from '../core/core';

/**
 * Groups
 */
export class Groups {
    client: SignifyClient;

    /**
     * Groups
     * @param {SignifyClient} client
     */
    constructor(client: SignifyClient) {
        this.client = client;
    }

    /**
     * Get group request messages
     * @async
     * @param {string} [said] SAID of exn message to load
     * @returns {Promise<any>} A promise to the list of replay messages
     */
    async getRequest(said: string): Promise<any> {
        const path = `/multisig/request/` + said;
        const method = 'GET';
        const res = await this.client.fetch(path, method, null);
        return await res.json();
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
    async sendRequest(
        name: string,
        exn: Dict<any>,
        sigs: string[],
        atc: string
    ): Promise<any> {
        const path = `/identifiers/${name}/multisig/request`;
        const method = 'POST';
        const data = {
            exn: exn,
            sigs: sigs,
            atc: atc,
        };
        const res = await this.client.fetch(path, method, data);
        return await res.json();
    }

    /**
     * Join multisig group using rotation event.
     * This can be used by participants being asked to contribute keys to a rotation event to join an existing group.
     * @async
     * @param {string} [name] human readable name of group AID
     * @param {any} [rot] rotation event
     * @param {any} [sigs] signatures
     * @param {string} [gid] prefix
     * @param {string[]} [smids] array of particpants
     * @param {string[]} [rmids] array of particpants
     * @returns {Promise<any>} A promise to the list of replay messages
     */
    async join(
        name: string,
        rot: any,
        sigs: any, //string[],
        gid: string,
        smids: string[],
        rmids: string[]
    ): Promise<any> {
        const path = `/identifiers/${name}/multisig/join`;
        const method = 'POST';
        const data = {
            tpc: 'multisig',
            rot: rot.sad,
            sigs: sigs,
            gid: gid,
            smids: smids,
            rmids: rmids,
        };
        const res = await this.client.fetch(path, method, data);
        return await res.json();
    }
}
