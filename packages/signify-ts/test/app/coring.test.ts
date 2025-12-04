import { assert, describe, it, beforeEach, vitest } from 'vitest';
import libsodium from 'libsodium-wrappers-sumo';
import {
    randomPasscode,
    randomNonce,
    Operations,
    OperationsDeps,
} from '../../src/keri/app/coring.ts';
import { SignifyClient } from '../../src/keri/app/clienting.ts';
import { Tier } from '../../src/keri/core/salter.ts';
import { randomUUID } from 'node:crypto';
import { createMockFetch } from './test-utils.ts';

const url = 'http://127.0.0.1:3901';
const boot_url = 'http://127.0.0.1:3903';
const fetchMock = createMockFetch();

describe('Coring', () => {
    it('Random passcode', async () => {
        await libsodium.ready;
        const passcode = randomPasscode();
        assert.equal(passcode.length, 21);
    });

    it('Random nonce', async () => {
        await libsodium.ready;
        const nonce = randomNonce();
        assert.equal(nonce.length, 44);
    });

    it('OOBIs', async () => {
        await libsodium.ready;
        const bran = '0123456789abcdefghijk';

        const client = new SignifyClient(url, bran, Tier.low, boot_url);

        await client.boot();
        await client.connect();

        const oobis = client.oobis();

        await oobis.get('aid', 'agent');
        let lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(lastCall[0]!, url + '/identifiers/aid/oobis?role=agent');
        assert.equal(lastCall[1]!.method, 'GET');

        await oobis.resolve('http://oobiurl.com');
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        let lastBody = JSON.parse(lastCall[1]!.body!.toString());
        assert.equal(lastCall[0]!, url + '/oobis');
        assert.equal(lastCall[1]!.method, 'POST');
        assert.deepEqual(lastBody.url, 'http://oobiurl.com');

        await oobis.resolve('http://oobiurl.com', 'witness');
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        lastBody = JSON.parse(lastCall[1]!.body!.toString());
        assert.equal(lastCall[0]!, url + '/oobis');
        assert.equal(lastCall[1]!.method, 'POST');
        assert.deepEqual(lastBody.url, 'http://oobiurl.com');
        assert.deepEqual(lastBody.oobialias, 'witness');
    });

    it('Events and states', async () => {
        await libsodium.ready;
        const bran = '0123456789abcdefghijk';

        const client = new SignifyClient(url, bran, Tier.low, boot_url);

        await client.boot();
        await client.connect();

        const keyEvents = client.keyEvents();
        const keyStates = client.keyStates();

        await keyEvents.get('EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX');
        let lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(
            lastCall[0]!,
            url + '/events?pre=EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX'
        );
        assert.equal(lastCall[1]!.method, 'GET');

        await keyStates.get('EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX');
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(
            lastCall[0]!,
            url + '/states?pre=EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX'
        );
        assert.equal(lastCall[1]!.method, 'GET');

        await keyStates.list([
            'EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX',
            'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK',
        ]);
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(
            lastCall[0]!,
            url +
                '/states?pre=EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX&pre=ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK'
        );
        assert.equal(lastCall[1]!.method, 'GET');

        await keyStates.query(
            'EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX',
            '1',
            'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao'
        );
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        const lastBody = JSON.parse(lastCall[1]!.body!.toString());
        assert.equal(lastCall[0]!, url + '/queries');
        assert.equal(lastCall[1]!.method, 'POST');
        assert.equal(
            lastBody.pre,
            'EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX'
        );
        assert.equal(lastBody.sn, '1');
        assert.equal(
            lastBody.anchor,
            'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao'
        );
    });

    it('Agent configuration', async () => {
        await libsodium.ready;
        const bran = '0123456789abcdefghijk';

        const client = new SignifyClient(url, bran, Tier.low, boot_url);

        await client.boot();
        await client.connect();

        const config = client.config();

        await config.get();
        const lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(lastCall[0]!, url + '/config');
        assert.equal(lastCall[1]!.method, 'GET');
    });
});

