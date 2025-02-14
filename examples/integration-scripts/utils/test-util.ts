import signify, {
    CreateIdentiferArgs,
    EventResult,
    Operation,
    randomPasscode,
    ready,
    Salter,
    SignifyClient,
    Tier,
} from 'signify-ts';
import { RetryOptions, retry } from './retry';
import { HabState } from '../../../src/keri/core/keyState';
import assert from 'assert';
import { resolveEnvironment } from './resolve-env';

export interface Aid {
    name: string;
    prefix: string;
    oobi: string;
}

export interface Notification {
    i: string;
    dt: string;
    r: boolean;
    a: { r: string; d?: string; m?: string };
}

export function sleep(ms: number): Promise<void> {
    return new Promise((resolve) => {
        setTimeout(resolve, ms);
    });
}

export async function admitSinglesig(
    client: SignifyClient,
    aidName: string,
    recipientAid: HabState
) {
    const grantMsgSaid = await waitAndMarkNotification(
        client,
        '/exn/ipex/grant'
    );

    const [admit, sigs, aend] = await client.ipex().admit({
        senderName: aidName,
        message: '',
        grantSaid: grantMsgSaid,
        recipient: recipientAid.prefix,
    });

    await client
        .ipex()
        .submitAdmit(aidName, admit, sigs, aend, [recipientAid.prefix]);
}

/**
 * Assert that all operations were waited for.
 * <p>This is a postcondition check to make sure all long-running operations have been waited for
 * @see waitOperation
 */
export async function assertOperations(
    ...clients: SignifyClient[]
): Promise<void> {
    for (const client of clients) {
        const operations = await client.operations().list();
        expect(operations).toHaveLength(0);
    }
}

/**
 * Assert that all notifications were handled.
 * <p>This is a postcondition check to make sure all notifications have been handled
 * @see markNotification
 * @see markAndRemoveNotification
 */
export async function assertNotifications(
    ...clients: SignifyClient[]
): Promise<void> {
    for (const client of clients) {
        const res = await client.notifications().list();
        const notes = res.notes.filter((i: { r: boolean }) => i.r === false);
        expect(notes).toHaveLength(0);
    }
}

export async function createAid(
    client: SignifyClient,
    name: string
): Promise<Aid> {
    const [prefix, oobi] = await getOrCreateIdentifier(client, name);
    return { prefix, oobi, name };
}

export async function createAID(client: signify.SignifyClient, name: string) {
    await getOrCreateIdentifier(client, name);
    const aid = await client.identifiers().get(name);
    console.log(name, 'AID:', aid.prefix);
    return aid;
}

