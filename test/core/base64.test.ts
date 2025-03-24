import { assert, test } from 'vitest';
import {
    decodeBase64Url,
    encodeBase64Url,
} from '../../src/keri/core/base64.ts';
import { Buffer } from 'buffer';

test('encode', () => {
    assert.equal(encodeBase64Url(Uint8Array.from(Buffer.from('f'))), 'Zg');
    assert.equal(encodeBase64Url(Uint8Array.from(Buffer.from('fi'))), 'Zmk');
    assert.equal(encodeBase64Url(Uint8Array.from(Buffer.from('fis'))), 'Zmlz');
    assert.equal(
        encodeBase64Url(Uint8Array.from(Buffer.from('fish'))),
        'ZmlzaA'
    );
    assert.equal(encodeBase64Url(Uint8Array.from([248])), '-A');
    assert.equal(encodeBase64Url(Uint8Array.from([252])), '_A');
});

test('decode', () => {
    assert.deepEqual(decodeBase64Url('Zg'), Uint8Array.from([102]));
    assert.deepEqual(decodeBase64Url('Zmk'), Uint8Array.from([102, 105]));
    assert.deepEqual(decodeBase64Url('Zmlz'), Uint8Array.from([102, 105, 115]));
    assert.deepEqual(
        decodeBase64Url('ZmlzaA'),
        Uint8Array.from([102, 105, 115, 104])
    );
    assert.deepEqual(Buffer.from([248]), decodeBase64Url('-A'));
    assert.deepEqual(Buffer.from([252]), decodeBase64Url('_A'));
});

test('Test encode / decode compare with built in node Buffer', () => {
    const text = '🏳️🏳️';
    const b64url = '8J-Ps--4j_Cfj7PvuI8';

    assert.deepEqual(
        Buffer.from(text).toString('base64url'),
        encodeBase64Url(Buffer.from(text))
    );

    assert.deepEqual(Buffer.from(b64url, 'base64url'), decodeBase64Url(b64url));
});
