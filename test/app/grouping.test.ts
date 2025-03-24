import { assert, describe, it } from 'vitest';
import { SignifyClient } from '../../src/keri/app/clienting.ts';
import { Tier } from '../../src/keri/core/salter.ts';
import libsodium from 'libsodium-wrappers-sumo';
import { createMockFetch } from './test-utils.ts';

const fetchMock = createMockFetch();

const url = 'http://127.0.0.1:3901';
const boot_url = 'http://127.0.0.1:3903';

describe('Grouping', () => {
    it('Groups', async () => {
        await libsodium.ready;
        const bran = '0123456789abcdefghijk';

        const client = new SignifyClient(url, bran, Tier.low, boot_url);

        await client.boot();
        await client.connect();

        const groups = client.groups();
        let lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        await groups.sendRequest('aid1', {}, [], '');
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(lastCall[0]!, url + '/identifiers/aid1/multisig/request');
        assert.equal(lastCall[1]!.method, 'POST');

        await groups.getRequest(
            'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose00'
        );
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(
            lastCall[0]!,
            url +
                '/multisig/request/ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose00'
        );
        assert.equal(lastCall[1]!.method, 'GET');

        await groups.join(
            'aid1',
            { sad: {} },
            ['sig'],
            'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose00',
            ['1', '2', '3'],
            ['a', 'b', 'c']
        );
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(lastCall[0]!, url + '/identifiers/aid1/multisig/join');
        assert.equal(lastCall[1]!.method, 'POST');
    });
});
