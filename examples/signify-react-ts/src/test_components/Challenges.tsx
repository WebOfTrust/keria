// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import { SignifyClient, ready, Serder, Diger, MtrDex, CredentialTypes } from "signify-ts";
import {strict as assert} from "assert";
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
                            const bran = '0123456789abcdefghijk'
                            const client = new SignifyClient(url, bran)
                            assert.equal(client.controller.pre, 'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose')
                            await client.connect()
                            const identifiers = client.identifiers()
                            const ids = await identifiers.list_identifiers()
                            assert.equal(ids[0].prefix,'EBcIURLpxmVwahksgrsGW6_dUw0zBhyEHYFk17eWrZfk')

                            let challenges = client.challenges()
                            let challenge_small = await challenges.get_challenge(128)
                            assert.equal(challenge_small.words.length, 12)
                            let challenge_big = await challenges.get_challenge(256)
                            assert.equal(challenge_big.words.length, 24)
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


