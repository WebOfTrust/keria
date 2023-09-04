
import _sodium from 'libsodium-wrappers-sumo';
import { create, all } from 'mathjs'

export const ready:() => Promise<void> =  (async() => {
    try {
        let b3 = await import('blake3/browser-async')
        // @ts-ignore
        await b3.default('https://cdn.jsdelivr.net/npm/blake3@2.1.7/dist/wasm/web/blake3_js_bg.wasm')
        await _sodium.ready;
    } catch(e) {
        await _sodium.ready;
    }
})

export * from './keri/app/habery'
export * from './keri/app/signify'
export * from './keri/app/apping'
export * from './keri/app/controller'
export * from './keri/app/habery'
export * from './keri/app/exchanging'
export * from './keri/app/signify'

export * from './keri/core/authing'
export * from './keri/core/cigar'
export * from './keri/core/cipher'
export * from './keri/core/core'
export * from './keri/core/counter'
export * from './keri/core/decrypter'
export * from './keri/core/diger'
export * from './keri/core/encrypter'
export * from './keri/core/eventing'
export * from './keri/core/httping'
export * from './keri/core/indexer'
export * from './keri/core/keeping'
export * from './keri/core/kering'
export * from './keri/core/manager'
export * from './keri/core/matter'
export * from './keri/core/number'
export * from './keri/core/prefixer'
export * from './keri/core/saider'
export * from './keri/core/salter'
export * from './keri/core/seqner'
export * from './keri/core/serder'
export * from './keri/core/siger'
export * from './keri/core/signer'
export * from './keri/core/tholder'
export * from './keri/core/utils'
export * from './keri/core/verfer'

export * from './keri/end/ending'



export { Algos } from './keri/core/manager';

import { Buffer } from 'buffer';

try {
    window.Buffer = Buffer;
} catch(e) {
}

const config = { }
export const math = create(all, config)
