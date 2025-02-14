import { SignifyClient } from './clienting';
import { interact, messagize } from '../core/eventing';
import { vdr } from '../core/vdring';
import {
    b,
    d,
    Dict,
    Protocols,
    Ilks,
    Serials,
    versify,
    Vrsn_1_0,
} from '../core/core';
import { Saider } from '../core/saider';
import { Serder } from '../core/serder';
import { Siger } from '../core/siger';
import { TraitDex } from './habery';
import {
    serializeACDCAttachment,
    serializeIssExnAttachment,
} from '../core/utils';
import { Operation } from './coring';
import { HabState } from '../core/keyState';

/** Types of credentials */
export class CredentialTypes {
    static issued = 'issued';
    static received = 'received';
}

/** Credential filter parameters */
export interface CredentialFilter {
    filter?: object;
    sort?: object[];
    skip?: number;
    limit?: number;
}

export interface CredentialSubject {
    /**
     * Issuee, or holder of the credential.
     */
    i?: string;
    /**
     * Timestamp of issuance.
     */
    dt?: string;
    /**
     * Privacy salt
     */
    u?: string;
    [key: string]: unknown;
}

export interface CredentialData {
    v?: string;
    d?: string;
    /**
     * Privacy salt
     */
    u?: string;
    /**
     * Issuer of the credential.
     */
    i?: string;
    /**
     * Registry id.
     */
    ri?: string;
    /**
     * Schema id
     */
    s?: string;
    /**
     * Credential subject data
     */
    a: CredentialSubject;
    /**
     * Credential source section
     */
    e?: { [key: string]: unknown };
    /**
     * Credential rules section
     */
    r?: { [key: string]: unknown };
}

export interface IssueCredentialResult {
    acdc: Serder;
    anc: Serder;
    iss: Serder;
    op: Operation;
}

export interface RevokeCredentialResult {
    anc: Serder;
    rev: Serder;
    op: Operation;
}

export interface IpexApplyArgs {
    /**
     * Alias for the IPEX sender AID
     */
    senderName: string;

    /**
     * Prefix of the IPEX recipient AID
     */
    recipient: string;

    /**
     * Message to send
     */
    message?: string;

    /**
     * SAID of schema to apply for
     */
    schemaSaid: string;

    /**
     * Optional attributes for selective disclosure
     */
    attributes?: Record<string, unknown>;
    datetime?: string;
}

export interface IpexOfferArgs {
    /**
     * Alias for the IPEX sender AID
     */
    senderName: string;

    /**
     * Prefix of the IPEX recipient AID
     */
    recipient: string;

    /**
     * Message to send
     */
    message?: string;

    /**
     * ACDC to offer
     */
    acdc: Serder;

    /**
     * Optional qb64 SAID of apply message this offer is responding to
     */
    applySaid?: string;
    datetime?: string;
}

export interface IpexAgreeArgs {
    /**
     * Alias for the IPEX sender AID
     */
    senderName: string;

    /**
     * Prefix of the IPEX recipient AID
     */
    recipient: string;

    /**
     * Message to send
     */
    message?: string;

    /**
     * qb64 SAID of offer message this agree is responding to
     */
    offerSaid: string;
    datetime?: string;
}

export interface IpexGrantArgs {
    /**
     * Alias for the IPEX sender AID
     */
    senderName: string;

    /**
     * Prefix of the IPEX recipient AID
     */
    recipient: string;

    /**
     * Message to send
     */
    message?: string;

    /**
     * qb64 SAID of agree message this grant is responding to
     */
    agreeSaid?: string;
    datetime?: string;
    acdc: Serder;
    acdcAttachment?: string;
    iss: Serder;
    issAttachment?: string;
    anc: Serder;
    ancAttachment?: string;
}

export interface IpexAdmitArgs {
    /**
     * Alias for the IPEX sender AID
     */
    senderName: string;

    /**
     * Prefix of the IPEX recipient AID
     */
    recipient: string;

    /**
     * Message to send
     */
    message?: string;

    /**
     * qb64 SAID of agree message this admit is responding to
     */
    grantSaid: string;
    datetime?: string;
}

export type CredentialState = {
    vn: [number, number];
    i: string;
    s: string;
    d: string;
    ri: string;
    a: { s: number; d: string };
    dt: string;
    et: string;
} & (
    | {
          et: 'iss' | 'rev';
          ra: Record<string, never>;
      }
    | {
          et: 'bis' | 'brv';
          ra: { i: string; s: string; d: string };
      }
);

