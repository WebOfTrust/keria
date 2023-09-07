import { strict as assert } from "assert";

let signify: any;
const url = "http://127.0.0.1:3901"
const boot_url = "http://127.0.0.1:3903"

// @ts-ignore
import('signify-ts').then(
    (module) => {
        signify = module
        signify.ready().then(() => {
            console.log("*** Starting SALTY test ***");
            run().then(() => {
                console.log("*** Test complete ***")
            });
        });
    }
)

async function run() {
    
    // Boot client
    const bran1 = signify.randomPasscode()
    const client1 = new signify.SignifyClient(url, bran1, signify.Tier.low, boot_url);
    await client1.boot()
    await client1.connect()
    const state1 = await client1.state()
    console.log("Client 1 connected. Client AID:",state1.controller.state.i,"Agent AID: ", state1.agent.i)

    let icpResult = client1.identifiers().create('aid1', {bran: '0123456789abcdefghijk'})
    let op = await icpResult.op()
    assert.equal(op['done'], true)
    const aid1 = op['response']
    const icp = new signify.Serder(aid1)
    assert.equal(icp.pre, 'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK')
    assert.equal(icp.verfers.length, 1)
    assert.equal(icp.verfers[0].qb64, 'DPmhSfdhCPxr3EqjxzEtF8TVy0YX7ATo0Uc8oo2cnmY9')
    assert.equal(icp.digers.length, 1)
    assert.equal(icp.digers[0].qb64, 'EAORnRtObOgNiOlMolji-KijC_isa3lRDpHCsol79cOc')
    assert.equal(icp.ked['kt'], '1')
    assert.equal(icp.ked['nt'], '1')
    let aids = await client1.identifiers().list()
    assert.equal(aids.aids.length, 1)
    let aid = aids.aids.pop()
    assert.equal(aid.name, 'aid1')
    let salt  = aid.salty
    assert.equal(salt.pidx, 0)
    assert.equal(salt.stem, 'signify:aid')
    assert.equal(aid.prefix, icp.pre)

    icpResult = client1.identifiers().create('aid2', {count:3, ncount:3, isith:"2", nsith:"2", bran:"0123456789lmnopqrstuv"})
    op = await icpResult.op()
    assert.equal(op['done'], true)
    const aid2 = op['response']
    const icp2 = new signify.Serder(aid2)
    assert.equal(icp2.pre,'EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX')
    assert.equal(icp2.verfers.length, 3)
    assert.equal(icp2.verfers[0].qb64, 'DGBw7C7AfC7jbD3jLLRS3SzIWFndM947TyNWKQ52iQx5')
    assert.equal(icp2.verfers[1].qb64, 'DD_bHYFsgWXuCbz3SD0HjCIe_ITjRvEoCGuZ4PcNFFDz')
    assert.equal(icp2.verfers[2].qb64, 'DEe9u8k0fm1wMFAuOIsCtCNrpduoaV5R21rAcJl0awze')
    assert.equal(icp2.digers.length, 3)
    assert.equal(icp2.digers[0].qb64, 'EML5FrjCpz8SEl4dh0U15l8bMRhV_O5iDcR1opLJGBSH')
    assert.equal(icp2.digers[1].qb64, 'EJpKquuibYTqpwMDqEFAFs0gwq0PASAHZ_iDmSF3I2Vg')
    assert.equal(icp2.digers[2].qb64, 'ELplTAiEKdobFhlf-dh1vUb2iVDW0dYOSzs1dR7fQo60')
    assert.equal(icp2.ked['kt'], '2')
    assert.equal(icp2.ked['nt'], '2')
    aids = await client1.identifiers().list()
    assert.equal(aids.aids.length, 2)
    aid = aids.aids[1]
    assert.equal(aid.name, 'aid2')
    salt  = aid.salty
    assert.equal(salt.pidx, 1)
    assert.equal(salt.stem, 'signify:aid')
    assert.equal(aid.prefix, icp2.pre)

    await client1.identifiers().create('aid3')
    aids = await client1.identifiers().list()
    assert.equal(aids.aids.length, 3)
    aid = aids.aids[0]
    assert.equal(aid.name, 'aid1')

    aids = await client1.identifiers().list(1,2)
    assert.equal(aids.aids.length, 2)
    aid = aids.aids[0]
    assert.equal(aid.name, 'aid2')

    aids = await client1.identifiers().list(2,2)
    assert.equal(aids.aids.length, 1)
    aid = aids.aids[0]
    assert.equal(aid.name, 'aid3')

    icpResult = await client1.identifiers().rotate('aid1')
    op = await icpResult.op()
    assert.equal(op['done'], true)
    let ked = op['response']
    let rot = new signify.Serder(ked)
    assert.equal(rot.ked['d'], 'EBQABdRgaxJONrSLcgrdtbASflkvLxJkiDO0H-XmuhGg')
    assert.equal(rot.ked['s'], '1')
    assert.equal(rot.verfers.length, 1)
    assert.equal(rot.digers.length, 1)
    assert.equal(rot.verfers[0].qb64, 'DHgomzINlGJHr-XP3sv2ZcR9QsIEYS3LJhs4KRaZYKly')
    assert.equal(rot.digers[0].qb64, 'EJMovBlrBuD6BVeUsGSxLjczbLEbZU9YnTSud9K4nVzk')

    icpResult = await client1.identifiers().interact("aid1", [icp.pre])
    op = await icpResult.op()
    assert.equal(op['done'], true)
    ked = op['response']
    let ixn = new signify.Serder(ked)
    assert.equal(ixn.ked['d'], 'ENsmRAg_oM7Hl1S-GTRMA7s4y760lQMjzl0aqOQ2iTce')
    assert.equal(ixn.ked['s'], '2')
    assert.deepEqual(ixn.ked['a'], [icp.pre])

    aid = await client1.identifiers().get("aid1")
    const state = aid["state"]

    assert.equal(state['s'], '2')
    assert.equal(state['f'], '2')
    assert.equal(state['et'], 'ixn')
    assert.equal(state['d'], ixn.ked['d'])
    assert.equal(state['ee']['d'], rot.ked['d'])

    const events = client1.keyEvents()
    const log = await events.get(aid["prefix"])
    assert.equal(log.length, 3)
    let serder = new signify.Serder(log[0])
    assert.equal(serder.pre, icp.pre)
    assert.equal(serder.ked['d'], icp.ked['d'])
    serder = new signify.Serder(log[1])
    assert.equal(serder.pre, rot.pre)
    assert.equal(serder.ked['d'], rot.ked['d'])
    serder = new signify.Serder(log[2])
    assert.equal(serder.pre, ixn.pre)
    assert.equal(serder.ked['d'], ixn.ked['d'])
    console.log("Salty test passed")

}