export function createTimestamp() {
    return new Date().toISOString().replace('Z', '000+00:00');
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

export async function getIssuedCredential(
    issuerClient: SignifyClient,
    issuerAID: HabState,
    recipientAID: HabState,
    schemaSAID: string
) {
    const credentialList = await issuerClient.credentials().list({
        filter: {
            '-i': issuerAID.prefix,
            '-s': schemaSAID,
            '-a-i': recipientAID.prefix,
        },
    });
    assert(credentialList.length <= 1);
    return credentialList[0];
}

export async function getOrCreateAID(
    client: SignifyClient,
    name: string,
    kargs: CreateIdentiferArgs
): Promise<HabState> {
    try {
        return await client.identifiers().get(name);
    } catch {
        const result: EventResult = await client
            .identifiers()
            .create(name, kargs);

        await waitOperation(client, await result.op());
        const aid = await client.identifiers().get(name);

        const op = await client
            .identifiers()
            .addEndRole(name, 'agent', client!.agent!.pre);
        await waitOperation(client, await op.op());
        console.log(name, 'AID:', aid.prefix);
        return aid;
    }
}

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
 * Connect or boot a number of SignifyClient instances
 * @example
 * <caption>Create two clients with random secrets</caption>
 * let client1: SignifyClient, client2: SignifyClient;
 * beforeAll(async () => {
 *   [client1, client2] = await getOrCreateClients(2);
 * });
 * @example
 * <caption>Launch jest from shell with pre-defined secrets</caption>
 * $ SIGNIFY_SECRETS="0ACqshJKkJ7DDXcaDuwnmI8s,0ABqicvyicXGvIVg6Ih-dngE" npx jest ./tests
 */
export async function getOrCreateClients(
    count: number,
    brans: string[] | undefined = undefined
): Promise<SignifyClient[]> {
    const tasks: Promise<SignifyClient>[] = [];
    const secrets = process.env['SIGNIFY_SECRETS']?.split(',');
    for (let i = 0; i < count; i++) {
        tasks.push(
            getOrCreateClient(brans?.at(i) ?? secrets?.at(i) ?? undefined)
        );
    }
    const clients: SignifyClient[] = await Promise.all(tasks);
    console.log(`SIGNIFY_SECRETS="${clients.map((i) => i.bran).join(',')}"`);
    return clients;
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
    return op.response.i;
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
    let id: any = undefined;
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
    const eid = client.agent?.pre!;
    if (!(await hasEndRole(client, name, 'agent', eid))) {
        const result: EventResult = await client
            .identifiers()
            .addEndRole(name, 'agent', eid);
        let op = await result.op();
        op = await waitOperation(client, op);
        console.log('identifiers.addEndRole', op);
    }

    const oobi = await client.oobis().get(name, 'agent');
    const result: [string, string] = [id, oobi.oobis[0]];
    console.log(name, result);
    return result;
}

export async function getOrIssueCredential(
    issuerClient: SignifyClient,
    issuerAid: Aid,
    recipientAid: Aid,
    issuerRegistry: { regk: string },
    credData: any,
    schema: string,
    rules?: any,
    source?: any,
    privacy = false
): Promise<any> {
    const credentialList = await issuerClient.credentials().list();

    if (credentialList.length > 0) {
        const credential = credentialList.find(
            (cred: any) =>
                cred.sad.s === schema &&
                cred.sad.i === issuerAid.prefix &&
                cred.sad.a.i === recipientAid.prefix
        );
        if (credential) return credential;
    }

    const issResult = await issuerClient.credentials().issue(issuerAid.name, {
        ri: issuerRegistry.regk,
        s: schema,
        u: privacy ? new Salter({}).qb64 : undefined,
        a: {
            i: recipientAid.prefix,
            u: privacy ? new Salter({}).qb64 : undefined,
            ...credData,
        },
        r: rules,
        e: source,
    });

    await waitOperation(issuerClient, issResult.op);
    const credential = await issuerClient
        .credentials()
        .get(issResult.acdc.ked.d);

    return credential;
}

export async function getStates(client: SignifyClient, prefixes: string[]) {
    const participantStates = await Promise.all(
        prefixes.map((p) => client.keyStates().get(p))
    );
    return participantStates.map((s) => s[0]);
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
 * Logs a warning for each un-handled notification.
 * <p>Replace warnNotifications with assertNotifications when test handles all notifications
 * @see assertNotifications
 */
export async function warnNotifications(
    ...clients: SignifyClient[]
): Promise<void> {
    let count = 0;
    for (const client of clients) {
        const res = await client.notifications().list();
        const notes = res.notes.filter((i: { r: boolean }) => i.r === false);
        if (notes.length > 0) {
            count += notes.length;
            console.warn('notifications', notes);
        }
    }
    expect(count).toBeGreaterThan(0); // replace warnNotifications with assertNotifications
}

async function deleteOperations<T = any>(
    client: SignifyClient,
    op: Operation<T>
) {
    if (op.metadata?.depends) {
        await deleteOperations(client, op.metadata.depends);
    }

    await client.operations().delete(op.name);
}

export async function getReceivedCredential(
    client: SignifyClient,
    credId: string
): Promise<any> {
    const credentialList = await client.credentials().list({
        filter: {
            '-d': credId,
        },
    });
    let credential: any;
    if (credentialList.length > 0) {
        assert.equal(credentialList.length, 1);
        credential = credentialList[0];
    }
    return credential;
}

/**
 * Mark and remove notification.
 */
export async function markAndRemoveNotification(
    client: SignifyClient,
    note: Notification
): Promise<void> {
    try {
        await client.notifications().mark(note.i);
    } finally {
        await client.notifications().delete(note.i);
    }
}

/**
 * Mark notification as read.
 */
export async function markNotification(
    client: SignifyClient,
    note: Notification
): Promise<void> {
    await client.notifications().mark(note.i);
}

export async function resolveOobi(
    client: SignifyClient,
    oobi: string,
    alias?: string
) {
    const op = await client.oobis().resolve(oobi, alias);
    await waitOperation(client, op);
}

export async function waitForCredential(
    client: SignifyClient,
    credSAID: string,
    MAX_RETRIES: number = 10
) {
    let retryCount = 0;
    while (retryCount < MAX_RETRIES) {
        const cred = await getReceivedCredential(client, credSAID);
        if (cred) return cred;

        await new Promise((resolve) => setTimeout(resolve, 1000));
        console.log(` retry-${retryCount}: No credentials yet...`);
        retryCount = retryCount + 1;
    }
    throw Error('Credential SAID: ' + credSAID + ' has not been received');
}

export async function waitAndMarkNotification(
    client: SignifyClient,
    route: string
) {
    const notes = await waitForNotifications(client, route);

    await Promise.all(
        notes.map(async (note) => {
            await markNotification(client, note);
        })
    );

    return notes[notes.length - 1]?.a.d ?? '';
}

export async function waitForNotifications(
    client: SignifyClient,
    route: string,
    options: RetryOptions = {}
): Promise<Notification[]> {
    return retry(async () => {
        const response: { notes: Notification[] } = await client
            .notifications()
            .list();

        const notes = response.notes.filter(
            (note) => note.a.r === route && note.r === false
        );

        if (!notes.length) {
            throw new Error(`No notifications with route ${route}`);
        }

        return notes;
    }, options);
}

/**
 * Poll for operation to become completed.
 * Removes completed operation
 */
export async function waitOperation<T = any>(
    client: SignifyClient,
    op: Operation<T> | string,
    signal?: AbortSignal
): Promise<Operation<T>> {
    if (typeof op === 'string') {
        op = await client.operations().get(op);
    }

    op = await client
        .operations()
        .wait(op, { signal: signal ?? AbortSignal.timeout(30000) });
    await deleteOperations(client, op);

    return op;
}