/**
 * Credentials
 */
export class Credentials {
    public client: SignifyClient;
    /**
     * Credentials
     * @param {SignifyClient} client
     */
    constructor(client: SignifyClient) {
        this.client = client;
    }

    /**
     * List credentials
     * @async
     * @param {CredentialFilter} [kargs] Optional parameters to filter the credentials
     * @returns {Promise<any>} A promise to the list of credentials
     */
    async list(kargs: CredentialFilter = {}): Promise<any> {
        const path = `/credentials/query`;
        const filtr = kargs.filter === undefined ? {} : kargs.filter;
        const sort = kargs.sort === undefined ? [] : kargs.sort;
        const limit = kargs.limit === undefined ? 25 : kargs.limit;
        const skip = kargs.skip === undefined ? 0 : kargs.skip;

        const data = {
            filter: filtr,
            sort: sort,
            skip: skip,
            limit: limit,
        };
        const method = 'POST';

        const res = await this.client.fetch(path, method, data, undefined);
        return await res.json();
    }

    /**
     * Get a credential
     * @async
     * @param {string} said - SAID of the credential
     * @param {boolean} [includeCESR=false] - Optional flag export the credential in CESR format
     * @returns {Promise<any>} A promise to the credential
     */
    async get(said: string, includeCESR: boolean = false): Promise<any> {
        const path = `/credentials/${said}`;
        const method = 'GET';
        const headers = includeCESR
            ? new Headers({ Accept: 'application/json+cesr' })
            : new Headers({ Accept: 'application/json' });
        const res = await this.client.fetch(path, method, null, headers);

        return includeCESR ? await res.text() : await res.json();
    }

    /**
     * Delete a credential from the DB
     * @async
     * @param {string} said - SAID of the credential
     * @returns {Promise<void>}
     */
    async delete(said: string): Promise<void> {
        const path = `/credentials/${said}`;
        const method = 'DELETE';
        await this.client.fetch(path, method, undefined);
    }

    /**
     * Get the state of a credential
     * @async
     * @param {string} ri - management registry identifier
     * @param {string} said - SAID of the credential
     * @returns {Promise<CredentialState>} A promise to the credential registry state
     */
    async state(ri: string, said: string): Promise<CredentialState> {
        const path = `/registries/${ri}/${said}`;
        const method = 'GET';
        const res = await this.client.fetch(path, method, null);
        return res.json();
    }

    /**
     * Creates a credential in the specified registry to be GRANTed with IPEX to the intended recipient
     */
    async issue(
        name: string,
        args: CredentialData
    ): Promise<IssueCredentialResult> {
        const hab = await this.client.identifiers().get(name);
        const estOnly = hab.state.c !== undefined && hab.state.c.includes('EO');
        if (estOnly) {
            // TODO implement rotation event
            throw new Error('Establishment only not implemented');
        }
        if (!this.client.manager) {
            throw new Error('No manager on client');
        }

        const keeper = this.client.manager.get(hab);

        const [, subject] = Saider.saidify({
            d: '',
            ...args.a,
            dt: args.a.dt ?? new Date().toISOString().replace('Z', '000+00:00'),
        });

        const [, acdc] = Saider.saidify({
            v: versify(Protocols.ACDC, undefined, Serials.JSON, 0),
            d: '',
            u: args.u,
            i: args.i ?? hab.prefix,
            ri: args.ri,
            s: args.s,
            a: subject,
            e: args.e,
            r: args.r,
        });

        const [, iss] = Saider.saidify({
            v: versify(Protocols.KERI, undefined, Serials.JSON, 0),
            t: Ilks.iss,
            d: '',
            i: acdc.d,
            s: '0',
            ri: args.ri,
            dt: subject.dt,
        });

        const sn = parseInt(hab.state.s, 16);
        const anc = interact({
            pre: hab.prefix,
            sn: sn + 1,
            data: [
                {
                    i: iss.i,
                    s: iss.s,
                    d: iss.d,
                },
            ],
            dig: hab.state.d,
            version: undefined,
            kind: undefined,
        });

        const sigs = await keeper.sign(b(anc.raw));

        const path = `/identifiers/${hab.name}/credentials`;
        const method = 'POST';
        const body = {
            acdc: acdc,
            iss: iss,
            ixn: anc.ked,
            sigs,
            [keeper.algo]: keeper.params(),
        };

        const headers = new Headers({
            Accept: 'application/json+cesr',
        });

        const res = await this.client.fetch(path, method, body, headers);
        const op = await res.json();

        return {
            acdc: new Serder(acdc),
            iss: new Serder(iss),
            anc,
            op,
        };
    }

