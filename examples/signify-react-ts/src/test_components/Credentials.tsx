// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import { SignifyClient, ready, Serder, Diger, MtrDex, CredentialTypes } from "signify-ts";
import {strict as assert} from "assert";
import { useState, useEffect } from 'react';
import { UndoRounded } from "@mui/icons-material";


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
                            const client1 = new SignifyClient(url, bran1)
                            await client1.boot()
                            await client1.connect()
                            const identifiers1 = client1.identifiers()
                            const operations1 = client1.operations()
                            const oobis1 = client1.oobis()
                            let op1 = await identifiers1.create('issuer',  {
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
                            let op2 = await identifiers2.create('holder', {
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
                            
                            await identifiers1.addEndRole("issuer", 'agent', client1!.agent!.pre)
                            await identifiers2.addEndRole("holder", 'agent', client2!.agent!.pre)
                            
                            op1 = await oobis1.resolve("http://127.0.0.1:5642/oobi/"+aid2.i+"/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha","rodo")
                            while (!op1["done"]) {
                                op1 = await operations1.get(op1["name"]);
                                await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                            }
                            op2 = await oobis2.resolve("http://127.0.0.1:5642/oobi/"+aid1.i+"/witness","alex")
                            while (!op2["done"]) {
                                op2 = await operations2.get(op2["name"]);
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


                            op1 = await client1.registries().create('issuer','vLEI', "AOLPzF1vRwMPo6tDfoxba1udvpu0jG_BCP_CI49rpMxK", false)
                            while (!op1["done"]) {
                                op1 = await operations1.get(op1["name"]);
                                await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                            }

                            await client1.registries().list('issuer')

                            await client1.schemas().get_schema("EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao")
                            await client2.schemas().list_all_schemas()
                            const vcdata = {
                                "LEI": "5493001KJTIIGC8Y1R17"
                              }
                            op1 = await client1.credentials().issue_credential('issuer','vLEI', aid2.i,'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao',{},{},vcdata,false)
                            while (!op1["done"]) {
                                op1 = await operations1.get(op1["name"]);
                                await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
                            }
                            await client2.credentials().list('holder')
                            // const creds = client.credentials()
                            // let rs = await creds.list(ids[0].prefix,CredentialTypes.received,'')
                            // console.log(rs)
                            // let said = rs[0]['sad']['d']
                            // let resp = await creds.export(ids[0].prefix,said)
                            // console.log(resp)
                            
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