describe('Operations', () => {
    class MockClient implements OperationsDeps {
        fetch = vitest.fn();

        constructor() {}

        operations() {
            return new Operations(this);
        }

        getLastMockRequest() {
            const [pathname, method, body] = this.fetch.mock.lastCall ?? [];

            return {
                path: pathname,
                method: method,
                body: body,
            };
        }
    }

    let client: MockClient;
    beforeEach(async () => {
        await libsodium.ready;
        client = new MockClient();
    });

    it('Can get operation by name', async () => {
        await libsodium.ready;

        client.fetch.mockResolvedValue(
            new Response(JSON.stringify({ name: randomUUID() }), {
                status: 200,
            })
        );
        await client.operations().get('operationName');
        const lastCall = client.getLastMockRequest();
        assert.equal(lastCall.path, '/operations/operationName');
        assert.equal(lastCall.method, 'GET');
    });

    it('Can list operations', async () => {
        client.fetch.mockResolvedValue(
            new Response(JSON.stringify([]), {
                status: 200,
            })
        );
        await client.operations().list();
        const lastCall = client.getLastMockRequest();
        assert.equal(lastCall.path, '/operations?');
        assert.equal(lastCall.method, 'GET');
    });

    it('Can list operations by type', async () => {
        client.fetch.mockResolvedValue(
            new Response(JSON.stringify([]), {
                status: 200,
            })
        );
        await client.operations().list('witness');
        const lastCall = client.getLastMockRequest();
        assert.equal(lastCall.path, '/operations?type=witness');
        assert.equal(lastCall.method, 'GET');
    });

    it('Can delete operation by name', async () => {
        client.fetch.mockResolvedValue(
            new Response(JSON.stringify({}), {
                status: 200,
            })
        );
        await client.operations().delete('operationName');
        const lastCall = client.getLastMockRequest();
        assert.equal(lastCall.path, '/operations/operationName');
        assert.equal(lastCall.method, 'DELETE');
    });

    describe('wait', () => {
        it('does not wait for operation that is already "done"', async () => {
            const name = randomUUID();
            client.fetch.mockResolvedValue(
                new Response(JSON.stringify({ name }), {
                    status: 200,
                })
            );

            const op = { name, done: true };
            const result = await client.operations().wait(op);
            assert.equal(client.fetch.mock.calls.length, 0);
            assert.equal<unknown>(op, result);
        });

        it('returns when operation is done after first call', async () => {
            const name = randomUUID();
            client.fetch.mockResolvedValue(
                new Response(JSON.stringify({ name, done: true }), {
                    status: 200,
                })
            );

            const op = { name, done: false };
            await client.operations().wait(op);
            assert.equal(client.fetch.mock.calls.length, 1);
        });

        it('returns when operation is done after second call', async () => {
            const name = randomUUID();
            client.fetch.mockResolvedValueOnce(
                new Response(JSON.stringify({ name, done: false }), {
                    status: 200,
                })
            );

            client.fetch.mockResolvedValueOnce(
                new Response(JSON.stringify({ name, done: true }), {
                    status: 200,
                })
            );

            const op = { name, done: false };
            await client.operations().wait(op, { maxSleep: 10 });
            assert.equal(client.fetch.mock.calls.length, 2);
        });

        it('throw if aborted', async () => {
            const name = randomUUID();
            client.fetch.mockImplementation(
                async () =>
                    new Response(JSON.stringify({ name, done: false }), {
                        status: 200,
                    })
            );

            const op = { name, done: false };

            const controller = new AbortController();
            const promise = client
                .operations()
                .wait(op, { signal: controller.signal })
                .catch((e) => e);

            const abortError = new Error('Aborted');
            controller.abort(abortError);

            const error = await promise;

            assert.equal(error, abortError);
        });

        it('returns when child operation is also done', async () => {
            const name = randomUUID();
            const nestedName = randomUUID();
            const depends = { name: nestedName, done: false };
            const op = { name, done: false, depends };

            client.fetch.mockResolvedValueOnce(
                new Response(JSON.stringify({ ...op, done: false }), {
                    status: 200,
                })
            );

            client.fetch.mockResolvedValueOnce(
                new Response(
                    JSON.stringify({
                        ...op,
                        depends: { ...depends, done: true },
                    }),
                    {
                        status: 200,
                    }
                )
            );

            client.fetch.mockResolvedValueOnce(
                new Response(
                    JSON.stringify({
                        ...op,
                        done: true,
                        depends: { ...depends, done: true },
                    }),
                    {
                        status: 200,
                    }
                )
            );

            await client.operations().wait(op, { maxSleep: 10 });
            assert.equal(client.fetch.mock.calls.length, 3);
        });
    });
});
