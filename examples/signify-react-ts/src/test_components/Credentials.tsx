// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import { SignifyClient, ready, Serder, Diger, MtrDex, CredentialTypes } from "signify-ts";
import {strict as assert} from "assert";
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
                            const bran = '0123456789abcdefghijk'
                            const client = new SignifyClient(url, bran)
                            assert.equal(client.controller.pre, 'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose')
                            await client.connect()
                            const identifiers = client.identifiers()
                            const ids = await identifiers.list_identifiers()
                            assert.equal(ids[0].prefix,'EBcIURLpxmVwahksgrsGW6_dUw0zBhyEHYFk17eWrZfk')

                            const creds = client.credentials()
                            let rs = await creds.list(ids[0].prefix,CredentialTypes.received,'')
                            console.log(rs)
                            let said = rs[0]['sad']['d']
                            let resp = await creds.export(ids[0].prefix,said)
                            console.log(resp)
                            // console.log(JSON.stringify(resp,null,2))
                            
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


