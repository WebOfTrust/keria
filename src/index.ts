
import _sodium from 'libsodium-wrappers-sumo';
import load from 'blake3/browser-async'
export const ready = (async () => {
    await load('https://cdn.jsdelivr.net/npm/blake3@2.1.7/dist/wasm/web/blake3_js_bg.wasm')
    await _sodium.ready;
})

export * from './keri/core/salter'
export * from './keri/core/matter'
export * from './keri/core/serder'
export * from './keri/core/diger'
export * from './keri/app/habery'
export * from './keri/app/signify'

import { Buffer } from 'buffer';

// @ts-ignore
window.Buffer = Buffer;