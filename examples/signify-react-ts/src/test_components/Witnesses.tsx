// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import { SignifyClient, ready, Serder } from "signify-ts";
import {strict as assert} from "assert";
import { useState } from 'react';

export function Witnesses() {
    const [testResult, setTestResult] = useState('');

    return (
        <>
            <div className="card">
                <button
                    onClick={async () => {
                        try {
                            const url = "http://localhost:3901"
                            const bran = '0123456789abcdefghijk'
                            const client = new SignifyClient(url, bran)
                            assert.equal(client.controller.pre, 'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose')
                            const r1 = await client.boot()
                            assert.equal(r1.status, 202)
                            await client.connect()
                            assert.notEqual(client.agent, undefined)
                            assert.equal(client.agent?.pre, 'EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei')
                            assert.equal(client.agent?.anchor, 'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose')
                            const identifiers = client.identifiers()
                            const operations = client.operations()
                            let aids = await identifiers.list()
                            assert.equal(aids.aids.length, 0)

                            let op = await identifiers.create('aid1', {
                                bran: 'canIGetAWitnessSaltGreaterThan21',
                                toad: 2,
                                wits: [
                                    "BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
                                    "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
                                    "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"]
                                })


                            while (!op["done"] ) {
                                op = await operations.get(op["name"]);
                                await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                            }

                            const icp1 = await new Serder(op["response"])
                            assert.equal(icp1.pre, 'EGTFIbnFoA7G-f4FHzzXUMp6VAgQfJ-2nXqzfb5hVwKa')
                            assert.deepEqual(icp1.ked['b'], [
                                            "BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
                                            "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
                                            "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"])
                            assert.equal(icp1.ked['bt'], '2')

                            const aid1 = await identifiers.get("aid1")
                            assert.equal(aid1.name, 'aid1')
                            assert.equal(aid1.prefix, icp1.pre)
                            assert.equal(aid1.windexes.length, 3)

                            aids = await identifiers.list()
                            assert.equal(aids.aids.length, 1)
                            const aid = aids.aids.pop()
                            assert.equal(aid.prefix, icp1.pre)

                            setTestResult("Passed")
                        }
                        catch (e) {
                            console.log(e)
                            setTestResult("Failed")
                        }
                    }} >Witnesses Integration Test</button>{testResult}
            </div>
        </>
    )
}