    /**
     * Revoke credential
     * @async
     * @param {string} name Name or alias of the identifier
     * @param {string} said SAID of the credential
     * @param {string} datetime date time of revocation
     * @returns {Promise<any>} A promise to the long-running operation
     */
    async revoke(
        name: string,
        said: string,
        datetime?: string
    ): Promise<RevokeCredentialResult> {
        const hab = await this.client.identifiers().get(name);
        const pre: string = hab.prefix;

        const vs = versify(Protocols.KERI, undefined, Serials.JSON, 0);
        const dt =
            datetime ?? new Date().toISOString().replace('Z', '000+00:00');

        const cred = await this.get(said);

        // Create rev
        const _rev = {
            v: vs,
            t: Ilks.rev,
            d: '',
            i: said,
            s: '1',
            ri: cred.sad.ri,
            p: cred.status.d,
            dt: dt,
        };

        const [, rev] = Saider.saidify(_rev);

        // create ixn
        let ixn = {};
        let sigs = [];

        const state = hab.state;
        if (state.c !== undefined && state.c.includes('EO')) {
            var estOnly = true;
        } else {
            var estOnly = false;
        }

        const sn = parseInt(state.s, 16);
        const dig = state.d;

        const data: any = [
            {
                i: rev.i,
                s: rev.s,
                d: rev.d,
            },
        ];

        const keeper = this.client!.manager!.get(hab);

        if (estOnly) {
            // TODO implement rotation event
            throw new Error('Establishment only not implemented');
        } else {
            const serder = interact({
                pre: pre,
                sn: sn + 1,
                data: data,
                dig: dig,
                version: undefined,
                kind: undefined,
            });
            sigs = await keeper.sign(b(serder.raw));
            ixn = serder.ked;
        }

        const body = {
            rev: rev,
            ixn: ixn,
            sigs: sigs,
            [keeper.algo]: keeper.params(),
        };

        const path = `/identifiers/${name}/credentials/${said}`;
        const method = 'DELETE';
        const headers = new Headers({
            Accept: 'application/json+cesr',
        });
        const res = await this.client.fetch(path, method, body, headers);
        const op = await res.json();

        return {
            rev: new Serder(rev),
            anc: new Serder(ixn),
            op,
        };
    }
}

export interface CreateRegistryArgs {
    name: string;
    registryName: string;
    toad?: string | number | undefined;
    noBackers?: boolean;
    baks?: string[];
    nonce?: string;
}

export class RegistryResult {
    private readonly _regser: any;
    private readonly _serder: Serder;
    private readonly _sigs: string[];
    private readonly promise: Promise<Response>;

    constructor(
        regser: Serder,
        serder: Serder,
        sigs: any[],
        promise: Promise<Response>
    ) {
        this._regser = regser;
        this._serder = serder;
        this._sigs = sigs;
        this.promise = promise;
    }

    get regser() {
        return this._regser;
    }

    get serder() {
        return this._serder;
    }

    get sigs() {
        return this._sigs;
    }

    async op(): Promise<any> {
        const res = await this.promise;
        return await res.json();
    }
}

/**
 * Registries
 */
export class Registries {
    public client: SignifyClient;
    /**
     * Registries
     * @param {SignifyClient} client
     */
    constructor(client: SignifyClient) {
        this.client = client;
    }

    /**
     * List registries
     * @async
     * @param {string} name Name or alias of the identifier
     * @returns {Promise<any>} A promise to the list of registries
     */
    async list(name: string): Promise<any> {
        const path = `/identifiers/${name}/registries`;
        const method = 'GET';
        const res = await this.client.fetch(path, method, null);
        return await res.json();
    }

