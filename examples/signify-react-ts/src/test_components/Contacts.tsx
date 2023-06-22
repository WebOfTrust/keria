// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import { SignifyClient, ready, Serder } from "signify-ts";
import {strict as assert} from "assert";
import { useState } from 'react';

export function Contacts() {
    const [testResult, setTestResult] = useState('');

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
                            let challenges1 = client1.challenges()
                            let challenge1_small = await challenges1.generate_challenge(128)
                            assert.equal(challenge1_small.words.length, 12)
                            let challenge1_big = await challenges1.generate_challenge(256)
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
                            

                            op1 = await oobis1.resolve("http://127.0.0.1:5642/oobi/"+aid2.i+"/witness")
                            while (!op1["done"]) {
                                op1 = await operations1.get(op1["name"]);
                                await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                            }

                            op2 = await oobis2.resolve("http://127.0.0.1:5642/oobi/"+aid1.i+"/witness")
                            while (!op2["done"]) {
                                op2 = await operations2.get(op2["name"]);
                                await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                            }

                            await contacts1.list_contacts()

                            await contacts1.add_contact(aid2.i,{alias: "rodo"})

                            await contacts1.list_contacts()

                            await contacts1.get_contact(aid2.i)

                            await contacts1.update_contact(aid2.i,{alias: "rodo2"})

                            await contacts1.get_contact(aid2.i)

                            // await contacts1.delete_contact(aid2.i)

                            await contacts1.list_contacts()

                            op1 = await oobis1.resolve("http://127.0.0.1:5642/oobi/EDIX9959tP3TL_F0kB3s3_njSSVmv-As15Ny7IjTK9dv/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha","keripy")
                            while (!op1["done"]) {
                                op1 = await operations1.get(op1["name"]);
                                await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                            }

                            await contacts1.add_contact("EDIX9959tP3TL_F0kB3s3_njSSVmv-As15Ny7IjTK9dv",{alias: "rodo"})

                            while (true){
                                await contacts1.list_contacts()
                                await new Promise(resolve => setTimeout(resolve, 10000))
                            }

                            setTestResult("Passed")
                        }
                        catch (e) {
                            console.log(e)
                            setTestResult("Failed")
                        }
                    }} >Contacts Integration Test</button>{testResult}
            </div>
        </>
    )
}


