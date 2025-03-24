import {
    CreateIdentiferArgs,
    EventResult,
    SignifyClient,
    Tier,
    randomPasscode,
    ready,
} from 'signify-ts';
import { resolveEnvironment } from './resolve-env.ts';
import { waitOperation } from './test-util.ts';

/**
 * Connect or boot a SignifyClient instance
 */
export async function getOrCreateClient(
    bran: string | undefined = undefined
): Promise<SignifyClient> {
    const env = resolveEnvironment();
    await ready();
    bran ??= randomPasscode();
    bran = bran.padEnd(21, '_');
    const client = new SignifyClient(env.url, bran, Tier.low, env.bootUrl);
    try {
        await client.connect();
    } catch {
        const res = await client.boot();
        if (!res.ok) throw new Error();
        await client.connect();
    }
    console.log('client', {
        agent: client.agent?.pre,
        controller: client.controller.pre,
    });
    return client;
}

/**
 * Get or create a Keri identifier. Uses default witness config from `resolveEnvironment`
 * @example
 * <caption>Create a Keri identifier before running tests</caption>
 * let name1_id: string, name1_oobi: string;
 * beforeAll(async () => {
 *   [name1_id, name1_oobi] = await getOrCreateIdentifier(client1, "name1");
 * });
 * @see resolveEnvironment
 */
export async function getOrCreateIdentifier(
    client: SignifyClient,
    name: string,
    kargs: CreateIdentiferArgs | undefined = undefined
): Promise<[string, string]> {
    let id: string;
    try {
        const identfier = await client.identifiers().get(name);
        // console.log("identifiers.get", identfier);
        id = identfier.prefix;
    } catch {
        const env = resolveEnvironment();
        kargs ??= {
            toad: env.witnessIds.length,
            wits: env.witnessIds,
        };
        const result: EventResult = await client
            .identifiers()
            .create(name, kargs);
        let op = await result.op();
        op = await waitOperation(client, op);
        // console.log("identifiers.create", op);
        id = op.response.i;
    }
    const eid = client.agent?.pre;
    if (!eid) {
        throw new Error('No agent on client');
    }
    if (!(await hasEndRole(client, name, 'agent', eid))) {
        const result: EventResult = await client
            .identifiers()
            .addEndRole(name, 'agent', eid);
        const op = await result.op();
        await waitOperation(client, op);
        // console.log("identifiers.addEndRole", op);
    }
    const oobi = await client.oobis().get(name, 'agent');
    const result: [string, string] = [id, oobi.oobis[0]];
    console.log(name, result);
    return result;
}

/**
 * Get list of end role authorizations for a Keri idenfitier
 */
export async function getEndRoles(
    client: SignifyClient,
    alias: string,
    role?: string
): Promise<any> {
    const path =
        role !== undefined
            ? `/identifiers/${alias}/endroles/${role}`
            : `/identifiers/${alias}/endroles`;
    const response: Response = await client.fetch(path, 'GET', null);
    if (!response.ok) throw new Error(await response.text());
    const result = await response.json();
    // console.log("getEndRoles", result);
    return result;
}

/**
 * Test if end role is authorized for a Keri identifier
 */
export async function hasEndRole(
    client: SignifyClient,
    alias: string,
    role: string,
    eid: string
): Promise<boolean> {
    const list = await getEndRoles(client, alias, role);
    for (const i of list) {
        if (i.role === role && i.eid === eid) {
            return true;
        }
    }
    return false;
}

/**
 * Get or resolve a Keri contact
 * @example
 * <caption>Create a Keri contact before running tests</caption>
 * let contact1_id: string;
 * beforeAll(async () => {
 *   contact1_id = await getOrCreateContact(client2, "contact1", name1_oobi);
 * });
 */
export async function getOrCreateContact(
    client: SignifyClient,
    name: string,
    oobi: string
): Promise<string> {
    const list = await client.contacts().list(undefined, 'alias', `^${name}$`);
    // console.log("contacts.list", list);
    if (list.length > 0) {
        const contact = list[0];
        if (contact.oobi === oobi) {
            // console.log("contacts.id", contact.id);
            return contact.id;
        }
    }
    let op = await client.oobis().resolve(oobi, name);
    op = await waitOperation(client, op);
    // console.log("oobis.resolve", op);
    return op.response.i;
}
