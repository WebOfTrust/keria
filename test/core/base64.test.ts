import assert from 'node:assert';
import { decodeBase64Url, encodeBase64Url } from '../../src/keri/core/base64';

test('encode', () => {
    assert.equal(encodeBase64Url(Buffer.from('f')), 'Zg');
    assert.equal(encodeBase64Url(Buffer.from('fi')), 'Zmk');
    assert.equal(encodeBase64Url(Buffer.from('fis')), 'Zmlz');
    assert.equal(encodeBase64Url(Buffer.from('fish')), 'ZmlzaA');
    assert.equal(encodeBase64Url(Buffer.from([248])), '-A');
    assert.equal(encodeBase64Url(Buffer.from([252])), '_A');
});

test('decode', () => {
    assert.equal(decodeBase64Url('Zg').toString(), 'f');
    assert.equal(decodeBase64Url('Zmk').toString(), 'fi');
    assert.equal(decodeBase64Url('Zmlz').toString(), 'fis');
    assert.equal(decodeBase64Url('ZmlzaA').toString(), 'fish');
    assert.equal(Buffer.from([248]).buffer, decodeBase64Url('-A').buffer);
    assert.equal(Buffer.from([252]).buffer, decodeBase64Url('_A').buffer);
});

test('Test encode / decode compare with built in node Buffer', () => {
    const text = '🏳️🏳️';
    const b64url = '8J-Ps--4j_Cfj7PvuI8';

    assert.equal(
        Buffer.from(text).toString('base64url'),
        encodeBase64Url(Buffer.from(text))
    );

    assert.equal(
        Buffer.from(b64url, 'base64url').buffer,
        decodeBase64Url(b64url).buffer
    );
});
