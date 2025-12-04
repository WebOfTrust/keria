import { assert, describe, it } from 'vitest';
import {
    b,
    d,
    Diger,
    exchange,
    Ilks,
    MtrDex,
    Salter,
    Serder,
    Tier,
} from '../../src/index.ts';
import libsodium from 'libsodium-wrappers-sumo';
import { SignifyClient } from '../../src/keri/app/clienting.ts';
import { createMockFetch } from './test-utils.ts';

const fetchMock = createMockFetch();

const url = 'http://127.0.0.1:3901';
const boot_url = 'http://127.0.0.1:3903';

describe('exchange', () => {
    it('should create an exchange message with no transposed attachments', async () => {
        await libsodium.ready;
        const dt = '2023-08-30T17:22:54.183Z';

        let [exn, end] = exchange('/multisig/vcp', {}, 'test', '', dt);
        assert.deepStrictEqual(exn.sad, {
            a: {
                i: '',
            },
            d: 'EPWm8LWxxQXmXlB8gbTZKDy7NIwXxpx49N_ZYTa5QkJV',
            dt: '2023-08-30T17:22:54.183Z',
            e: {},
            i: 'test',
            p: '',
            q: {},
            r: '/multisig/vcp',
            rp: '',
            t: 'exn',
            v: 'KERI10JSON0000bf_',
        });
        assert.deepStrictEqual(end, new Uint8Array());

        const sith = 1;
        const nsith = 1;
        const sn = 0;
        const toad = 0;

        const raw = new Uint8Array([
            5, 170, 143, 45, 83, 154, 233, 250, 85, 156, 2, 156, 155, 8, 72,
            117,
        ]);
        const salter = new Salter({ raw: raw });
        const skp0 = salter.signer(
            MtrDex.Ed25519_Seed,
            true,
            'A',
            Tier.low,
            true
        );
        const keys = [skp0.verfer.qb64];

        const skp1 = salter.signer(
            MtrDex.Ed25519_Seed,
            true,
            'N',
            Tier.low,
            true
        );
        const ndiger = new Diger({}, skp1.verfer.qb64b);
        const nxt = [ndiger.qb64];
        assert.deepStrictEqual(nxt, [
            'EAKUR-LmLHWMwXTLWQ1QjxHrihBmwwrV2tYaSG7hOrWj',
        ]);

        const ked0 = {
            v: 'KERI10JSON000000_',
            t: Ilks.icp,
            d: '',
            i: '',
            s: sn.toString(16),
            kt: sith.toString(16),
            k: keys,
            nt: nsith.toString(16),
            n: nxt,
            bt: toad.toString(16),
            b: [],
            c: [],
            a: [],
        };

        const serder = new Serder(ked0);
        const siger = skp0.sign(b(serder.raw), 0);
        assert.equal(
            siger.qb64,
            'AAAPkMTS3LrrhVuQB0k4UndDN0xIfEiKYaN7rTlQ_q9ImnBcugwNO8VWTALXzWoaldJEC1IOpEGkEnjZfxxIleoI'
        );

        const ked1 = {
            v: 'KERI10JSON000000_',
            t: Ilks.vcp,
            d: '',
            i: '',
            s: '0',
            bt: toad.toString(16),
            b: [],
        };
        const vcp = new Serder(ked1);

        const embeds = {
            icp: [serder, siger.qb64],
            vcp: [vcp, undefined],
        };

        [exn, end] = exchange(
            '/multisig/vcp',
            {},
            'test',
            '',
            dt,
            undefined,
            undefined,
            embeds
        );

        assert.deepStrictEqual(exn.sad, {
            a: {
                i: '',
            },
            d: 'EOK2xNjB5xlSvizCUrkFKbdF4j1nsGpvt6TR1HL0wvaY',
            dt: '2023-08-30T17:22:54.183Z',
            e: {
                d: 'EDPWpKtMoPwro_Of8TQzpNMGdtmfyWzqTcRKQ01fGFRi',
                icp: {
                    a: [],
                    b: [],
                    bt: '0',
                    c: [],
                    d: '',
                    i: '',
                    k: ['DAUDqkmn-hqlQKD8W-FAEa5JUvJC2I9yarEem-AAEg3e'],
                    kt: '1',
                    n: ['EAKUR-LmLHWMwXTLWQ1QjxHrihBmwwrV2tYaSG7hOrWj'],
                    nt: '1',
                    s: '0',
                    t: 'icp',
                    v: 'KERI10JSON0000d3_',
                },
                vcp: {
                    b: [],
                    bt: '0',
                    d: '',
                    i: '',
                    s: '0',
                    t: 'vcp',
                    v: 'KERI10JSON000049_',
                },
            },
            i: 'test',
            p: '',
            q: {},
            r: '/multisig/vcp',
            rp: '',
            t: 'exn',
            v: 'KERI10JSON00021b_',
        });
        assert.equal(
            d(end),
            '-LAZ5AACAA-e-icpAAAPkMTS3LrrhVuQB0k4UndDN0xIfEiKYaN7rTlQ_q9ImnBcugwNO8VWTALXzWoaldJEC1IOpEGkEnjZfxxIleoI'
        );
    });

    it('SendFromEvents', async () => {
        await libsodium.ready;
        const bran = '0123456789abcdefghijk';

        const client = new SignifyClient(url, bran, Tier.low, boot_url);

        await client.boot();
        await client.connect();

        const exchange = client.exchanges();
        const sith = 1;
        const nsith = 1;
        const sn = 0;
        const toad = 0;

        const raw = new Uint8Array([
            5, 170, 143, 45, 83, 154, 233, 250, 85, 156, 2, 156, 155, 8, 72,
            117,
        ]);
        const salter = new Salter({ raw: raw });
        const skp0 = salter.signer(
            MtrDex.Ed25519_Seed,
            true,
            'A',
            Tier.low,
            true
        );
        const keys = [skp0.verfer.qb64];

        const skp1 = salter.signer(
            MtrDex.Ed25519_Seed,
            true,
            'N',
            Tier.low,
            true
        );
        const ndiger = new Diger({}, skp1.verfer.qb64b);
        const nxt = [ndiger.qb64];
        assert.deepStrictEqual(nxt, [
            'EAKUR-LmLHWMwXTLWQ1QjxHrihBmwwrV2tYaSG7hOrWj',
        ]);

        const ked0 = {
            v: 'KERI10JSON000000_',
            t: Ilks.icp,
            d: '',
            i: '',
            s: sn.toString(16),
            kt: sith.toString(16),
            k: keys,
            nt: nsith.toString(16),
            n: nxt,
            bt: toad.toString(16),
            b: [],
            c: [],
            a: [],
        };

        const serder = new Serder(ked0);

        let lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        await exchange.sendFromEvents('aid1', '', serder, [''], '', []);
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(lastCall[0]!, url + '/identifiers/aid1/exchanges');
        assert.equal(lastCall[1]!.method, 'POST');
    });

    it('Get exchange', async () => {
        await libsodium.ready;
        const bran = '0123456789abcdefghijk';
        const client = new SignifyClient(url, bran, Tier.low, boot_url);
        await client.boot();
        await client.connect();
        const exchanges = client.exchanges();
        await exchanges.get('EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao');
        const lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(
            lastCall[0]!,
            url + '/exchanges/EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao'
        );
        assert.equal(lastCall[1]!.method, 'GET');
    });
});
