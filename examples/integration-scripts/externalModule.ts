import { strict as assert } from "assert"
import signify from "signify-ts"
import {BIP39Shim} from './bip39_shim/src/bip39_shim.ts'

const url = "http://127.0.0.1:3901"
const boot_url = "http://127.0.0.1:3903"

await run()

async function run() {
    await signify.ready()
    const bran1 = signify.randomPasscode()
    const externalModule:signify.ExternalModule = {
        type: "bip39_shim",
        name: "bip39_shim",
        module: BIP39Shim
    }
    const client1 = new signify.SignifyClient(url, bran1, signify.Tier.low, boot_url,[externalModule]);
    await client1.boot()
    await client1.connect()
    const state1 = await client1.state()
    console.log("Client 1 connected. Client AID:",state1.controller.state.i,"Agent AID: ", state1.agent.i)
    let words = new BIP39Shim(0,{}).generateMnemonic(256)
    let icpResult = client1.identifiers().create('aid1', {algo: signify.Algos.extern, extern_type:"bip39_shim", extern:{mnemonics: words}})
    let op = await icpResult.op()
    assert.equal(op['done'], true)
}