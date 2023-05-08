
import _sodium from 'libsodium-wrappers-sumo';

export const ready = (async () => {
    await _sodium.ready;
})

export * from './keri/core/salter'
export * from './keri/core/matter'
export * from './keri/app/habery'
export * from './keri/app/signify'

import { Buffer } from 'buffer';

// @ts-ignore
window.Buffer = Buffer;