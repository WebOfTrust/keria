
import _sodium from 'libsodium-wrappers-sumo';

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


export * from './keri/core/salter'
export * from './keri/core/matter'
export * from './keri/core/serder'
export * from './keri/core/diger'
export * from './keri/app/habery'
export * from './keri/app/signify'
export * from './keri/app/apping';

import { Buffer } from 'buffer';

try {
    window.Buffer = Buffer;
} catch(e) {
}
