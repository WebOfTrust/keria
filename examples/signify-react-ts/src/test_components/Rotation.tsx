// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import { SignifyClient, ready, Serder, Diger, MtrDex } from "signify-ts";
import {strict as assert} from "assert";
import { useState, useEffect } from 'react';


export function Rotation() {
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
                            const url = "http://localhost:3901"
                            const _bran = '0123456789abcdefghijk'
                            const client = new SignifyClient(url, _bran)
                            assert.equal(client.controller.pre, 'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose')
                            const r1 = await client.boot()
                            assert.equal(r1.status, 202)
                            await client.connect()
                            assert.notEqual(client.agent, undefined)
                            assert.equal(client.agent?.pre, 'EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei')
                            assert.equal(client.agent?.anchor, 'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose')
                            const identifiers = client.identifiers()

                            let op_rand = await identifiers.create('aid1', {algo: 'randy'})
                            assert.equal(op_rand['done'], true)

                            let op_salt = await identifiers.create('aid2', {})
                            assert.equal(op_salt['done'], true)


                            let pres = await identifiers.list()
                            let aids = []
                            for (let pre of pres) {
                                let _aid = await identifiers.get(pre.name)
                                aids.push(_aid)
                            }
                            client.rotate('1111123456789abcdefghijk', aids)

                            setTestResult("Passed")
                      
                    }} >Rotation Integration Test</button>{testResult}
            </div>
        </>
    )
}


