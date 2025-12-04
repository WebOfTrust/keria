import { SignifyClient } from './clienting.ts';
import { b, d, Dict, Protocols, Ilks, Serials, versify } from '../core/core.ts';
import { Serder } from '../core/serder.ts';
import { nowUTC } from '../core/utils.ts';
import { Pather } from '../core/pather.ts';
import { Counter, CtrDex } from '../core/counter.ts';
import { Saider } from '../core/saider.ts';
import { HabState } from '../core/keyState.ts';

/**
 * Exchanges
 */
export class Exchanges {
    client: SignifyClient;

    /**
     * Exchanges
     * @param {SignifyClient} client
     */
    constructor(client: SignifyClient) {
        this.client = client;
    }

    /**
     * Create exn message
     * @async
     * @returns {Promise<any>} A promise to the list of replay messages
     * @param sender
     * @param route
     * @param payload
     * @param embeds
     * @param recipient
     * @param datetime
     * @param dig
     */
    async createExchangeMessage(
        sender: HabState,
        route: string,
        payload: Dict<any>,
        embeds: Dict<any>,
        recipient: string,
        datetime?: string,
        dig?: string
    ): Promise<[Serder, string[], string]> {
        const keeper = this.client.manager!.get(sender);
        const [exn, end] = exchange(
            route,
            payload,
            sender['prefix'],
            recipient,
            datetime,
            dig,
            undefined,
            embeds
        );

        const sigs = await keeper.sign(b(exn.raw));
        return [exn, sigs, d(end)];
    }

    /**
     * Send exn messages to list of recipients
     * @async
     * @returns {Promise<any>} A promise to the list of replay messages
     * @param name
     * @param topic
     * @param sender
     * @param route
     * @param payload
     * @param embeds
     * @param recipients
     */
    async send(
        name: string,
        topic: string,
        sender: HabState,
        route: string,
        payload: Dict<any>,
        embeds: Dict<any>,
        recipients: string[]
    ): Promise<any> {
        for (const recipient of recipients) {
            const [exn, sigs, atc] = await this.createExchangeMessage(
                sender,
                route,
                payload,
                embeds,
                recipient
            );
            return await this.sendFromEvents(
                name,
                topic,
                exn,
                sigs,
                atc,
                recipients
            );
        }
    }

    /**
     * Send exn messaget to list of recipients
     * @async
     * @returns {Promise<any>} A promise to the list of replay messages
     * @param name
     * @param topic
     * @param exn
     * @param sigs
     * @param atc
     * @param recipients
     */
    async sendFromEvents(
        name: string,
        topic: string,
        exn: Serder,
        sigs: string[],
        atc: string,
        recipients: string[]
    ): Promise<any> {
        const path = `/identifiers/${name}/exchanges`;
        const method = 'POST';
        const data: any = {
            tpc: topic,
            exn: exn.sad,
            sigs: sigs,
            atc: atc,
            rec: recipients,
        };

        const res = await this.client.fetch(path, method, data);
        return await res.json();
    }

    /**
     * Get exn message by said
     * @async
     * @returns A promise to the exn message
     * @param said The said of the exn message
     */
    async get(said: string): Promise<any> {
        const path = `/exchanges/${said}`;
        const method = 'GET';
        const res = await this.client.fetch(path, method, null);
        return await res.json();
    }
}

export function exchange(
    route: string,
    payload: Dict<any>,
    sender: string,
    recipient: string,
    date?: string,
    dig?: string,
    modifiers?: Dict<any>,
    embeds?: Dict<any>
): [Serder, Uint8Array] {
    const vs = versify(Protocols.KERI, undefined, Serials.JSON, 0);
    const ilk = Ilks.exn;
    const dt =
        date !== undefined
            ? date
            : nowUTC().toISOString().replace('Z', '000+00:00');
    const p = dig !== undefined ? dig : '';
    const q = modifiers !== undefined ? modifiers : {};
    const ems = embeds != undefined ? embeds : {};

    let e = {} as Dict<any>;
    let end = '';
    Object.entries(ems).forEach(([key, value]) => {
        const serder = value[0];
        const atc = value[1];
        e[key] = serder.sad;

        if (atc == undefined) {
            return;
        }
        let pathed = '';
        const pather = new Pather({}, undefined, ['e', key]);
        pathed += pather.qb64;
        pathed += atc;

        const counter = new Counter({
            code: CtrDex.PathedMaterialQuadlets,
            count: Math.floor(pathed.length / 4),
        });
        end += counter.qb64;
        end += pathed;
    });

    if (Object.keys(e).length > 0) {
        e['d'] = '';
        [, e] = Saider.saidify(e);
    }

    const attrs = {} as Dict<any>;

    attrs['i'] = recipient;

    const a = {
        ...attrs,
        ...payload,
    };

    const _sad = {
        v: vs,
        t: ilk,
        d: '',
        i: sender,
        rp: recipient,
        p: p,
        dt: dt,
        r: route,
        q: q,
        a: a,
        e: e,
    };
    const [, sad] = Saider.saidify(_sad);

    const exn = new Serder(sad);

    return [exn, b(end)];
}
