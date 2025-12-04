import { assert, describe, it, test, expect } from 'vitest';
import { SignifyClient } from '../../src/keri/app/clienting.ts';
import { Identifier } from '../../src/keri/app/aiding.ts';
import {
    Operations,
    KeyEvents,
    KeyStates,
    Oobis,
} from '../../src/keri/app/coring.ts';
import { Contacts, Challenges } from '../../src/keri/app/contacting.ts';
import {
    Credentials,
    Schemas,
    Registries,
} from '../../src/keri/app/credentialing.ts';
import { Escrows } from '../../src/keri/app/escrowing.ts';
import { Exchanges } from '../../src/keri/app/exchanging.ts';
import { Groups } from '../../src/keri/app/grouping.ts';
import { Notifications } from '../../src/keri/app/notifying.ts';

import {
    HEADER_SIG_INPUT,
    HEADER_SIG_TIME,
} from '../../src/keri/core/httping.ts';
import { Tier } from '../../src/keri/core/salter.ts';
import libsodium from 'libsodium-wrappers-sumo';
import { createMockFetch } from './test-utils.ts';

const fetchMock = createMockFetch();

const url = 'http://127.0.0.1:3901';
const boot_url = 'http://127.0.0.1:3903';
const bran = '0123456789abcdefghijk';

