import { strict as assert } from "assert"
import signify from "signify-ts"

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
    console.log("Client 1 connected. Client AID:",state1.controller.state.i,"Agent AID: ", state1.agent.i)

    let icpResult = client1.identifiers().create('aid1', {algo: signify.Algos.randy})
    let op = await icpResult.op()
    assert.equal(op['done'], true)
    let aid = op['response']
    const icp = new signify.Serder(aid)
    assert.equal(icp.verfers.length, 1)
    assert.equal(icp.digers.length, 1)
    assert.equal(icp.ked['kt'], '1')
    assert.equal(icp.ked['nt'], '1')


    let aids = await client1.identifiers().list()
    assert.equal(aids.aids.length, 1)
    aid = aids.aids[0]
    assert.equal(aid.name, 'aid1')
    assert.equal(aid.prefix, icp.pre)

    icpResult = await client1.identifiers().interact("aid1", [icp.pre])
    op = await icpResult.op()
    assert.equal(op['done'], true)
    let ked = op['response']
    let ixn = new signify.Serder(ked)
    assert.equal(ixn.ked['s'], '1')
    assert.deepEqual(ixn.ked['a'], [icp.pre])

    aids = await client1.identifiers().list()
    assert.equal(aids.aids.length, 1)
    aid = aids.aids[0]

    const events = client1.keyEvents()
    let log = await events.get(aid["prefix"])
    assert.equal(log.length, 2)

    icpResult = await client1.identifiers().rotate('aid1')
    op = await icpResult.op()
    assert.equal(op['done'], true)
    ked = op['response']
    let rot = new signify.Serder(ked)
    assert.equal(rot.ked['s'], '2')
    assert.equal(rot.verfers.length, 1)
    assert.equal(rot.digers.length, 1)
    assert.notEqual(rot.verfers[0].qb64, icp.verfers[0].qb64)
    assert.notEqual(rot.digers[0].qb64, icp.digers[0].qb64)
    let dig = new signify.Diger({code: signify.MtrDex.Blake3_256},rot.verfers[0].qb64b, )
    assert.equal(dig.qb64, icp.digers[0].qb64)
    log = await events.get(aid["prefix"])
    assert.equal(log.length, 3)
    console.log("Randy test passed")

}