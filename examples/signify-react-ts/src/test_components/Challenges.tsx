// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import { SignifyClient, ready, Serder, Diger, MtrDex, CredentialTypes } from "signify-ts";
import { strict as assert } from "assert";
import { useState, useEffect } from 'react';

export function Challenges() {
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
                            const bran1 = '0123456789abcdefghijk'
                            const bran2 = '1123456789abcdefghijk'
                            const client1 = new SignifyClient(url, bran1)
                            await client1.boot()
                            await client1.connect()
                            const identifiers1 = client1.identifiers()
                            const operations1 = client1.operations()
                            const oobis1 = client1.oobis()
                            const contacts1 = client1.contacts()
                            const challenges1 = client1.challenges()
                            let challenge1_small = await challenges1.generate(128)
                            assert.equal(challenge1_small.words.length, 12)
                            let challenge1_big = await challenges1.generate(256)
                            assert.equal(challenge1_big.words.length, 24)
                            let op1 = await identifiers1.create('alex',  {
                                toad: 2,
                                wits: [
                                    "BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
                                    "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
                                    "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"]
                                })
                            while (!op1["done"] ) {
                                    op1 = await operations1.get(op1["name"]);
                                    await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                                }
                            const aid1 = op1['response']

                            const client2 = new SignifyClient(url, bran2)
                            await client2.boot()
                            await client2.connect()
                            const identifiers2 = client2.identifiers()
                            const challenges2 = client2.challenges()
                            const operations2 = client2.operations()
                            const oobis2 = client2.oobis()
                            let op2 = await identifiers2.create('rodo', {
                                toad: 2,
                                wits: [
                                    "BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
                                    "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
                                    "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"]
                                })
                            while (!op2["done"] ) {
                                    op2 = await operations2.get(op2["name"]);
                                    await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                                }
                            const aid2 = op2['response']
                            
                            await identifiers1.addEndRole("alex", 'agent', client1!.agent!.pre)
                            await identifiers2.addEndRole("rodo", 'agent', client2!.agent!.pre)
                            let oobi1 = await oobis1.get("alex","agent")
                            let oobi2 = await oobis2.get("rodo","agent")
                            
                            op1 = await oobis1.resolve(oobi2.oobis[0],"rodo")
                            while (!op1["done"]) {
                                op1 = await operations1.get(op1["name"]);
                                await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                            }
                            op2 = await oobis2.resolve(oobi1.oobis[0],"alex")
                            while (!op2["done"]) {
                                op2 = await operations2.get(op2["name"]);
                                await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                            }
                            await contacts1.list(undefined, undefined, undefined)
                            await challenges2.respond('rodo', aid1.i, challenge1_small.words)

                            let challenge_received = false
                            let contacts = []
                            while (!challenge_received) {
                                contacts = await contacts1.list(undefined, undefined, undefined)
                                if (contacts[0].challenges.length > 0 ){
                                    if (JSON.stringify(contacts[0].challenges[0].words) == JSON.stringify(challenge1_small.words)) {
                                        challenge_received = true
                                    }
                                }
                                await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                            }
                            await challenges1.accept('alex', aid2.i, contacts[0].challenges[0].said)
                            await contacts1.list(undefined, undefined, undefined)
                            setTestResult("Passed")
                        }
                        catch (e) {
                            console.log(e)
                            setTestResult("Failed")
                        }
                    }} >Challenges Test</button>{testResult}
            </div>
        </>
    )
}


