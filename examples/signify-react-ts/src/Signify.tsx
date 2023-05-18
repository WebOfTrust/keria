import { useState, useEffect, useRef } from 'react'
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import { SignifyClient, ready } from "signify-ts";
import { SignifyDemo } from './SignifyDemo';

function generateRandomKey() {
    const characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
    const length = 21;
    let result = "";
    for (let i = 0; i < length; i++) {
        result += characters.charAt(Math.floor(Math.random() * characters.length));
    }
    return result;
}

export function Signify() {
    const [pre, setPre] = useState("")
    const [icp, setICP] = useState("")
    const [key, setKey] = useState(generateRandomKey())
    const [response, setResponse] = useState("")



    useEffect(() => {
        ready().then(() => {
            console.log("signify client is ready")
        })
    }, [])

    const bootAgent = async () => {
        if (!key) {
            alert("Please enter a valid key.")
            return
        }
        //check len of key is 21
        if (key.length !== 21) {
            alert("Invalid key lenght " + key.length)
            return
        }
        const client = new SignifyClient("http://localhost:3901", key)
        setPre(client.controller.pre)
        let res = await client.boot()
        console.log(res)
    }

    const inputRef = useRef(null)

    useEffect(() => {
        if (inputRef.current) {
            inputRef.current.style.width = "auto"
            inputRef.current.style.width = `${inputRef.current.scrollWidth}px`
        }
    }, [key])

    return (
        <>
            <div className="card">
                {/* show kel*/}
                <div className="form">
                    <label htmlFor="key">Enter 21 character passcode:</label>
                    <input type="text" id="key" value={key} onChange={(e) => setKey(e.target.value)} ref={inputRef} className="button" />
                    <button
                        onClick={async () => { await bootAgent() }}
                        className="button"
                    >Boot Keria </button>
                </div>
                <p >
                    AID is {pre}
                </p>
                {/* show kel*/}
                <SignifyDemo text={'Agent State'}
                    onClick={async () => {
                        const client = new SignifyClient("http://localhost:3901", key)
                        let res = await client.state()

                        let resp = JSON.stringify(res, null, 2)
                        console.log(resp)
                        return resp
                    }} />
                <SignifyDemo text={'Agent Connect'}
                    onClick={async () => {
                        try {
                            const client = new SignifyClient("http://localhost:3901", key)
                            await client.boot()
                            let res = await client.connect()
                            console.log('connected res, ', res)
                            let res1 = await client.get_identifiers()

                            return 'Connected to agent'
                        }
                        catch (e) {
                            console.log(e)
                            return 'Error connecting to agent'
                        }
                    }} />
                <SignifyDemo text={'Get identifiers'}
                    onClick={async () => {
                        try {
                            const client = new SignifyClient("http://localhost:3901", key)
                            let res = await client.get_identifiers()
                            return res
                        }
                        catch (e) {
                            console.log(e)
                            return 'Error getting identifiers'
                        }
                    }} />
            </div>
        </>
    )
}


