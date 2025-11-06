import { assert, describe, it } from 'vitest';
import { SignifyClient } from '../../src/keri/app/clienting.ts';
import { Tier } from '../../src/keri/core/salter.ts';
import libsodium from 'libsodium-wrappers-sumo';
import { createMockFetch } from './test-utils.ts';

const fetchMock = createMockFetch();

const url = 'http://127.0.0.1:3901';
const boot_url = 'http://127.0.0.1:3903';

describe('SignifyClient', () => {
    it('Escrows', async () => {
        await libsodium.ready;
        const bran = '0123456789abcdefghijk';

        const client = new SignifyClient(url, bran, Tier.low, boot_url);

        await client.boot();
        await client.connect();

        const escrows = client.escrows();

        let lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        await escrows.listReply('/presentation/request');
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(
            lastCall[0]!,
            url + '/escrows/rpy?route=%2Fpresentation%2Frequest'
        );
        assert.equal(lastCall[1]!.method, 'GET');
    });
});
