import { useState, useEffect, useRef } from 'react'
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import { SignifyClient, ready, Serder } from "signify-ts";
import { SignifyDemo } from './SignifyDemo';
import {strict as assert} from "assert";


function generateRandomKey() {
    const characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
    const length = 21;
    let result = "";
    for (let i = 0; i < length; i++) {
        result += characters.charAt(Math.floor(Math.random() * characters.length));
    }
    return result;
}

export function TestsComponent() {
    const [pre, setPre] = useState("")
    const [key, setKey] = useState(generateRandomKey())

    useEffect(() => {
        ready().then(() => {
            console.log("signify client is ready")
        })
    }, [])

    const inputRef = useRef(null)

    useEffect(() => {
        if (inputRef.current) {
            // inputRef.current.style.width = "auto"
            // inputRef.current.style.width = `${inputRef.current.scrollWidth}px`
        }
    }, [key])

    return (
        <>
            <div className="card">
                <SignifyDemo text={'Salty Integration Test'}
                    onClick={async () => {
                        try {
                            const url = "http://localhost:3901"
                            const bran = '0123456789abcdefghijk'
                            // const tier = Tiers.med
                            const client = new SignifyClient(url, bran)
                            assert.equal(client.controller.pre, 'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose')
                            const r1 = await client.boot()
                            assert.equal(r1.status, 202)
                            await client.connect()
                            assert.notEqual(client.agent, undefined)
                            assert.equal(client.agent?.pre, 'EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei')
                            assert.equal(client.agent?.anchor, 'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose')
                            const identifiers = client.identifiers()
                            let aids = await identifiers.list_identifiers()
                            assert.equal(aids.length, 0)
                            const aid1 = await identifiers.create('aid1', {bran: '0123456789abcdefghijk'})
                            const icp = await new Serder(aid1)
                            assert.equal(icp.pre, 'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK')
                            assert.equal(icp.verfers.length, 1)
                            assert.equal(icp.verfers[0].qb64, 'DPmhSfdhCPxr3EqjxzEtF8TVy0YX7ATo0Uc8oo2cnmY9')
                            assert.equal(icp.digers.length, 1)
                            assert.equal(icp.digers[0].qb64, 'EAORnRtObOgNiOlMolji-KijC_isa3lRDpHCsol79cOc')
                            // assert.equal(icp.tholder.num, 1)
                            // assert.equal(icp.ntholder.num, 1)
                            aids = await identifiers.list_identifiers()
                            assert.equal(aids.length, 1)
                            let aid = aids.pop()
                            assert.equal(aid.name, 'aid1')
                            let salt  = aid.salty
                            assert.equal(salt.pidx, 0)
                            assert.equal(salt.stem, 'signify:aid')
                            assert.equal(aid.prefix, icp.pre)

                            const aid2 = await identifiers.create('aid2', {count:3, ncount:3, isith:"2", nsith:"2", bran:"0123456789lmnopqrstuv"})
                            const icp2 = await new Serder(aid2)
                            assert.equal(icp2.pre,'EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX')
                            assert.equal(icp2.verfers.length, 3)
                            assert.equal(icp2.verfers[0].qb64, 'DGBw7C7AfC7jbD3jLLRS3SzIWFndM947TyNWKQ52iQx5')
                            assert.equal(icp2.verfers[1].qb64, 'DD_bHYFsgWXuCbz3SD0HjCIe_ITjRvEoCGuZ4PcNFFDz')
                            assert.equal(icp2.verfers[2].qb64, 'DEe9u8k0fm1wMFAuOIsCtCNrpduoaV5R21rAcJl0awze')
                            assert.equal(icp2.digers.length, 3)
                            assert.equal(icp2.digers[0].qb64, 'EML5FrjCpz8SEl4dh0U15l8bMRhV_O5iDcR1opLJGBSH')
                            assert.equal(icp2.digers[1].qb64, 'EJpKquuibYTqpwMDqEFAFs0gwq0PASAHZ_iDmSF3I2Vg')
                            assert.equal(icp2.digers[2].qb64, 'ELplTAiEKdobFhlf-dh1vUb2iVDW0dYOSzs1dR7fQo60')
                            // assert.equal(icp2.tholder.num, 2)
                            // assert.equal(icp2.ntholder.num, 2)
                            aids = await identifiers.list_identifiers()
                            assert.equal(aids.length, 2)
                            aid = aids[1]
                            assert.equal(aid.name, 'aid2')
                            salt  = aid.salty
                            assert.equal(salt.pidx, 1)
                            assert.equal(salt.stem, 'signify:aid')
                            assert.equal(aid.prefix, icp2.pre)

                            let ked = await identifiers.rotate('aid1')
                            let rot = await new Serder(ked)
                            assert.equal(rot.said, 'EBQABdRgaxJONrSLcgrdtbASflkvLxJkiDO0H-XmuhGg')
                            assert.equal(rot.sn, 1)
                            


                            return "Salty Integration Test Passed"
                        }
                        catch (e) {
                            console.log(e)
                            return 'Salt Integration Test Failed'
                        }
                    }} />
            </div>
        </>
    )
}


