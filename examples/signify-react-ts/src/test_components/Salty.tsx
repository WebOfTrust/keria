// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import { SignifyClient, ready, Serder, Tier } from "signify-ts";
import {strict as assert} from "assert";
import { useState } from 'react';

export function Salty() {
    const [testResult, setTestResult] = useState('');

    return (
        <>
            <div className="card">
                <button
                    onClick={async () => {
                        try {
                            const url = "http://localhost:3901"
                            const bran = '0123456789abcdefghijk'

                            let client = new SignifyClient(url, bran, Tier.med)
                            assert.equal(client.controller.pre, 'EOgQvKz8ziRn7FdR_ebwK9BkaVOnGeXQOJ87N6hMLrK0')

                            client = new SignifyClient(url, bran, Tier.low)
                            assert.equal(client.controller.pre, 'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose')
                            const r1 = await client.boot()
                            assert.equal(r1.status, 202)
                            await client.connect()
                            assert.notEqual(client.agent, undefined)
                            assert.equal(client.agent?.pre, 'EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei')
                            assert.equal(client.agent?.anchor, 'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose')
                            const identifiers = client.identifiers()
                            let aids = await identifiers.list()
                            assert.equal(aids.length, 0)
                            let op = await identifiers.create('aid1', {bran: '0123456789abcdefghijk'})
                            assert.equal(op['done'], true)
                            const aid1 = op['response']
                            const icp = new Serder(aid1)
                            assert.equal(icp.pre, 'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK')
                            assert.equal(icp.verfers.length, 1)
                            assert.equal(icp.verfers[0].qb64, 'DPmhSfdhCPxr3EqjxzEtF8TVy0YX7ATo0Uc8oo2cnmY9')
                            assert.equal(icp.digers.length, 1)
                            assert.equal(icp.digers[0].qb64, 'EAORnRtObOgNiOlMolji-KijC_isa3lRDpHCsol79cOc')
                            assert.equal(icp.ked['kt'], '1')
                            assert.equal(icp.ked['nt'], '1')
                            aids = await identifiers.list()
                            assert.equal(aids.length, 1)
                            let aid = aids.pop()
                            assert.equal(aid.name, 'aid1')
                            let salt  = aid.salty
                            assert.equal(salt.pidx, 0)
                            assert.equal(salt.stem, 'signify:aid')
                            assert.equal(aid.prefix, icp.pre)

                            op = await identifiers.create('aid2', {count:3, ncount:3, isith:"2", nsith:"2", bran:"0123456789lmnopqrstuv"})
                            assert.equal(op['done'], true)
                            const aid2 = op['response']
                            const icp2 = new Serder(aid2)
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
                            aids = await identifiers.list()
                            assert.equal(aids.length, 2)
                            aid = aids[1]
                            assert.equal(aid.name, 'aid2')
                            salt  = aid.salty
                            assert.equal(salt.pidx, 1)
                            assert.equal(salt.stem, 'signify:aid')
                            assert.equal(aid.prefix, icp2.pre)

                            op = await identifiers.rotate('aid1')
                            assert.equal(op['done'], true)
                            let ked = op['response']
                            let rot = new Serder(ked)
                            assert.equal(rot.ked['d'], 'EBQABdRgaxJONrSLcgrdtbASflkvLxJkiDO0H-XmuhGg')
                            assert.equal(rot.ked['s'], '1')
                            assert.equal(rot.verfers.length, 1)
                            assert.equal(rot.digers.length, 1)
                            assert.equal(rot.verfers[0].qb64, 'DHgomzINlGJHr-XP3sv2ZcR9QsIEYS3LJhs4KRaZYKly')
                            assert.equal(rot.digers[0].qb64, 'EJMovBlrBuD6BVeUsGSxLjczbLEbZU9YnTSud9K4nVzk')

                            op = await identifiers.interact("aid1", [icp.pre])
                            assert.equal(op['done'], true)
                            ked = op['response']
                            let ixn = new Serder(ked)
                            assert.equal(ixn.ked['d'], 'ENsmRAg_oM7Hl1S-GTRMA7s4y760lQMjzl0aqOQ2iTce')
                            assert.equal(ixn.ked['s'], '2')
                            assert.deepEqual(ixn.ked['a'], [icp.pre])

                            aid = await identifiers.get("aid1")
                            const state = aid["state"]

                            assert.equal(state['s'], '2')
                            assert.equal(state['f'], '2')
                            assert.equal(state['et'], 'ixn')
                            assert.equal(state['d'], ixn.ked['d'])
                            assert.equal(state['ee']['d'], rot.ked['d'])

                            const events = client.keyEvents()
                            const log = await events.get(aid["prefix"])
                            assert.equal(log.length, 3)
                            let serder = new Serder(log[0])
                            assert.equal(serder.pre, icp.pre)
                            assert.equal(serder.ked['d'], icp.ked['d'])
                            serder = new Serder(log[1])
                            assert.equal(serder.pre, rot.pre)
                            assert.equal(serder.ked['d'], rot.ked['d'])
                            serder = new Serder(log[2])
                            assert.equal(serder.pre, ixn.pre)
                            assert.equal(serder.ked['d'], ixn.ked['d'])
                            setTestResult("Passed")
                        }
                        catch (e) {
                            console.log(e)
                            setTestResult("Failed")
                        }
                    }} >Salty Integration Test</button>{testResult}
            </div>
        </>
    )
}


