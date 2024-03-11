import { Buffer } from 'buffer';
// base64url is supported by node Buffer, but not in buffer package for browser compatibility
// https://github.com/feross/buffer/issues/309

// Instead of using a node.js-only module and forcing us to polyfill the Buffer global,
// we insert code from https://gitlab.com/seangenabe/safe-base64 here

export function encodeBase64Url(buffer: Buffer) {
    if (!Buffer.isBuffer(buffer)) {
        throw new TypeError('`buffer` must be a buffer.');
    }
    return buffer
        .toString('base64')
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=+/, '');
}

export function decodeBase64Url(input: string) {
    if (!(typeof input === 'string')) {
        throw new TypeError('`input` must be a string.');
    }

    const n = input.length % 4;
    const padded = input + '='.repeat(n > 0 ? 4 - n : n);
    const base64String = padded.replace(/-/g, '+').replace(/_/g, '/');
    return Buffer.from(base64String, 'base64');
}
