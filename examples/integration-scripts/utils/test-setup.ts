import { CreateIdentiferArgs, EventResult, SignifyClient, Tier, randomPasscode, ready } from "signify-ts";
import { resolveEnvironment } from "./resolve-env";
import { waitOperation } from "./test-util";

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
export async function getOrCreateClients(count: number, brans: string[] | undefined = undefined): Promise<SignifyClient[]> {
    let tasks: Promise<SignifyClient>[] = [];
    let secrets = process.env["SIGNIFY_SECRETS"]?.split(",");
    for (let i = 0; i < count; i++) {
        tasks.push(getOrCreateClient(brans?.at(i) ?? secrets?.at(i) ?? undefined));
    }
    let clients: SignifyClient[] = await Promise.all(tasks);
    console.log(`SIGNIFY_SECRETS="${clients.map(i => i.bran).join(",")}"`);
    return clients;
}

/**
 * Connect or boot a SignifyClient instance
 */
export async function getOrCreateClient(bran: string | undefined = undefined): Promise<SignifyClient> {
    let env = resolveEnvironment();
    await ready();
    bran ??= randomPasscode();
    bran = bran.padEnd(21, "_");
    let client = new SignifyClient(env.url, bran, Tier.low, env.bootUrl);
    try {
        await client.connect();
    } catch {
        let res = await client.boot();
        if (!res.ok) throw new Error();
        await client.connect();
    }
    console.log("client", { agent: client.agent?.pre, controller: client.controller.pre });
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
export async function getOrCreateIdentifier(client: SignifyClient, name: string): Promise<[string, string]> {
    let id: any = undefined;
    try {
        let identfier = await client.identifiers().get(name);
        // console.log("identifiers.get", identfier);
        id = identfier.prefix;
    } catch {
        let env = resolveEnvironment();
        let args: CreateIdentiferArgs = {
            toad: env.witnessIds.length,
            wits: env.witnessIds
        };
        let result: EventResult = await client.identifiers().create(name, args);
        let op = await result.op();
        op = await waitOperation(client, op);
        // console.log("identifiers.create", op);
        id = op.response.i;
    }
    let eid = client.agent?.pre!;
    if (!await hasEndRole(client, name, "agent", eid)) {
        let result: EventResult = await client.identifiers().addEndRole(name, "agent", eid);
        let op = await result.op();
        op = await waitOperation(client, op);
        // console.log("identifiers.addEndRole", op);
    }
    let oobi = await client.oobis().get(name, "agent");
    let result: [string, string] = [id, oobi.oobis[0]];
    console.log(name, result);
    return result;
}

/**
 * Get list of end role authorizations for a Keri idenfitier
 */
export async function getEndRoles(client: SignifyClient, alias: string, role?: string): Promise<any> {
    let path = (role !== undefined) ? `/identifiers/${alias}/endroles/${role}` : `/identifiers/${alias}/endroles`;
    let response: Response = await client.fetch(path, "GET", null);
    if (!response.ok) throw new Error(await response.text());
    let result = await response.json();
    // console.log("getEndRoles", result);
    return result;
}

/**
 * Test if end role is authorized for a Keri identifier
 */
export async function hasEndRole(client: SignifyClient, alias: string, role: string, eid: string): Promise<boolean> {
    let list = await getEndRoles(client, alias, role);
    for (let i of list) {
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
export async function getOrCreateContact(client: SignifyClient, name: string, oobi: string): Promise<string> {
    let list = await client.contacts().list(undefined, "alias", `^${name}$`);
    // console.log("contacts.list", list);
    if (list.length > 0) {
        let contact = list[0];
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
