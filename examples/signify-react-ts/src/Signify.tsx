import { useState, useEffect, useRef } from 'react'
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import { SignifyClient, ready } from "signify-ts";
import {SignifyDemo } from './SignifyDemo';

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

    const handleComputePre = async () => {
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
        setPre(client.controller?.pre)
        console.log("here")
        let res  = await client.boot()
        console.log(res)
    }
    const getAgentState = async () => {
        const client = new SignifyClient("http://localhost:3901", key)
        let res = await client.state()
        console.log(res)
        setResponse(JSON.stringify(res, null, 2))
        console.log(client)
    }



    const handleButtonClick = () => {
        if (!pre) {
            alert("Please compute pre first.")
            return
        }
        setICP(JSON.stringify(client.controller?.event[0]))
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
                <SignifyDemo keypassed={key} />
                {/* show kel*/}
                <div className="form">
                    <label htmlFor="key">Enter 21 character passcode:</label>
                    <input type="text" id="key" value={key} onChange={(e) => setKey(e.target.value)} ref={inputRef} className="button" />
                    <button 
                    onClick={async () => {await handleComputePre()}}
                    className="button"
                    >Boot Keria </button>
                </div>
                <p >
                    AID is {pre}
                </p>
                <button onClick={async () => {await connectAgent()}} className="button">
                    Agent conenct
                </button>
                {/* show kel*/}
                <button onClick={async () => {await getAgentState()}} className="button">
                    Agent Kel State
                </button>
                <div
                    style={{
                            whiteSpace: "pre-wrap",
                            wordWrap: "break-word",
                            width: "100%",
                            height: "auto",
                            textAlign: "left",
                            padding: "1rem",
                            backgroundColor: "#eee",
                            borderRadius: "0.5rem",
                            marginTop: "1rem",
                            border: "1px solid black"
                    }}
                    >
                    {response}
                </div>
            </div>
        </>
    )
}


