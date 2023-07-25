// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import { SignifyClient, ready, Serder, Diger, MtrDex, CredentialTypes } from "signify-ts";
import { useState, useEffect } from 'react';


export function Credentials() {
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
                            const bran3 = '2123456789abcdefghijk'

                            const client1 = new SignifyClient(url, bran1)
                            await client1.boot()
                            await client1.connect()
                            const identifiers1 = client1.identifiers()
                            const operations1 = client1.operations()
                            const oobis1 = client1.oobis()
                            let op1 = await identifiers1.create('issuer',  {
                                toad: 3,
                                wits: [
                                    "BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
                                    "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
                                    "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"]
                                })
                            while (!op1["done"] ) {
                                    op1 = await operations1.get(op1["name"]);
                                    await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                                }

                            const client2 = new SignifyClient(url, bran2)
                            await client2.boot()
                            await client2.connect()
                            const identifiers2 = client2.identifiers()
                            const operations2 = client2.operations()
                            const oobis2 = client2.oobis()
                            // let client2 = client1
                            // let identifiers2 = identifiers1
                            // let operations2 = operations1
                            // let oobis2 = oobis1
                            let op2 = await identifiers2.create('recipient', {
                                toad: 3,
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

                            const client3 = new SignifyClient(url, bran3)
                            await client3.boot()
                            await client3.connect()
                            const identifiers3 = client3.identifiers()
                            const operations3 = client3.operations()
                            const oobis3 = client3.oobis()
                            let op3 = await identifiers3.create('verifier', {
                                toad: 3,
                                wits: [
                                    "BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
                                    "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
                                    "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"]
                                })
                            while (!op3["done"] ) {
                                    op3 = await operations3.get(op3["name"]);
                                    await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                                }
                            
                            await identifiers1.addEndRole("issuer", 'agent', client1!.agent!.pre)
                            await identifiers2.addEndRole("recipient", 'agent', client2!.agent!.pre)
                            await identifiers3.addEndRole("verifier", 'agent', client3!.agent!.pre)
                            let oobi1 = await oobis1.get("issuer","agent")
                            let oobi2 = await oobis2.get("recipient","agent")
                            let oobi3 = await oobis3.get("verifier","agent")
                            
                            op1 = await oobis1.resolve(oobi2.oobis[0],"recipient")

                            while (!op1["done"]) {
                                op1 = await operations1.get(op1["name"]);
                                await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                            }
                            op1 = await oobis1.resolve(oobi3.oobis[0],"verifier")

                            while (!op1["done"]) {
                                op1 = await operations1.get(op1["name"]);
                                await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                            }


                            op2 = await oobis2.resolve(oobi1.oobis[0],"issuer")

                            while (!op2["done"]) {
                                op2 = await operations2.get(op2["name"]);
                                await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                            }

                            op2 = await oobis2.resolve(oobi3.oobis[0],"verifier")

                            while (!op2["done"]) {
                                op2 = await operations2.get(op2["name"]);
                                await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                            }

                            op3 = await oobis3.resolve(oobi2.oobis[0],"issuer")
                            while (!op3["done"]) {
                                op3 = await operations3.get(op3["name"]);
                                await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                            }

                            op1 = await oobis1.resolve("http://127.0.0.1:7723/oobi/EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao","schema")
                            while (!op1["done"]) {
                                op1 = await operations1.get(op1["name"]);
                                await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                            }
                            op2 = await oobis2.resolve("http://127.0.0.1:7723/oobi/EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao","schema")
                            while (!op2["done"]) {
                                op2 = await operations2.get(op2["name"]);
                                await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                            }

                            op3 = await oobis3.resolve("http://127.0.0.1:7723/oobi/EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao","schema")
                            while (!op3["done"]) {
                                op3 = await operations3.get(op3["name"]);
                                await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                            }


                            op1 = await client1.registries().create('issuer','vLEI', "AOLPzF1vRwMPo6tDfoxba1udvpu0jG_BCP_CI49rpMxK")
                            while (!op1["done"]) {
                                op1 = await operations1.get(op1["name"]);
                                await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                            }

                            let registries = await client1.registries().list('issuer')

                            await client1.schemas().get("EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao")
                            await client2.schemas().list()
                            const vcdata = {
                                "LEI": "5493001KJTIIGC8Y1R17"
                              }
                            op1 = await client1.credentials().issue('issuer',registries[0].regk, 'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao',aid2.i,vcdata)
                            while (!op1["done"]) {
                                op1 = await operations1.get(op1["name"]);
                                await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                            }
                            // await new Promise(resolve => setTimeout(resolve, 20000))
                            let creds = await client1.credentials().list('issuer')
                            await client1.credentials().list('issuer')
                            await client2.credentials().list('recipient')
                            
                            await client1.credentials().present('issuer', creds[0].sad.d, 'verifier', true)
                            await new Promise(resolve => setTimeout(resolve, 5000))
                            await client3.credentials().list('verifier')

                            op1 = await client1.credentials().revoke('issuer', creds[0].sad.d)
                            // while (!op1["done"]) {
                            //     op1 = await operations1.get(op1["name"]);
                            //     await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                            // }
                            await new Promise(resolve => setTimeout(resolve, 5000))
                            await client1.credentials().list('issuer')
                            await client2.credentials().list('recipient')
                            await client3.credentials().list('verifier')

                            await client1.credentials().present('issuer', creds[0].sad.d, 'verifier', true)
                            await new Promise(resolve => setTimeout(resolve, 5000))
                            await client3.credentials().list('verifier')
                            setTestResult("Passed")
                        }
                        catch (e) {
                            console.log(e)
                            setTestResult("Failed")
                        }
                    }} >Credential Integration Test</button>{testResult}
            </div>
        </>
    )
}


