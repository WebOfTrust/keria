import { useState, useEffect, useRef } from 'react'
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import { SignifyClient, ready, Serder } from "signify-ts";
import { SignifyDemo } from './SignifyDemo';
import {strict as assert} from "assert";


function generateRandomKey() {
    const characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
    const length = 21;
    let result = "";
    for (let i = 0; i < length; i++) {
        result += characters.charAt(Math.floor(Math.random() * characters.length));
    }
    return result;
}

export function TestsComponent() {
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
                <SignifyDemo text={'Salty Integration Test'}
                    onClick={async () => {
                        try {
                            const url = "http://localhost:3901"
                            const bran = '0123456789abcdefghijk'
                            // const tier = Tiers.med
                            const client = new SignifyClient(url, bran)
                            assert.equal(client.controller.pre, 'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose')
                            const r1 = await client.boot()
                            assert.equal(r1.status, 202)
                            await client.connect()
                            assert.notEqual(client.agent, undefined)
                            assert.equal(client.agent?.pre, 'EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei')
                            assert.equal(client.agent?.anchor, 'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose')
                            const identifiers = client.identifiers()
                            const aids = await identifiers.list_identifiers()
                            assert.equal(aids.length, 0)
                            const aid1 = await identifiers.create('aid1', {bran: '0123456789abcdefghijk'})
                            const icp = await new Serder(aid1)
                            assert.equal(icp.pre, 'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK')
                            assert.equal(icp.verfers.length, 1)
                            // catch (e) {
                            //     console.log('error connecting', e)
                            //     console.log('booting up')
                            //     await client.boot()
                            //     await client.connect()
                            //     console.log('booted and connected up')
                            // }
                            // const identifiers = client.identifiers()
                            // const resp = await identifiers.create('aid_' + generateRandomKey().slice(1, 3), {})
                            return "Salty Integration Test Passed"
                        }
                        catch (e) {
                            console.log(e)
                            return 'Salt Integration Test Failed'
                        }
                    }} />
            </div>
        </>
    )
}


