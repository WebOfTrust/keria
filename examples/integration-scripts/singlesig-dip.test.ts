import { CreateIdentiferArgs, EventResult, SignifyClient } from "signify-ts";
import { getOrCreateClients, getOrCreateContact, getOrCreateIdentifier } from "./utils/test-setup";
import { waitOperation } from "./utils/test-util";
import { resolveEnvironment } from "./utils/resolve-env";

let client1: SignifyClient, client2: SignifyClient;
let name1_id: string, name1_oobi: string;
let contact1_id: string;

beforeAll(async () => {
    [client1, client2] = await getOrCreateClients(2);
});
beforeAll(async () => {
    [name1_id, name1_oobi] = await getOrCreateIdentifier(client1, "name1");
});
beforeAll(async () => {
    contact1_id = await getOrCreateContact(client2, "contact1", name1_oobi);
});

describe("singlesig-dip", () => {
    test("delegate1a", async () => {
        let kargs: CreateIdentiferArgs = {
            delpre: name1_id
        };
        let result = await client2.identifiers().create("delegate1", kargs);
        let op = await result.op();
        let dip1 = await client2.identifiers().get("delegate1");
        expect(op.name).toEqual(`delegation.${dip1.prefix}`);
    });
    test("delegator1", async () => {
        let dip1 = await client2.identifiers().get("delegate1");
        let seal = {
            i: dip1.prefix,
            s: 0,
            d: dip1.prefix
        };
        let result = await client1.identifiers().interact("name1", seal);
        let op = waitOperation(client1, await result.op());
    })
    test("delegate1b", async () => {
        let dip1 = await client2.identifiers().get("delegate1");
        let op: any = { name: `delegation.${dip1.prefix}` };
        op = await waitOperation(client2, op);
        expect(dip1.prefix).toEqual(op.response.i);
    });
    test("delegate2a", async () => {
        let env = resolveEnvironment();
        let kargs: CreateIdentiferArgs = {
            delpre: name1_id,
            toad: env.witnessIds.length,
            wits: env.witnessIds
        };
        let result = await client2.identifiers().create("delegate2", kargs);
        let op = await result.op();
        let dip1 = await client2.identifiers().get("delegate2");
        expect(op.name).toEqual(`delegation.${dip1.prefix}`);
    });
    test("delegator2", async () => {
        let dip1 = await client2.identifiers().get("delegate2");
        let seal = {
            i: dip1.prefix,
            s: 0,
            d: dip1.prefix
        };
        let result = await client1.identifiers().interact("name1", seal);
        let op = waitOperation(client1, await result.op());
    })
    test("delegate2b", async () => {
        let dip1 = await client2.identifiers().get("delegate2");
        let op: any = { name: `delegation.${dip1.prefix}` };
        op = await waitOperation(client2, op);
        expect(dip1.prefix).toEqual(op.response.i);
    });
});
