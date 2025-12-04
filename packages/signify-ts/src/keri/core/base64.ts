import { fromByteArray, toByteArray } from 'base64-js';

export function encodeBase64Url(input: Uint8Array): string {
    return fromByteArray(input)
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=+/, '');
}

export function decodeBase64Url(input: string): Uint8Array {
    if (!(typeof input === 'string')) {
        throw new TypeError('`input` must be a string.');
    }

    const n = input.length % 4;
    const padded = input + '='.repeat(n > 0 ? 4 - n : n);
    const base64String = padded.replace(/-/g, '+').replace(/_/g, '/');
    return toByteArray(base64String);
}
