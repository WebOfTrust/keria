import { useState, useEffect, useRef } from 'react'
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import { SignifyClient, ready, Algos } from "signify-ts";
import { SignifyDemo } from './SignifyDemo';

const KERIA_URL = "http://localhost:3901"

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
    const [key, setKey] = useState(generateRandomKey())

    useEffect(() => {
        ready().then(() => {
            console.log("signify client is ready")
        })
    }, [])

    const inputRef = useRef(null)

    useEffect(() => {
        if (inputRef.current) {
            // inputRef.current.style.width = "auto"
            // inputRef.current.style.width = `${inputRef.current.scrollWidth}px`
        }
    }, [key])

    return (
        <>
            <div className="card">
                {/* show kel*/}
                <div className="form">
                    <label htmlFor="key">Enter 21 character passcode:</label>
                    <input type="text" id="key" value={key} onChange={(e) => setKey(e.target.value)} ref={inputRef} className="button" />
                </div>
                <p className='pre' >
                    Client AID is {pre}
                </p>
                {/* show kel*/}
                <SignifyDemo text={'Agent State'}
                    onClick={async () => {
                        const client = new SignifyClient(KERIA_URL, key)
                        setPre(client.controller.pre)
                        try {
                            await client.state()
                        }
                        catch (e) {
                            console.log(e)
                            await client.boot()
                        }
                        const res = await client.state()
                        const resp = JSON.stringify(res, null, 2)
                        return resp
                    }} />

                <SignifyDemo text={'Connect'}
                    onClick={async () => {
                            const client = new SignifyClient(KERIA_URL, key)
                            console.log('error connecting')
                            console.log('booting up')
                            await client.boot()
                            await client.connect()
                            console.log('booted and connected up')
                            setPre(client.controller.pre)
                            // const resp = await client.state()
                            // return JSON.stringify(resp, null, 2)
                        }
                    } />
                <SignifyDemo text={'Get identifiers'}
                    onClick={async () => {
                        try {
                            const client = new SignifyClient(KERIA_URL, key)
                            setPre(client.controller.pre)
                            try {
                                await client.connect()
                            }
                            catch (e) {
                                console.log('error connecting', e)
                                console.log('booting up')
                                await client.boot()
                                await client.connect()
                                console.log('booted and connected up')
                            }
                            const identifiers = client.identifiers()
                            const resp = await identifiers.list()
                            return JSON.stringify(resp, null, 2)
                        }
                        catch (e) {
                            console.log(e)
                            return 'Error getting identifiers'
                        }
                    }} />
                <SignifyDemo text={'Create salty identifier'}
                    onClick={async () => {
                        try {
                            const client = new SignifyClient(KERIA_URL, key)
                            setPre(client.controller.pre)
                            try {
                                await client.connect()
                            }
                            catch (e) {
                                console.log('error connecting', e)
                                console.log('booting up')
                                await client.boot()
                                await client.connect()
                                console.log('booted and connected up')
                            }
                            const identifiers = client.identifiers()
                            const resp = await identifiers.create('aid_' + generateRandomKey().slice(1, 3))
                            return JSON.stringify(resp, null, 2)
                        }
                        catch (e) {
                            console.log(e)
                            return 'Error creating identifiers'
                        }
                    }} />
                <SignifyDemo text={'Create randy identifier'}
                    onClick={async () => {
                        try {
                            const client = new SignifyClient(KERIA_URL, key)
                            setPre(client.controller.pre)
                            try {
                                await client.connect()
                            }
                            catch (e) {
                                console.log('error connecting', e)
                                console.log('booting up')
                                await client.boot()
                                await client.connect()
                                console.log('booted and connected up')
                            }
                            const identifiers = client.identifiers()
                            const resp = await identifiers.create('aid_' + generateRandomKey().slice(1, 3), {algo: Algos.randy})
                            return JSON.stringify(resp, null, 2)
                        }
                        catch (e) {
                            console.log(e)
                            return 'Error creating identifiers'
                        }
                    }} />
                <SignifyDemo text={'Rotate first identifier'}
                    onClick={async () => {
                        try {
                            const client = new SignifyClient(KERIA_URL, key)
                            setPre(client.controller.pre)
                            try {
                                await client.connect()
                            }
                            catch (e) {
                                console.log('error connecting', e)
                                console.log('booting up')
                                await client.boot()
                                await client.connect()
                                console.log('booted and connected up')
                            }
                            const identifiers = client.identifiers()
                            const aids = await identifiers.list()
                            const resp = await identifiers.rotate(aids[0]["name"], {})
                            return JSON.stringify(resp, null, 2)
                        }
                        catch (e) {
                            console.log(e)
                            return 'Error creating identifiers'
                        }
                    }} />
                <SignifyDemo text={'Get first identifier'}
                    onClick={async () => {
                        try {
                            const client = new SignifyClient(KERIA_URL, key)
                            setPre(client.controller.pre)
                            try {
                                await client.connect()
                            }
                            catch (e) {
                                console.log('error connecting', e)
                                console.log('booting up')
                                await client.boot()
                                await client.connect()
                                console.log('booted and connected up')
                            }
                            const identifiers = client.identifiers()
                            const aids = await identifiers.list()
                            const resp = await identifiers.get(aids[0]["name"])
                            return JSON.stringify(resp, null, 2)
                        }
                        catch (e) {
                            console.log(e)
                            return 'Error creating identifiers'
                        }
                    }} />
            </div>
        </>
    )
}


