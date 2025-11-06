import { assert, describe, it } from 'vitest';
import { Tier } from '../../src/index.ts';
import libsodium from 'libsodium-wrappers-sumo';
import { SignifyClient } from '../../src/keri/app/clienting.ts';
import { createMockFetch } from './test-utils.ts';

const fetchMock = createMockFetch();

const url = 'http://127.0.0.1:3901';
const boot_url = 'http://127.0.0.1:3903';

describe('delegate', () => {
    it('approve delegation', async () => {
        await libsodium.ready;
        const bran = '0123456789abcdefghijk';
        const client = new SignifyClient(url, bran, Tier.low, boot_url);
        await client.boot();
        await client.connect();
        const delegations = client.delegations();
        await delegations.approve(
            'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao'
        );
        const lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(
            lastCall[0]!,
            url +
                '/identifiers/EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao/delegation'
        );
        assert.equal(lastCall[1]!.method, 'POST');
        const expectedBody = {
            ixn: {
                v: 'KERI10JSON0000cf_',
                t: 'ixn',
                d: 'EBPt7hivibUQN-dlRyE9x_Y5LgFCGJ8QoNLSJrIkBYIg',
                i: 'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK',
                s: '1',
                p: 'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK',
                a: [null],
            },
            sigs: [
                'AAC4StAw-0IiV_LujceAXB3tnkaK011rPYPBKLgz-u6jI7hwfWGTCu5LDvBUsON4CqXbZAwPgIv6JqYjIusWKv0G',
            ],
            salty: {
                sxlt: '1AAHnNQTkD0yxOC9tSz_ukbB2e-qhDTStH18uCsi5PCwOyXLONDR3MeKwWv_AVJKGKGi6xiBQH25_R1RXLS2OuK3TN3ovoUKH7-A',
                pidx: 0,
                kidx: 0,
                stem: 'signify:aid',
                tier: 'low',
                icodes: ['A'],
                ncodes: ['A'],
                dcode: 'E',
                transferable: true,
            },
        };
        assert.equal(
            lastCall[1]?.body?.toString(),
            JSON.stringify(expectedBody)
        );
    });
});
