import { useState, useEffect, useRef } from 'react'
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import { SignifyClient, ready } from "signify-ts";



export function SignifyDemo(keypassed: any) {
    const [key, setKey] = useState(keypassed.keypassed)
    const [response, setResponse] = useState("")

    useEffect(() => {
        ready().then(() => {
            console.log("signify client is ready")
        })
    }, [])

    const connectAgent = async () => {
        const client = new SignifyClient("http://localhost:3901", key)
        let res1 = await client.boot()
        let res = await client.connect()
        console.log(res)
        setResponse(JSON.stringify(res, null, 2))
        console.log(client)
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
                <button onClick={async () => {await connectAgent()}} className="button">
                    Agent conenct
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


