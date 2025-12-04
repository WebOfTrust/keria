import { assert, describe, it } from 'vitest';
import { SignifyClient } from '../../src/keri/app/clienting.ts';
import { Tier } from '../../src/keri/core/salter.ts';
import libsodium from 'libsodium-wrappers-sumo';
import { createMockFetch } from './test-utils.ts';

const fetchMock = createMockFetch();

const url = 'http://127.0.0.1:3901';
const boot_url = 'http://127.0.0.1:3903';

describe('Contacting', () => {
    it('Contacts', async () => {
        await libsodium.ready;
        const bran = '0123456789abcdefghijk';

        const client = new SignifyClient(url, bran, Tier.low, boot_url);

        await client.boot();
        await client.connect();

        const contacts = client.contacts();

        await contacts.list('mygroup', 'company', 'mycompany');
        let lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(
            lastCall[0]!,
            url +
                '/contacts?group=mygroup&filter_field=company&filter_value=mycompany'
        );
        assert.equal(lastCall[1]!.method, 'GET');

        await contacts.get('EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao');
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(
            lastCall[0]!,
            url + '/contacts/EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao'
        );
        assert.equal(lastCall[1]!.method, 'GET');

        const info = {
            name: 'John Doe',
            company: 'My Company',
        };
        await contacts.add(
            'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao',
            info
        );
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        let lastBody = JSON.parse(lastCall[1]!.body!.toString());
        assert.equal(
            lastCall[0]!,
            url + '/contacts/EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao'
        );
        assert.equal(lastCall[1]!.method, 'POST');
        assert.deepEqual(lastBody, info);

        await contacts.update(
            'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao',
            info
        );
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        lastBody = JSON.parse(lastCall[1]!.body!.toString());
        assert.equal(
            lastCall[0]!,
            url + '/contacts/EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao'
        );
        assert.equal(lastCall[1]!.method, 'PUT');
        assert.deepEqual(lastBody, info);

        await contacts.delete('EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao');
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(
            lastCall[0]!,
            url + '/contacts/EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao'
        );
        assert.equal(lastCall[1]!.method, 'DELETE');
        assert.equal(lastCall[1]!.body, undefined);
    });

    it('Challenges', async () => {
        await libsodium.ready;
        const bran = '0123456789abcdefghijk';

        const client = new SignifyClient(url, bran, Tier.low, boot_url);

        await client.boot();
        await client.connect();

        const challenges = client.challenges();

        await challenges.generate(128);
        let lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(lastCall[0]!, url + '/challenges?strength=128');
        assert.equal(lastCall[1]!.method, 'GET');

        const words = [
            'shell',
            'gloom',
            'mimic',
            'cereal',
            'stool',
            'furnace',
            'nominee',
            'nation',
            'sauce',
            'sausage',
            'rather',
            'venue',
        ];
        await challenges.respond(
            'aid1',
            'EG2XjQN-3jPN5rcR4spLjaJyM4zA6Lgg-Hd5vSMymu5p',
            words
        );
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(lastCall[0]!, url + '/identifiers/aid1/exchanges');
        assert.equal(lastCall[1]!.method, 'POST');
        let lastBody = JSON.parse(lastCall[1]!.body!.toString());
        assert.equal(lastBody.tpc, 'challenge');
        assert.equal(lastBody.exn.r, '/challenge/response');
        assert.equal(
            lastBody.exn.i,
            'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK'
        );
        assert.deepEqual(lastBody.exn.a.words, words);
        assert.equal(lastBody.sigs[0].length, 88);

        await challenges.verify(
            'EG2XjQN-3jPN5rcR4spLjaJyM4zA6Lgg-Hd5vSMymu5p',
            words
        );
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(
            lastCall[0]!,
            url +
                '/challenges_verify/EG2XjQN-3jPN5rcR4spLjaJyM4zA6Lgg-Hd5vSMymu5p'
        );
        assert.equal(lastCall[1]!.method, 'POST');
        lastBody = JSON.parse(lastCall[1]!.body!.toString());
        assert.deepEqual(lastBody.words, words);

        await challenges.responded(
            'EG2XjQN-3jPN5rcR4spLjaJyM4zA6Lgg-Hd5vSMymu5p',
            'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao'
        );
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(
            lastCall[0]!,
            url +
                '/challenges_verify/EG2XjQN-3jPN5rcR4spLjaJyM4zA6Lgg-Hd5vSMymu5p'
        );
        assert.equal(lastCall[1]!.method, 'PUT');
        lastBody = JSON.parse(lastCall[1]!.body!.toString());
        assert.equal(
            lastBody.said,
            'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao'
        );
    });
});