    /**
     * Create a registry
     * @async
     * @param {CreateRegistryArgs}
     * @returns {Promise<[any, Serder, any[], object]> } A promise to the long-running operation
     */
    async create({
        name,
        registryName,
        noBackers = true,
        toad = 0,
        baks = [],
        nonce,
    }: CreateRegistryArgs): Promise<RegistryResult> {
        const hab = await this.client.identifiers().get(name);
        const pre: string = hab.prefix;

        const cnfg: string[] = [];
        if (noBackers) {
            cnfg.push(TraitDex.NoBackers);
        }

        const state = hab.state;
        const estOnly = state.c !== undefined && state.c.includes('EO');
        if (estOnly) {
            cnfg.push(TraitDex.EstOnly);
        }

        const regser = vdr.incept({ pre, baks, toad, nonce, cnfg });

        if (estOnly) {
            throw new Error('establishment only not implemented');
        } else {
            const state = hab.state;
            const sn = parseInt(state.s, 16);
            const dig = state.d;

            const data: any = [
                {
                    i: regser.pre,
                    s: '0',
                    d: regser.pre,
                },
            ];

            const serder = interact({
                pre: pre,
                sn: sn + 1,
                data: data,
                dig: dig,
                version: Vrsn_1_0,
                kind: Serials.JSON,
            });
            const keeper = this.client.manager!.get(hab);
            const sigs = await keeper.sign(b(serder.raw));
            const res = this.createFromEvents(
                hab,
                name,
                registryName,
                regser.ked,
                serder.ked,
                sigs
            );
            return new RegistryResult(regser, serder, sigs, res);
        }
    }

    createFromEvents(
        hab: HabState,
        name: string,
        registryName: string,
        vcp: Dict<any>,
        ixn: Dict<any>,
        sigs: any[]
    ) {
        const path = `/identifiers/${name}/registries`;
        const method = 'POST';

        const data: any = {
            name: registryName,
            vcp: vcp,
            ixn: ixn,
            sigs: sigs,
        };
        const keeper = this.client!.manager!.get(hab);
        data[keeper.algo] = keeper.params();

        return this.client.fetch(path, method, data);
    }

    /**
     * Rename a registry
     * @async
     * @param {string} name Name or alias of the identifier
     * @param {string} registryName Current registry name
     * @param {string} newName New registry name
     * @returns {Promise<any>} A promise to the registry record
     */
    async rename(
        name: string,
        registryName: string,
        newName: string
    ): Promise<any> {
        const path = `/identifiers/${name}/registries/${registryName}`;
        const method = 'PUT';
        const data = {
            name: newName,
        };
        const res = await this.client.fetch(path, method, data);
        return await res.json();
    }
}
/**
 * Schemas
 */
export class Schemas {
    client: SignifyClient;
    /**
     * Schemas
     * @param {SignifyClient} client
     */
    constructor(client: SignifyClient) {
        this.client = client;
    }

    /**
     * Get a schema
     * @async
     * @param {string} said SAID of the schema
     * @returns {Promise<any>} A promise to the schema
     */
    async get(said: string): Promise<any> {
        const path = `/schema/${said}`;
        const method = 'GET';
        const res = await this.client.fetch(path, method, null);
        return await res.json();
    }

    /**
     * List schemas
     * @async
     * @returns {Promise<any>} A promise to the list of schemas
     */
    async list(): Promise<any> {
        const path = `/schema`;
        const method = 'GET';
        const res = await this.client.fetch(path, method, null);
        return await res.json();
    }
}

/**
 * Ipex
 */

export class Ipex {
    client: SignifyClient;
    /**
     * Schemas
     * @param {SignifyClient} client
     */
    constructor(client: SignifyClient) {
        this.client = client;
    }

    /**
     * Create an IPEX apply EXN message
     */
    async apply(args: IpexApplyArgs): Promise<[Serder, string[], string]> {
        const hab = await this.client.identifiers().get(args.senderName);
        const data = {
            m: args.message ?? '',
            s: args.schemaSaid,
            a: args.attributes ?? {},
        };

        return this.client
            .exchanges()
            .createExchangeMessage(
                hab,
                '/ipex/apply',
                data,
                {},
                args.recipient,
                args.datetime,
                undefined
            );
    }

    async submitApply(
        name: string,
        exn: Serder,
        sigs: string[],
        recp: string[]
    ): Promise<any> {
        const body = {
            exn: exn.ked,
            sigs,
            rec: recp,
        };

        const response = await this.client.fetch(
            `/identifiers/${name}/ipex/apply`,
            'POST',
            body
        );

        return response.json();
    }