describe('SignifyClient', () => {
    it('SignifyClient initialization', async () => {
        await libsodium.ready;

        const t = () => {
            new SignifyClient(url, 'short', Tier.low, boot_url);
        };
        expect(t).toThrow('bran must be 21 characters');

        const client = new SignifyClient(url, bran, Tier.low, boot_url);
        assert.equal(client.bran, '0123456789abcdefghijk');
        assert.equal(client.url, url);
        assert.equal(client.bootUrl, boot_url);
        assert.equal(client.tier, Tier.low);
        assert.equal(client.pidx, 0);
        assert.equal(
            client.controller.pre,
            'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose'
        );
        assert.equal(client.controller.stem, 'signify:controller');
        assert.equal(client.controller.tier, Tier.low);
        assert.equal(
            client.controller.serder.raw,
            '{"v":"KERI10JSON00012b_","t":"icp",' +
                '"d":"ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose",' +
                '"i":"ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose","s":"0",' +
                '"kt":"1","k":["DAbWjobbaLqRB94KiAutAHb_qzPpOHm3LURA_ksxetVc"],' +
                '"nt":"1","n":["EIFG_uqfr1yN560LoHYHfvPAhxQ5sN6xZZT_E3h7d2tL"],' +
                '"bt":"0","b":[],"c":[],"a":[]}'
        );
        assert.deepEqual(client.controller.serder.sad.s, '0');

        const res = await client.boot();
        assert.equal(fetchMock.mock.calls[0]![0]!, boot_url + '/boot');
        assert.equal(
            fetchMock.mock.calls[0]![1]!.body!.toString(),
            '{"icp":{"v":"KERI10JSON00012b_","t":"icp","d":"ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose","i":"ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose","s":"0","kt":"1","k":["DAbWjobbaLqRB94KiAutAHb_qzPpOHm3LURA_ksxetVc"],"nt":"1","n":["EIFG_uqfr1yN560LoHYHfvPAhxQ5sN6xZZT_E3h7d2tL"],"bt":"0","b":[],"c":[],"a":[]},"sig":"AACJwsJ0mvb4VgxD87H4jIsiT1QtlzznUy9zrX3lGdd48jjQRTv8FxlJ8ClDsGtkvK4Eekg5p-oPYiPvK_1eTXEG","stem":"signify:controller","pidx":1,"tier":"low"}'
        );
        assert.equal(res.status, 202);

        await client.connect();

        // validate agent
        assert(
            client.agent!.pre,
            'EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei'
        );
        assert(
            client.agent!.anchor,
            'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose'
        );
        assert(
            client.agent!.said,
            'EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei'
        );
        assert(client.agent!.state.s, '0');
        assert(
            client.agent!.state.d,
            'EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei'
        );

        // validate approve delegation
        assert.equal(client.controller.serder.sad.s, '1');
        assert.equal(client.controller.serder.sad.t, 'ixn');
        assert.equal(
            client.controller.serder.sad.a[0].i,
            'EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei'
        );
        assert.equal(
            client.controller.serder.sad.a[0].d,
            'EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei'
        );
        assert.equal(client.controller.serder.sad.a[0].s, '0');

        const data = client.data;
        assert(data[0], url);
        assert(data[0], bran);

        assert.equal(client.identifiers() instanceof Identifier, true);
        assert.equal(client.operations() instanceof Operations, true);
        assert.equal(client.keyEvents() instanceof KeyEvents, true);
        assert.equal(client.keyStates() instanceof KeyStates, true);
        assert.equal(client.keyStates() instanceof KeyStates, true);
        assert.equal(client.credentials() instanceof Credentials, true);
        assert.equal(client.registries() instanceof Registries, true);
        assert.equal(client.schemas() instanceof Schemas, true);
        assert.equal(client.challenges() instanceof Challenges, true);
        assert.equal(client.contacts() instanceof Contacts, true);
        assert.equal(client.notifications() instanceof Notifications, true);
        assert.equal(client.escrows() instanceof Escrows, true);
        assert.equal(client.oobis() instanceof Oobis, true);
        assert.equal(client.exchanges() instanceof Exchanges, true);
        assert.equal(client.groups() instanceof Groups, true);
    });

    it('Signed fetch', async () => {
        await libsodium.ready;
        await libsodium.ready;
        const bran = '0123456789abcdefghijk';
        const client = new SignifyClient(url, bran, Tier.low, boot_url);

        await client.connect();

        let resp = await client.fetch('/contacts', 'GET', undefined);
        assert.equal(resp.status, 202);
        let lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(lastCall[0]!, url + '/contacts');
        assert.equal(lastCall[1]!.method, 'GET');
        let lastHeaders = new Headers(lastCall[1]!.headers!);
        assert.equal(
            lastHeaders.get('signify-resource'),
            'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose'
        );

        // Headers in error
        let badAgentHeaders = {
            'signify-resource': 'bad_resource',
            [HEADER_SIG_TIME]: '2023-08-20T15:34:31.534673+00:00',
            [HEADER_SIG_INPUT]:
                'signify=("signify-resource" "@method" "@path" "signify-timestamp");created=1692545671;keyid="EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei";alg="ed25519"',
            signature:
                'indexed="?0";signify="0BDiSoxCv42h2BtGMHy_tpWAqyCgEoFwRa8bQy20mBB2D5Vik4gRp3XwkEHtqy6iy6SUYAytMUDtRbewotAfkCgN"',
            'content-type': 'application/json',
        };
        fetchMock.mockResolvedValueOnce(
            Response.json([], {
                status: 202,
                headers: badAgentHeaders,
            })
        );
        let t = async () => await client.fetch('/contacts', 'GET', undefined);
        await expect(t).rejects.toThrowError(
            'message from a different remote agent'
        );

        badAgentHeaders = {
            'signify-resource': 'EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei',
            'signify-timestamp': '2023-08-20T15:34:31.534673+00:00',
            [HEADER_SIG_INPUT]:
                'signify=("signify-resource" "@method" "@path" "signify-timestamp");created=1692545671;keyid="EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei";alg="ed25519"',
            signature:
                'indexed="?0";signify="0BDiSoxCv42h2BtGMHy_tpWAqyCgEoFwRa8bQy20mBB2D5Vik4gRp3XwkEHtqy6iy6SUYAytMUDtRbewotAfkCbad"',
            'content-type': 'application/json',
        };
        fetchMock.mockResolvedValueOnce(
            Response.json([], {
                status: 202,
                headers: badAgentHeaders,
            })
        );
        t = async () => await client.fetch('/contacts', 'GET', undefined);
        await expect(t).rejects.toThrowError(
            'Signature for EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei invalid.'
        );

        // Other calls
        resp = await client.saveOldPasscode('1234');
        assert.equal(resp.status, 202);
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(
            lastCall[0]!,
            url + '/salt/ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose'
        );
        assert.equal(lastCall[1]!.method, 'PUT');
        assert.equal(lastCall[1]!.body, '{"salt":"1234"}');

        resp = await client.deletePasscode();
        assert.equal(resp.status, 202);
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(
            lastCall[0]!,
            url + '/salt/ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose'
        );
        assert.equal(lastCall[1]!.method, 'DELETE');

        resp = await client.rotate('abcdefghijk0123456789', []);
        assert.equal(resp.status, 202);
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(
            lastCall[0]!,
            url + '/agent/ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose'
        );
        assert.equal(lastCall[1]!.method, 'PUT');
        let lastBody = JSON.parse(lastCall[1]!.body! as string);
        assert.equal(lastBody.rot.t, 'rot');
        assert.equal(lastBody.rot.s, '1');
        assert.deepEqual(lastBody.rot.kt, ['1', '0']);
        assert.equal(
            lastBody.rot.d,
            'EGFi9pCcRaLK8dPh5S7JP9Em62fBMiR1l4gW1ZazuuAO'
        );

        const heads = new Headers();
        heads.set('Content-Type', 'application/json');
        const treqInit = {
            headers: heads,
            method: 'POST',
            body: JSON.stringify({ foo: true }),
        };
        const turl = 'http://example.com/test';
        const treq = await client.createSignedRequest('aid1', turl, treqInit);
        assert.equal(treq.url, 'http://example.com/test');
        assert.equal(treq.method, 'POST');
        lastBody = await treq.json();
        assert.deepEqual(lastBody.foo, true);
        lastHeaders = new Headers(treq.headers);
        assert.equal(
            lastHeaders.get('signify-resource'),
            'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK'
        );
        assert.equal(
            lastHeaders
                .get(HEADER_SIG_INPUT)
                ?.startsWith(
                    'signify=("@method" "@path" "signify-resource" "signify-timestamp");created='
                ),
            true
        );
        assert.equal(
            lastHeaders
                .get(HEADER_SIG_INPUT)
                ?.endsWith(
                    ';keyid="DPmhSfdhCPxr3EqjxzEtF8TVy0YX7ATo0Uc8oo2cnmY9";alg="ed25519"'
                ),
            true
        );

        const aid = await client.identifiers().get('aid1');
        const keeper = client.manager!.get(aid);
        const signer = keeper.signers[0];
        const created = lastHeaders
            .get(HEADER_SIG_INPUT)
            ?.split(';created=')[1]
            .split(';keyid=')[0];
        const data = `"@method": POST\n"@path": /test\n"signify-resource": ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK\n"signify-timestamp": ${lastHeaders.get(
            HEADER_SIG_TIME
        )}\n"@signature-params: (@method @path signify-resource signify-timestamp);created=${created};keyid=DPmhSfdhCPxr3EqjxzEtF8TVy0YX7ATo0Uc8oo2cnmY9;alg=ed25519"`;

        if (data) {
            const raw = new TextEncoder().encode(data);
            const sig = signer.sign(raw);
            assert.equal(
                sig.qb64,
                lastHeaders
                    .get('signature')
                    ?.split('signify="')[1]
                    .split('"')[0]
            );
        } else {
            assert.fail(`${HEADER_SIG_INPUT} is empty`);
        }
    });

    test('includes HTTP status info in error message', async () => {
        await libsodium.ready;
        const bran = '0123456789abcdefghijk';
        const client = new SignifyClient(url, bran, Tier.low, boot_url);

        await client.connect();

        fetchMock.mockResolvedValue(
            new Response('Error info', {
                status: 400,
                statusText: 'Bad Request',
            })
        );

        const error = await client
            .fetch('/somepath', 'GET', undefined)
            .catch((e) => e);

        assert(error instanceof Error);
        assert.equal(
            error.message,
            'HTTP GET /somepath - 400 Bad Request - Error info'
        );
    });
});
