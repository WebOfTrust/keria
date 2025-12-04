import { assert, test } from 'vitest';
import {
    decodeBase64Url,
    encodeBase64Url,
} from '../../src/keri/core/base64.ts';

test('encode', () => {
    assert.equal(encodeBase64Url(Uint8Array.from([102])), 'Zg');
    assert.equal(encodeBase64Url(Uint8Array.from([102, 105])), 'Zmk');
    assert.equal(encodeBase64Url(Uint8Array.from([102, 105, 115])), 'Zmlz');
    assert.equal(
        encodeBase64Url(Uint8Array.from([102, 105, 115, 104])),
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
    assert.deepEqual(Uint8Array.from([248]), decodeBase64Url('-A'));
    assert.deepEqual(Uint8Array.from([252]), decodeBase64Url('_A'));
});

test('Test encode / decode compare with built in node Buffer', () => {
    const text = '🏳️🏳️';
    const b64url = '8J-Ps--4j_Cfj7PvuI8';
    const data = Uint8Array.from([
        240, 159, 143, 179, 239, 184, 143, 240, 159, 143, 179, 239, 184, 143,
    ]);

    assert.deepEqual(b64url, encodeBase64Url(new TextEncoder().encode(text)));
    assert.deepEqual(data, decodeBase64Url(b64url));
});
