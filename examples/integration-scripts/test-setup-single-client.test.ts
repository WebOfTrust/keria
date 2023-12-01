import { SignifyClient } from "signify-ts";
import { getOrCreateClients, getOrCreateIdentifier } from "./utils/test-setup";

let client: SignifyClient;
let name1_id: string, name1_oobi: string;

beforeAll(async () => {
    // Create client with pre-defined secret. Allows working with known identifiers
    [client] = await getOrCreateClients(1, ["0ADF2TpptgqcDE5IQUF1HeTp"]);
});
beforeAll(async () => {
    [name1_id, name1_oobi] = await getOrCreateIdentifier(client, "name1");
});

describe("test-setup-single-client", () => {
    test("step1", async () => {
        expect(client.agent?.pre).toEqual("EC60ue9GOpQGrLBlS9T0dO6JkBTbv3V05Y4O730QBBoc");
        expect(client.controller?.pre).toEqual("EB3UGWwIMq7ppzcQ697ImQIuXlBG5jzh-baSx-YG3-tY");
    });
    test("step2", async () => {
        expect(name1_id).toEqual("ENpvkzG5PhOXPn0LOBIRR6wyd8YXZPW9dn7Drxd7jJcH");
        expect(name1_oobi).toEqual("http://localhost:3902/oobi/ENpvkzG5PhOXPn0LOBIRR6wyd8YXZPW9dn7Drxd7jJcH/agent/EC60ue9GOpQGrLBlS9T0dO6JkBTbv3V05Y4O730QBBoc");
    });
});
