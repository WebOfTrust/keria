// This scrip also work if you start keria with no config file with witness urls
import { strict as assert } from "assert";
import signify from "signify-ts";

const url = "http://127.0.0.1:3901"
const boot_url = "http://127.0.0.1:3903"

await run()
async function run() {
    await signify.ready()
    // Boot client
    const bran1 = signify.randomPasscode()
    const client1 = new signify.SignifyClient(url, bran1, signify.Tier.low, boot_url);
    await client1.boot()
    await client1.connect()
    const state1 = await client1.state()
    console.log("Client connected. Client AID:",state1.controller.state.i,"Agent AID: ", state1.agent.i)

    const witness = "BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha"

    // Client 1 resolves witness OOBI
    let op1 = await client1.oobis().resolve("http://127.0.0.1:5642/oobi/" + witness,"wit")
    while (!op1["done"]) {
        op1 = await client1.operations().get(op1.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    console.log("Witness OOBI resolved")

    // Client 1 creates AID with 1 witness
    let icpResult1 = await client1.identifiers().create('aid1',{
        toad: 1,
        wits: ["BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha"]
        })
    op1 = await icpResult1.op()
    while (!op1["done"] ) {
            op1 = await client1.operations().get(op1.name);
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    let aid1 = await client1.identifiers().get("aid1")
    console.log("AID:",aid1.prefix)
    assert.equal(aid1.state.b.length, 1)
    assert.equal(aid1.state.b[0], witness)

    icpResult1 = await client1.identifiers().rotate('aid1')
    op1 = await icpResult1.op()
    while (!op1["done"] ) {
            op1 = await client1.operations().get(op1.name);
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    aid1 = await client1.identifiers().get("aid1")
    assert.equal(aid1.state.b.length, 1)
    assert.equal(aid1.state.b[0], witness)
 
}