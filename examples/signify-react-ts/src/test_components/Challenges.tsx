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
                            // await client1.boot()
                            await client1.connect()
                            const identifiers1 = client1.identifiers()
                            let challenges1 = client1.challenges()
                            let challenge1_small = await challenges1.get_challenge(128)
                            assert.equal(challenge1_small.words.length, 12)
                            let challenge1_big = await challenges1.get_challenge(256)
                            assert.equal(challenge1_big.words.length, 24)
                            let op1 = await identifiers1.create('alex', {})
                            let aid1 = op1['response']

                            const client2 = new SignifyClient(url, bran2)
                            // await client2.boot()
                            await client2.connect()
                            const identifiers2 = client2.identifiers()
                            const challenges2 = client2.challenges()
                            let op2 = await identifiers2.create('rodo', {})
                            let aid2 = op2['response']
                            console.log(aid2)


                            let challenge_to_send = await challenges1.send_challenge('alex', aid2.d, challenge1_small)
                            console.log(challenge_to_send)
                            await setTimeout(() => { }, 3000)
                        
                            let challenge_to_receive = await challenges2.accept_challenge('rodo', aid1.d, challenge_to_send.d)
                            console.log(challenge_to_receive)
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