    /**
     * Create an IPEX offer EXN message
     */
    async offer(args: IpexOfferArgs): Promise<[Serder, string[], string]> {
        const hab = await this.client.identifiers().get(args.senderName);
        const data = {
            m: args.message ?? '',
        };

        return this.client
            .exchanges()
            .createExchangeMessage(
                hab,
                '/ipex/offer',
                data,
                { acdc: [args.acdc, undefined] },
                args.recipient,
                args.datetime,
                args.applySaid
            );
    }

    async submitOffer(
        name: string,
        exn: Serder,
        sigs: string[],
        atc: string,
        recp: string[]
    ): Promise<any> {
        const body = {
            exn: exn.ked,
            sigs,
            atc,
            rec: recp,
        };

        const response = await this.client.fetch(
            `/identifiers/${name}/ipex/offer`,
            'POST',
            body
        );

        return response.json();
    }

    /**
     * Create an IPEX agree EXN message
     */
    async agree(args: IpexAgreeArgs): Promise<[Serder, string[], string]> {
        const hab = await this.client.identifiers().get(args.senderName);
        const data = {
            m: args.message ?? '',
        };

        return this.client
            .exchanges()
            .createExchangeMessage(
                hab,
                '/ipex/agree',
                data,
                {},
                args.recipient,
                args.datetime,
                args.offerSaid
            );
    }

    async submitAgree(
        name: string,
        exn: Serder,
        sigs: string[],
        recp: string[]
    ): Promise<any> {
        const body = {
            exn: exn.ked,
            sigs,
            rec: recp,
        };

        const response = await this.client.fetch(
            `/identifiers/${name}/ipex/agree`,
            'POST',
            body
        );

        return response.json();
    }

    /**
     * Create an IPEX grant EXN message
     */
    async grant(args: IpexGrantArgs): Promise<[Serder, string[], string]> {
        const hab = await this.client.identifiers().get(args.senderName);
        const data = {
            m: args.message ?? '',
        };

        let atc = args.ancAttachment;
        if (atc === undefined) {
            const keeper = this.client.manager!.get(hab);
            const sigs = await keeper.sign(b(args.anc.raw));
            const sigers = sigs.map((sig: string) => new Siger({ qb64: sig }));
            const ims = d(messagize(args.anc, sigers));
            atc = ims.substring(args.anc.size);
        }

        const acdcAtc =
            args.acdcAttachment === undefined
                ? d(serializeACDCAttachment(args.iss))
                : args.acdcAttachment;
        const issAtc =
            args.issAttachment === undefined
                ? d(serializeIssExnAttachment(args.anc))
                : args.issAttachment;

        const embeds: Record<string, [Serder, string]> = {
            acdc: [args.acdc, acdcAtc],
            iss: [args.iss, issAtc],
            anc: [args.anc, atc],
        };

        return this.client
            .exchanges()
            .createExchangeMessage(
                hab,
                '/ipex/grant',
                data,
                embeds,
                args.recipient,
                args.datetime,
                args.agreeSaid
            );
    }

    async submitGrant(
        name: string,
        exn: Serder,
        sigs: string[],
        atc: string,
        recp: string[]
    ): Promise<any> {
        const body = {
            exn: exn.ked,
            sigs: sigs,
            atc: atc,
            rec: recp,
        };

        const response = await this.client.fetch(
            `/identifiers/${name}/ipex/grant`,
            'POST',
            body
        );

        return response.json();
    }

    /**
     * Create an IPEX admit EXN message
     */
    async admit(args: IpexAdmitArgs): Promise<[Serder, string[], string]> {
        const hab = await this.client.identifiers().get(args.senderName);
        const data: any = {
            m: args.message,
        };

        return this.client
            .exchanges()
            .createExchangeMessage(
                hab,
                '/ipex/admit',
                data,
                {},
                args.recipient,
                args.datetime,
                args.grantSaid
            );
    }

    async submitAdmit(
        name: string,
        exn: Serder,
        sigs: string[],
        atc: string,
        recp: string[]
    ): Promise<any> {
        const body = {
            exn: exn.ked,
            sigs: sigs,
            atc: atc,
            rec: recp,
        };

        const response = await this.client.fetch(
            `/identifiers/${name}/ipex/admit`,
            'POST',
            body
        );

        return response.json();
    }
}
