// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import { SignifyClient, ready, Serder, Diger, MtrDex } from "signify-ts";
import {strict as assert} from "assert";
import { useState, useEffect } from 'react';


export function Delegation() {
    const [testResult, setTestResult] = useState('');
    useEffect(() => {
        ready().then(() => {
            console.log("signify client is ready")
        })
    }, [])

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
                            
                            // Delegator OOBI:
                            // http://127.0.0.1:5642/oobi/EHpD0-CDWOdu5RJ8jHBSUkOqBZ3cXeDVHWNb_Ul89VI7/witness

                            const delpre = "EHpD0-CDWOdu5RJ8jHBSUkOqBZ3cXeDVHWNb_Ul89VI7"
                            
                            
                            const identifiers = client.identifiers()
                            const operations = client.operations()
                            const oobis = client.oobis()

                            let op = await oobis.resolve("http://127.0.0.1:5642/oobi/"+delpre+"/witness")
                            let count = 0;
                            while (!op["done"] && count <= 25) {
                                op = await operations.get(op["name"]);
                                await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                                count++;
                            }

                            op = await identifiers.create('aid1', {delpre: delpre})
                            let pre = op["metadata"]["pre"]

                            while (!op["done"]) {
                                op = await operations.get(op["name"]);
                                await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                            }

                            let icp1 = new Serder(op["response"])
                            assert.equal(icp1.pre, pre)

                            setTestResult("Passed")
                        }
                        catch (e) {
                            console.log(e)
                            setTestResult("Failed")
                        }
                    }} >Delegation Integration Test</button>{testResult}
            </div>
        </>
    )
}


