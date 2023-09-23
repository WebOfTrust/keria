import { strict as assert } from "assert"
import signify from "signify-ts"

const url = "http://127.0.0.1:3901"
const boot_url = "http://127.0.0.1:3903"

await run()

async function run() {
    await signify.ready()
    // Boot client
    const bran1 = signify.randomPasscode()
    const externalModule:ExternalModule = {
        type: "bip39",
        name: "bip39",
        params: []
    }
    const client1 = new signify.SignifyClient(url, bran1, signify.Tier.low, boot_url,externalModule);
    await client1.boot()
    await client1.connect()
    const state1 = await client1.state()
    console.log("Client 1 connected. Client AID:",state1.controller.state.i,"Agent AID: ", state1.agent.i)
    let words = ["asd", "asd", "asds"]
    let icpResult = client1.identifiers().create('aid1', {algo: signify.Algos.extern, extern_type:"bip39", extern:{mnemonics: words}})
    let op = await icpResult.op()
    assert.equal(op['done'], true)
    let aid = op['response']
}