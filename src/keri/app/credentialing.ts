import { SignifyClient } from './clienting';
import { Salter } from '../core/salter';
import { interact, messagize } from '../core/eventing';
import { vdr } from '../core/vdring';
import {
    b,
    d,
    Dict,
    Ident,
    Ilks,
    Serials,
    versify,
    Versionage,
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

export interface IssueCredentialArgs {
    /**
     * Name of the issuer identifier
     */
    issuerName: string;

    /**
     * QB64 AID of credential registry
     */
    registryId: string;

    /**
     * SAID Of the schema
     */
    schemaId: string;

    /**
     * Prefix of recipient identifier
     */
    recipient?: string;

    /**
     * Credential data
     */
    data?: Record<string, unknown>;

    /**
     * Credential rules
     */
    rules?: Record<string, unknown>;

    /**
     * Credential sources
     */
    source?: Record<string, unknown>;

    /**
     * Datetime to set for the credential
     */
    datetime?: string;

    /**
     * Flag to issue a credential with privacy preserving features
     */
    privacy?: boolean;
}

export interface IssueCredentialResult {
    acdc: Serder;
    anc: Serder;
    iss: Serder;
    op: Operation;
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
    agree?: string;
    datetime?: string;
    acdc: Serder;
    acdcAttachment?: string;
    iss: Serder;
    issAttachment?: string;
    anc: Serder;
    ancAttachment?: string;
}

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
     * @param {string} name - Name or alias of the identifier
     * @param {string} said - SAID of the credential
     * @param {boolean} [includeCESR=false] - Optional flag export the credential in CESR format
     * @returns {Promise<any>} A promise to the credential
     */
    async get(
        name: string,
        said: string,
        includeCESR: boolean = false
    ): Promise<any> {
        const path = `/identifiers/${name}/credentials/${said}`;
        const method = 'GET';
        const headers = includeCESR
            ? new Headers({ Accept: 'application/json+cesr' })
            : new Headers({ Accept: 'application/json' });
        const res = await this.client.fetch(path, method, null, headers);

        return includeCESR ? await res.text() : await res.json();
    }

    /**
     * Issue a credential
     */
    async issue(args: IssueCredentialArgs): Promise<IssueCredentialResult> {
        const hab = await this.client.identifiers().get(args.issuerName);
        const estOnly = hab.state.c !== undefined && hab.state.c.includes('EO');
        if (estOnly) {
            // TODO implement rotation event
            throw new Error('Establishment only not implemented');
        }
        if (!this.client.manager) {
            throw new Error('No manager on client');
        }

        const keeper = this.client.manager.get(hab);

        const dt =
            args.datetime ?? new Date().toISOString().replace('Z', '000+00:00');

        const [, subject] = Saider.saidify({
            d: '',
            u: args.privacy ? new Salter({}) : undefined,
            i: args.recipient,
            dt: dt,
            ...args.data,
        });

        const [, acdc] = Saider.saidify({
            v: versify(Ident.ACDC, undefined, Serials.JSON, 0),
            d: '',
            u: args.privacy ? new Salter({}) : undefined,
            i: hab.prefix,
            ri: args.registryId,
            s: args.schemaId,
            a: subject,
            e: args.source,
            r: args.rules,
        });

        const [, iss] = Saider.saidify({
            v: versify(Ident.KERI, undefined, Serials.JSON, 0),
            t: Ilks.iss,
            d: '',
            i: acdc.d,
            s: '0',
            ri: args.registryId,
            dt: dt,
        });

        const sn = Number(hab.state.s);
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
     * @returns {Promise<any>} A promise to the long-running operation
     */
    async revoke(name: string, said: string): Promise<any> {
        const hab = await this.client.identifiers().get(name);
        const pre: string = hab.prefix;

        const vs = versify(Ident.KERI, undefined, Serials.JSON, 0);
        const dt = new Date().toISOString().replace('Z', '000+00:00');

        const cred = await this.get(name, said);

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

        const sn = Number(state.s);
        const dig = state.d;

        const data: any = [
            {
                i: rev.i,
                s: rev.s,
                d: rev.d,
            },
        ];
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
            const keeper = this.client!.manager!.get(hab);
            sigs = await keeper.sign(b(serder.raw));
            ixn = serder.ked;
        }

        const body = {
            rev: rev,
            ixn: ixn,
            sigs: sigs,
        };

        const path = `/identifiers/${name}/credentials/${said}`;
        const method = 'DELETE';
        const headers = new Headers({
            Accept: 'application/json+cesr',
        });
        const res = await this.client.fetch(path, method, body, headers);
        return await res.json();
    }

    /**
     * Present a credential
     * @async
     * @param {string} name Name or alias of the identifier
     * @param {string} said SAID of the credential
     * @param {string} recipient Identifier prefix of the receiver of the presentation
     * @param {boolean} [include=true] Flag to indicate whether to stream credential alongside presentation exchange message
     * @returns {Promise<string>} A promise to the long-running operation
     */
    async present(
        name: string,
        said: string,
        recipient: string,
        include: boolean = true
    ): Promise<string> {
        const hab = await this.client.identifiers().get(name);
        const pre: string = hab.prefix;

        const cred = await this.get(name, said);
        const data = {
            i: cred.sad.i,
            s: cred.sad.s,
            n: said,
        };

        const vs = versify(Ident.KERI, undefined, Serials.JSON, 0);

        const _sad = {
            v: vs,
            t: Ilks.exn,
            d: '',
            dt: new Date().toISOString().replace('Z', '000+00:00'),
            r: '/presentation',
            q: {},
            a: data,
        };
        const [, sad] = Saider.saidify(_sad);
        const exn = new Serder(sad);

        const keeper = this.client!.manager!.get(hab);

        const sig = keeper.sign(b(exn.raw), true);

        const siger = new Siger({ qb64: sig[0] });
        const seal = ['SealLast', { i: pre }];
        let ims = messagize(exn, [siger], seal, undefined, undefined, true);
        ims = ims.slice(JSON.stringify(exn.ked).length);

        const body = {
            exn: exn.ked,
            sig: new TextDecoder().decode(ims),
            recipient: recipient,
            include: include,
        };

        const path = `/identifiers/${name}/credentials/${said}/presentations`;
        const method = 'POST';
        const headers = new Headers({
            Accept: 'application/json+cesr',
        });
        const res = await this.client.fetch(path, method, body, headers);
        return await res.text();
    }

    /**
     * Request a presentation of a credential
     * @async
     * @param {string} name Name or alias of the identifier
     * @param {string} recipient Identifier prefix of the receiver of the presentation
     * @param {string} schema SAID of the schema
     * @param {string} [issuer] Optional prefix of the issuer of the credential
     * @returns {Promise<string>} A promise to the long-running operation
     */
    async request(
        name: string,
        recipient: string,
        schema: string,
        issuer?: string
    ): Promise<string> {
        const hab = await this.client.identifiers().get(name);
        const pre: string = hab.prefix;

        const data: any = {
            s: schema,
        };
        if (issuer !== undefined) {
            data['i'] = issuer;
        }

        const vs = versify(Ident.KERI, undefined, Serials.JSON, 0);

        const _sad = {
            v: vs,
            t: Ilks.exn,
            d: '',
            dt: new Date().toISOString().replace('Z', '000+00:00'),
            r: '/presentation/request',
            q: {},
            a: data,
        };
        const [, sad] = Saider.saidify(_sad);
        const exn = new Serder(sad);

        const keeper = this.client!.manager!.get(hab);

        const sig = await keeper.sign(b(exn.raw), true);

        const siger = new Siger({ qb64: sig[0] });
        const seal = ['SealLast', { i: pre }];
        let ims = messagize(exn, [siger], seal, undefined, undefined, true);
        ims = ims.slice(JSON.stringify(exn.ked).length);

        const body = {
            exn: exn.ked,
            sig: new TextDecoder().decode(ims),
            recipient: recipient,
        };

        const path = `/identifiers/${name}/requests`;
        const method = 'POST';
        const headers = new Headers({
            Accept: 'application/json+cesr',
        });
        const res = await this.client.fetch(path, method, body, headers);
        return await res.text();
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
            const sn = Number(state.s);
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
                version: Versionage,
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
        hab: Dict<any>,
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
     * Create an IPEX grant EXN message
     */
    async grant(args: IpexGrantArgs): Promise<[Serder, string[], string]> {
        const hab = await this.client.identifiers().get(args.senderName);
        const data = {
            m: args.message ?? '',
            i: args.recipient,
        };

        let atc = args.ancAttachment;
        if (atc === undefined) {
            const keeper = this.client.manager?.get(hab);
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
                undefined,
                args.datetime,
                args.agree
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
     * @async
     * @param {string} name Name or alias of the identifier
     * @param {string} message accompany human readable description of the credential being admitted
     * @param {string} grant qb64 SAID of grant message this admit is responding to
     * @param {string} datetime Optional datetime to set for the credential
     * @returns {Promise<[Serder, string[], string]>} A promise to the long-running operation
     */
    async admit(
        name: string,
        message: string,
        grant: string,
        datetime?: string
    ): Promise<[Serder, string[], string]> {
        const hab = await this.client.identifiers().get(name);
        const data: any = {
            m: message,
        };

        return this.client
            .exchanges()
            .createExchangeMessage(
                hab,
                '/ipex/admit',
                data,
                {},
                undefined,
                datetime,
                grant
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
