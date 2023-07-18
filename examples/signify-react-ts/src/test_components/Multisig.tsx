// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import { SignifyClient, ready, Serder, Diger, MtrDex, Algos } from "signify-ts";
import {strict as assert} from "assert";
import { useState, useEffect } from 'react';


export function Multisig() {
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
                                                        
                            
                            const identifiers = client.identifiers()
                            const operations = client.operations()
                            const oobis = client.oobis()

                            let op = await identifiers.create('aid1', {bran: '0123456789abcdefghijk' })
                            assert.equal(op['done'], true)
                            const icp = op['response']
                            let serder = new Serder(icp)
                            assert.equal(serder.pre, "ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK")
                            
                            await identifiers.addEndRole("aid1", 'agent', client.agent.pre)

                            let oobi = await oobis.get("aid1")
                            console.log(oobi)

                            op = await oobis.resolve("http://127.0.0.1:5642/oobi/EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha","multisig1")
                            while (!op["done"]) {
                                op = await operations.get(op["name"]);
                                await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                            }
                            let multisig1 = op["response"]

                            op = await oobis.resolve("http://127.0.0.1:5642/oobi/EJccSRTfXYF6wrUVuenAIHzwcx3hJugeiJsEKmndi5q1/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha","multisig2")
                            while (!op["done"]) {
                                op = await operations.get(op["name"]);
                                await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                            }
                            let multisig2 = op["response"]

                            let aid1 = await identifiers.get("aid1")
                            let agent0 = aid1["state"]
                            let rstates = [multisig2, multisig1, agent0]
                            let states = rstates

                            op = await identifiers.create("multisig",{
                                algo: Algos.group,
                                mhab: aid1,
                                isith: 3, 
                                nsith: 3,
                                toad: 3,
                                wits: [
                                    "BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
                                    "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
                                    "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"],
                                states: states,
                                rstates: rstates
                            })
                            console.log("waiting on multisig creation...")
                            while (!op["done"]) {
                                op = await operations.get(op["name"]);
                                await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                            }
                            
                            // Join an interaction event with the group
                            const data = {i: "EE77q3_zWb5ojgJr-R1vzsL5yiL4Nzm-bfSOQzQl02dy"}
                            op = await identifiers.interact("multisig", data)
                            while (!op["done"]) {
                                op = await operations.get(op["name"]);
                                await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                            }
                            const ixn = new Serder(op["response"])
                            const events = await client.keyEvents()
                            const log = await events.get(ixn.pre)
                            assert.equal(log.length, 2)
                            op = await identifiers.rotate("aid1",{})
                            assert.equal(op['done'], true)
                            const rot = op['response']
                            serder = new Serder(rot)

                            aid1 = await identifiers.get("aid1")
                            agent0 = aid1["state"]
                            const keyState = await client.keyStates()
                            op = await keyState.query("EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4",0)
                            while (!op["done"]) {
                                op = await operations.get(op["name"]);
                                await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                            }
                            multisig1 = op["response"]

                            op = await keyState.query("EJccSRTfXYF6wrUVuenAIHzwcx3hJugeiJsEKmndi5q1", 0)
                            while (!op["done"]) {
                                op = await operations.get(op["name"]);
                                await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                            }
                            multisig2 = op["response"]
                            rstates = [multisig2, multisig1, agent0]
                            states = rstates

                            op = identifiers.rotate("multisig", {states: states, rstates: rstates})

                            setTestResult("Passed")
                        }
                        catch (e) {
                            console.log(e)
                            setTestResult("Failed")
                        }
                    }} >Multisig Integration Test</button>{testResult}
            </div>
        </>
    )
}


