import {useState} from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import {SignifyClient, ready} from "signify-ts";

function App() {
    const [pre, setPre] = useState("")
    const [icp, setICP] = useState("")

    let data = ""
    ready().then(() => {
        const client = new SignifyClient("http://localhost:3902", "0123456789abcdefghijk")
        console.log("we have a signify client", client.controller?.pre)
        setPre(client.controller?.pre)
        data = client.controller?.event
    })

    return (
        <>
            <div>
                <a href="https://vitejs.dev" target="_blank">
                    <img src={viteLogo} className="logo" alt="Vite logo"/>
                </a>
                <a href="https://react.dev" target="_blank">
                    <img src={reactLogo} className="logo react" alt="React logo"/>
                </a>
            </div>
            <h1>Vite + React + Signify</h1>
            <div className="card">
                <button onClick={() => setICP(JSON.stringify(data[0]))}>
                    AID is {pre}
                </button>
                <p>
                    {icp}
                </p>
            </div>
            <p className="read-the-docs">
                Click on the Vite and React logos to learn more
            </p>
        </>
    )
}

export default App
