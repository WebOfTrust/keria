import { strict as assert } from 'assert';
import { SignifyClient } from '../../src/keri/app/clienting';

import { Authenticater } from '../../src/keri/core/authing';
import { Salter, Tier } from '../../src/keri/core/salter';
import libsodium from 'libsodium-wrappers-sumo';
import fetchMock from 'jest-fetch-mock';
import 'whatwg-fetch';
import {
    d,
    Ident,
    Ilks,
    interact,
    Saider,
    Serder,
    serializeACDCAttachment,
    serializeIssExnAttachment,
    Serials,
    versify,
} from '../../src';

fetchMock.enableMocks();

const url = 'http://127.0.0.1:3901';
const boot_url = 'http://127.0.0.1:3903';

const mockConnect = {
    agent: {
        vn: [1, 0],
        i: 'EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei',
        s: '0',
        p: '',
        d: 'EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei',
        f: '0',
        dt: '2023-08-19T21:04:57.948863+00:00',
        et: 'dip',
        kt: '1',
        k: ['DMZh_y-H5C3cSbZZST-fqnsmdNTReZxIh0t2xSTOJQ8a'],
        nt: '1',
        n: ['EM9M2EQNCBK0MyAhVYBvR98Q0tefpvHgE-lHLs82XgqC'],
        bt: '0',
        b: [],
        c: [],
        ee: {
            s: '0',
            d: 'EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei',
            br: [],
            ba: [],
        },
        di: 'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose',
    },
    controller: {
        state: {
            vn: [1, 0],
            i: 'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose',
            s: '0',
            p: '',
            d: 'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose',
            f: '0',
            dt: '2023-08-19T21:04:57.959047+00:00',
            et: 'icp',
            kt: '1',
            k: ['DAbWjobbaLqRB94KiAutAHb_qzPpOHm3LURA_ksxetVc'],
            nt: '1',
            n: ['EIFG_uqfr1yN560LoHYHfvPAhxQ5sN6xZZT_E3h7d2tL'],
            bt: '0',
            b: [],
            c: [],
            ee: {
                s: '0',
                d: 'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose',
                br: [],
                ba: [],
            },
            di: '',
        },
        ee: {
            v: 'KERI10JSON00012b_',
            t: 'icp',
            d: 'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose',
            i: 'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose',
            s: '0',
            kt: '1',
            k: ['DAbWjobbaLqRB94KiAutAHb_qzPpOHm3LURA_ksxetVc'],
            nt: '1',
            n: ['EIFG_uqfr1yN560LoHYHfvPAhxQ5sN6xZZT_E3h7d2tL'],
            bt: '0',
            b: [],
            c: [],
            a: [],
        },
    },
    ridx: 0,
    pidx: 0,
};
const mockGetAID = {
    name: 'aid1',
    prefix: 'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK',
    salty: {
        sxlt: '1AAHnNQTkD0yxOC9tSz_ukbB2e-qhDTStH18uCsi5PCwOyXLONDR3MeKwWv_AVJKGKGi6xiBQH25_R1RXLS2OuK3TN3ovoUKH7-A',
        pidx: 0,
        kidx: 0,
        stem: 'signify:aid',
        tier: 'low',
        dcode: 'E',
        icodes: ['A'],
        ncodes: ['A'],
        transferable: true,
    },
    transferable: true,
    state: {
        vn: [1, 0],
        i: 'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK',
        s: '0',
        p: '',
        d: 'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK',
        f: '0',
        dt: '2023-08-21T22:30:46.473545+00:00',
        et: 'icp',
        kt: '1',
        k: ['DPmhSfdhCPxr3EqjxzEtF8TVy0YX7ATo0Uc8oo2cnmY9'],
        nt: '1',
        n: ['EAORnRtObOgNiOlMolji-KijC_isa3lRDpHCsol79cOc'],
        bt: '0',
        b: [],
        c: [],
        ee: {
            s: '0',
            d: 'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK',
            br: [],
            ba: [],
        },
        di: '',
    },
    windexes: [],
};

const mockCredential = {
    sad: {
        v: 'ACDC10JSON000197_',
        d: 'EMwcsEMUEruPXVwPCW7zmqmN8m0I3CihxolBm-RDrsJo',
        i: 'EMQQpnSkgfUOgWdzQTWfrgiVHKIDAhvAZIPQ6z3EAfz1',
        ri: 'EGK216v1yguLfex4YRFnG7k1sXRjh3OKY7QqzdKsx7df',
        s: 'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao',
        a: {
            d: 'EK0GOjijKd8_RLYz9qDuuG29YbbXjU8yJuTQanf07b6P',
            i: 'EKvn1M6shPLnXTb47bugVJblKMuWC0TcLIePP8p98Bby',
            dt: '2023-08-23T15:16:07.553000+00:00',
            LEI: '5493001KJTIIGC8Y1R17',
        },
    },
    pre: 'EMQQpnSkgfUOgWdzQTWfrgiVHKIDAhvAZIPQ6z3EAfz1',
    sadsigers: [
        {
            path: '-',
            pre: 'EMQQpnSkgfUOgWdzQTWfrgiVHKIDAhvAZIPQ6z3EAfz1',
            sn: 0,
            d: 'EMQQpnSkgfUOgWdzQTWfrgiVHKIDAhvAZIPQ6z3EAfz1',
        },
    ],
    sadcigars: [],
    chains: [],
    status: {
        v: 'KERI10JSON000135_',
        i: 'EMwcsEMUEruPXVwPCW7zmqmN8m0I3CihxolBm-RDrsJo',
        s: '0',
        d: 'ENf3IEYwYtFmlq5ZzoI-zFzeR7E3ZNRN2YH_0KAFbdJW',
        ri: 'EGK216v1yguLfex4YRFnG7k1sXRjh3OKY7QqzdKsx7df',
        ra: {},
        a: { s: 2, d: 'EIpgyKVF0z0Pcn2_HgbWhEKmJhOXFeD4SA62SrxYXOLt' },
        dt: '2023-08-23T15:16:07.553000+00:00',
        et: 'iss',
    },
};

fetchMock.mockResponse((req) => {
    if (req.url.startsWith(url + '/agent')) {
        return Promise.resolve({
            body: JSON.stringify(mockConnect),
            init: { status: 202 },
        });
    } else if (req.url == boot_url + '/boot') {
        return Promise.resolve({ body: '', init: { status: 202 } });
    } else {
        const headers = new Headers();
        let signed_headers = new Headers();

        headers.set(
            'Signify-Resource',
            'EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei'
        );
        headers.set(
            'Signify-Timestamp',
            new Date().toISOString().replace('Z', '000+00:00')
        );
        headers.set('Content-Type', 'application/json');

        const requrl = new URL(req.url);
        const salter = new Salter({ qb64: '0AAwMTIzNDU2Nzg5YWJjZGVm' });
        const signer = salter.signer(
            'A',
            true,
            'agentagent-ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose00',
            Tier.low
        );

        const authn = new Authenticater(signer!, signer!.verfer);
        signed_headers = authn.sign(
            headers,
            req.method,
            requrl.pathname.split('?')[0]
        );
        const body = req.url.startsWith(url + '/credentials')
            ? mockCredential
            : mockGetAID;

        return Promise.resolve({
            body: JSON.stringify(body),
            init: { status: 202, headers: signed_headers },
        });
    }
});

describe('Credentialing', () => {
    it('Credentials', async () => {
        await libsodium.ready;
        const bran = '0123456789abcdefghijk';

        const client = new SignifyClient(url, bran, Tier.low, boot_url);

        await client.boot();
        await client.connect();

        const credentials = client.credentials();

        const kargs = {
            filter: {
                '-i': { $eq: 'EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX' },
            },
            sort: [{ '-s': 1 }],
            limit: 25,
            skip: 5,
        };
        await credentials.list(kargs);
        let lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        let lastBody = JSON.parse(lastCall[1]!.body!.toString());
        assert.equal(lastCall[0]!, url + '/credentials/query');
        assert.equal(lastCall[1]!.method, 'POST');
        assert.deepEqual(lastBody, kargs);

        await credentials.get(
            'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao',
            true
        );
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(
            lastCall[0]!,
            url + '/credentials/EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao'
        );
        assert.equal(lastCall[1]!.method, 'GET');

        const registry = 'EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX';
        const schema = 'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao';
        const isuee = 'EG2XjQN-3jPN5rcR4spLjaJyM4zA6Lgg-Hd5vSMymu5p';
        await credentials.issue('aid1', {
            ri: registry,
            s: schema,
            a: { i: isuee, LEI: '1234' },
        });
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        lastBody = JSON.parse(lastCall[1]!.body!.toString());
        assert.equal(lastCall[0]!, url + '/identifiers/aid1/credentials');
        assert.equal(lastCall[1]!.method, 'POST');
        assert.equal(lastBody.acdc.ri, registry);
        assert.equal(lastBody.acdc.s, schema);
        assert.equal(lastBody.acdc.a.i, isuee);
        assert.equal(lastBody.acdc.a.LEI, '1234');
        assert.equal(lastBody.iss.s, '0');
        assert.equal(lastBody.iss.t, 'iss');
        assert.equal(lastBody.iss.ri, registry);
        assert.equal(lastBody.iss.i, lastBody.acdc.d);
        assert.equal(lastBody.ixn.t, 'ixn');
        assert.equal(lastBody.ixn.i, lastBody.acdc.i);
        assert.equal(lastBody.ixn.p, lastBody.acdc.i);
        assert.equal(lastBody.sigs[0].substring(0, 2), 'AA');
        assert.equal(lastBody.sigs[0].length, 88);

        const credential = lastBody.acdc.i;
        await credentials.revoke('aid1', credential);
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        lastBody = JSON.parse(lastCall[1]!.body!.toString());
        assert.equal(
            lastCall[0]!,
            url + '/identifiers/aid1/credentials/' + credential
        );
        assert.equal(lastCall[1]!.method, 'DELETE');
        assert.equal(lastBody.rev.s, '1');
        assert.equal(lastBody.rev.t, 'rev');
        assert.equal(
            lastBody.rev.ri,
            'EGK216v1yguLfex4YRFnG7k1sXRjh3OKY7QqzdKsx7df'
        );
        assert.equal(
            lastBody.rev.i,
            'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK'
        );
        assert.equal(lastBody.ixn.t, 'ixn');
        assert.equal(
            lastBody.ixn.i,
            'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK'
        );
        assert.equal(
            lastBody.ixn.p,
            'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK'
        );
        assert.equal(lastBody.sigs[0].substring(0, 2), 'AA');
        assert.equal(lastBody.sigs[0].length, 88);

        await credentials.state(mockCredential.sad.ri, mockCredential.sad.d);
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(
            lastCall[0]!,
            url +
                '/registries/EGK216v1yguLfex4YRFnG7k1sXRjh3OKY7QqzdKsx7df/EMwcsEMUEruPXVwPCW7zmqmN8m0I3CihxolBm-RDrsJo'
        );
        assert.equal(lastCall[1]!.method, 'GET');
        assert.equal(lastCall[1]!.body, null);

        await credentials.delete(mockCredential.sad.d);
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(
            lastCall[0]!,
            url + '/credentials/EMwcsEMUEruPXVwPCW7zmqmN8m0I3CihxolBm-RDrsJo'
        );
        assert.equal(lastCall[1]!.method, 'DELETE');
        assert.equal(lastCall[1]!.body, undefined);
    });
});

describe('Ipex', () => {
    it('IPEX - grant-admit flow initiated by discloser', async () => {
        await libsodium.ready;
        const bran = '0123456789abcdefghijk';
        const client = new SignifyClient(url, bran, Tier.low, boot_url);

        await client.boot();
        await client.connect();

        const ipex = client.ipex();

        const holder = 'ELjSFdrTdCebJlmvbFNX9-TLhR2PO0_60al1kQp5_e6k';
        const [, acdc] = Saider.saidify(mockCredential.sad);

        // Create iss
        const vs = versify(Ident.KERI, undefined, Serials.JSON, 0);
        const _iss = {
            v: vs,
            t: Ilks.iss,
            d: '',
            i: mockCredential.sad.d,
            s: '0',
            ri: mockCredential.sad.ri,
            dt: mockCredential.sad.a.dt,
        };

        const [, iss] = Saider.saidify(_iss);
        const iserder = new Serder(iss);
        const anc = interact({
            pre: mockCredential.sad.i,
            sn: 1,
            data: [{}],
            dig: mockCredential.sad.d,
            version: undefined,
            kind: undefined,
        });

        const [grant, gsigs, end] = await ipex.grant({
            senderName: 'multisig',
            recipient: holder,
            message: '',
            acdc: new Serder(acdc),
            iss: iserder,
            anc,
            datetime: mockCredential.sad.a.dt,
        });

        assert.deepStrictEqual(grant.ked, {
            v: 'KERI10JSON0004e5_',
            t: 'exn',
            d: 'EPVuNFwXTG56BvNtGjeyxncY-MfZMXOAgEtsmIvktkdb',
            i: 'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK',
            p: '',
            dt: '2023-08-23T15:16:07.553000+00:00',
            r: '/ipex/grant',
            rp: 'ELjSFdrTdCebJlmvbFNX9-TLhR2PO0_60al1kQp5_e6k',
            q: {},
            a: { m: '', i: 'ELjSFdrTdCebJlmvbFNX9-TLhR2PO0_60al1kQp5_e6k' },
            e: {
                acdc: {
                    v: 'ACDC10JSON000197_',
                    d: 'EMwcsEMUEruPXVwPCW7zmqmN8m0I3CihxolBm-RDrsJo',
                    i: 'EMQQpnSkgfUOgWdzQTWfrgiVHKIDAhvAZIPQ6z3EAfz1',
                    ri: 'EGK216v1yguLfex4YRFnG7k1sXRjh3OKY7QqzdKsx7df',
                    s: 'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao',
                    a: {
                        d: 'EK0GOjijKd8_RLYz9qDuuG29YbbXjU8yJuTQanf07b6P',
                        i: 'EKvn1M6shPLnXTb47bugVJblKMuWC0TcLIePP8p98Bby',
                        dt: '2023-08-23T15:16:07.553000+00:00',
                        LEI: '5493001KJTIIGC8Y1R17',
                    },
                },
                iss: {
                    v: 'KERI10JSON0000ed_',
                    t: 'iss',
                    d: 'ENf3IEYwYtFmlq5ZzoI-zFzeR7E3ZNRN2YH_0KAFbdJW',
                    i: 'EMwcsEMUEruPXVwPCW7zmqmN8m0I3CihxolBm-RDrsJo',
                    s: '0',
                    ri: 'EGK216v1yguLfex4YRFnG7k1sXRjh3OKY7QqzdKsx7df',
                    dt: '2023-08-23T15:16:07.553000+00:00',
                },
                anc: {
                    v: 'KERI10JSON0000cd_',
                    t: 'ixn',
                    d: 'ECVCyxNpB4PJkpLbWqI02WXs1wf7VUxPNY2W28SN2qqm',
                    i: 'EMQQpnSkgfUOgWdzQTWfrgiVHKIDAhvAZIPQ6z3EAfz1',
                    s: '1',
                    p: 'EMwcsEMUEruPXVwPCW7zmqmN8m0I3CihxolBm-RDrsJo',
                    a: [{}],
                },
                d: 'EGpSjqjavdzgjQiyt0AtrOutWfKrj5gR63lOUUq-1sL-',
            },
        });

        assert.deepStrictEqual(gsigs, [
            'AADGVl57V4gcKYPO_Dn4UuYIdHI62vEQP--U3pnsl8oCqiqQbRqjw2E_7PHBy5-U78de5rhfF4UZQBFeub5evO8M',
        ]);
        assert.equal(
            end,
            '-LAg4AACA-e-acdc-IABEMwcsEMUEruPXVwPCW7zmqmN8m0I3CihxolBm-RDrsJo0AAAAAAAAAAAAAAAAAAAAAAAENf3IEYwYtFmlq5Zz' +
                'oI-zFzeR7E3ZNRN2YH_0KAFbdJW-LAW5AACAA-e-iss-VAS-GAB0AAAAAAAAAAAAAAAAAAAAAAAECVCyxNpB4PJkpLbWqI02WXs1wf7VU' +
                'xPNY2W28SN2qqm-LAa5AACAA-e-anc-AABAADMtDfNihvCSXJNp1VronVojcPGo--0YZ4Kh6CAnowRnn4Or4FgZQqaqCEv6XVS413qfZo' +
                'Vp8j2uxTTPkItO7ED'
        );

        const [ng, ngsigs, ngend] = await ipex.grant({
            senderName: 'multisig',
            recipient: holder,
            message: '',
            acdc: new Serder(acdc),
            acdcAttachment: d(serializeACDCAttachment(iserder)),
            iss: iserder,
            issAttachment: d(serializeIssExnAttachment(anc)),
            anc,
            ancAttachment:
                '-AABAADMtDfNihvCSXJNp1VronVojcPGo--0YZ4Kh6CAnowRnn4Or4FgZQqaqCEv6XVS413qfZoVp8j2uxTTPkItO7ED',
            datetime: mockCredential.sad.a.dt,
        });

        assert.deepStrictEqual(ng.ked, grant.ked);
        assert.deepStrictEqual(ngsigs, gsigs);
        assert.deepStrictEqual(ngend, ngend);

        await ipex.submitGrant('multisig', ng, ngsigs, ngend, [holder]);
        let lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(
            lastCall[0],
            'http://127.0.0.1:3901/identifiers/multisig/ipex/grant'
        );

        const [admit, asigs, aend] = await ipex.admit({
            senderName: 'holder',
            message: '',
            grantSaid: grant.ked.d,
            recipient: holder,
            datetime: mockCredential.sad.a.dt,
        });

        assert.deepStrictEqual(admit.ked, {
            v: 'KERI10JSON000178_',
            t: 'exn',
            d: 'EJrfQsTZhkHC6vDEwkbWISpbBk9HFLO3NuI5uByYw8tH',
            i: 'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK',
            p: 'EPVuNFwXTG56BvNtGjeyxncY-MfZMXOAgEtsmIvktkdb',
            dt: '2023-08-23T15:16:07.553000+00:00',
            r: '/ipex/admit',
            rp: 'ELjSFdrTdCebJlmvbFNX9-TLhR2PO0_60al1kQp5_e6k',
            q: {},
            a: { m: '', i: 'ELjSFdrTdCebJlmvbFNX9-TLhR2PO0_60al1kQp5_e6k' },
            e: {},
        });

        assert.deepStrictEqual(asigs, [
            'AAC4MTRQR-U8_3Hf53f2nJuh3n93lauXSHUkF1Yk2diTHwF-qkcBHn_jd-6pgRnRtBV2CInfwZyOsSL2CrRyuNEN',
        ]);

        await ipex.submitAdmit('multisig', admit, asigs, aend, [holder]);
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(
            lastCall[0],
            'http://127.0.0.1:3901/identifiers/multisig/ipex/admit'
        );

        assert.equal(aend, '');
    });

    it('IPEX - apply-admit flow initiated by disclosee', async () => {
        await libsodium.ready;
        const bran = '0123456789abcdefghijk';
        const client = new SignifyClient(url, bran, Tier.low, boot_url);

        await client.boot();
        await client.connect();

        const ipex = client.ipex();

        const holder = 'ELjSFdrTdCebJlmvbFNX9-TLhR2PO0_60al1kQp5_e6k';
        const [, acdc] = Saider.saidify(mockCredential.sad);

        // Create iss
        const vs = versify(Ident.KERI, undefined, Serials.JSON, 0);
        const _iss = {
            v: vs,
            t: Ilks.iss,
            d: '',
            i: mockCredential.sad.d,
            s: '0',
            ri: mockCredential.sad.ri,
            dt: mockCredential.sad.a.dt,
        };

        const [, iss] = Saider.saidify(_iss);
        const iserder = new Serder(iss);
        const anc = interact({
            pre: mockCredential.sad.i,
            sn: 1,
            data: [{}],
            dig: mockCredential.sad.d,
            version: undefined,
            kind: undefined,
        });

        const [apply, applySigs, applyEnd] = await ipex.apply({
            senderName: 'multisig',
            recipient: holder,
            message: 'Applying',
            schemaSaid: mockCredential.sad.s,
            attributes: { LEI: mockCredential.sad.a.LEI },
            datetime: mockCredential.sad.a.dt,
        });

        assert.deepStrictEqual(apply.ked, {
            v: 'KERI10JSON0001aa_',
            t: 'exn',
            d: 'ELjIE5cr_M2r7oUYw2pwcdNY_ZBuEgRlefaP0zSs_bXL',
            i: 'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK',
            p: '',
            dt: '2023-08-23T15:16:07.553000+00:00',
            r: '/ipex/apply',
            rp: 'ELjSFdrTdCebJlmvbFNX9-TLhR2PO0_60al1kQp5_e6k',
            q: {},
            a: {
                m: 'Applying',
                i: 'ELjSFdrTdCebJlmvbFNX9-TLhR2PO0_60al1kQp5_e6k',
                s: 'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao',
                a: { LEI: '5493001KJTIIGC8Y1R17' },
            },
            e: {},
        });

        assert.deepStrictEqual(applySigs, [
            'AADJYSkOTxd8KfH4YUKWWjkNynAH4fm3wcKOPmepLiI_iuNPV9TL-sIRxLeCBG5rQmqXtnSP0Wi6jgI7sHC9PBgF',
        ]);

        assert.equal(applyEnd, '');

        await ipex.submitApply('multisig', apply, applySigs, [holder]);
        let lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(
            lastCall[0],
            'http://127.0.0.1:3901/identifiers/multisig/ipex/apply'
        );

        const [offer, offerSigs, offerEnd] = await ipex.offer({
            senderName: 'multisig',
            recipient: holder,
            message: 'How about this',
            acdc: new Serder(acdc),
            datetime: mockCredential.sad.a.dt,
            applySaid: apply.ked.d,
        });

        assert.deepStrictEqual(offer.ked, {
            v: 'KERI10JSON000357_',
            t: 'exn',
            d: 'EBkyi_fhfnDWJXi4FW6t_o4F7Oep3PvSZ6E-qT716kfU',
            i: 'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK',
            p: 'ELjIE5cr_M2r7oUYw2pwcdNY_ZBuEgRlefaP0zSs_bXL',
            dt: '2023-08-23T15:16:07.553000+00:00',
            r: '/ipex/offer',
            rp: 'ELjSFdrTdCebJlmvbFNX9-TLhR2PO0_60al1kQp5_e6k',
            q: {},
            a: {
                m: 'How about this',
                i: 'ELjSFdrTdCebJlmvbFNX9-TLhR2PO0_60al1kQp5_e6k',
            },
            e: {
                acdc: {
                    v: 'ACDC10JSON000197_',
                    d: 'EMwcsEMUEruPXVwPCW7zmqmN8m0I3CihxolBm-RDrsJo',
                    i: 'EMQQpnSkgfUOgWdzQTWfrgiVHKIDAhvAZIPQ6z3EAfz1',
                    ri: 'EGK216v1yguLfex4YRFnG7k1sXRjh3OKY7QqzdKsx7df',
                    s: 'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao',
                    a: {
                        d: 'EK0GOjijKd8_RLYz9qDuuG29YbbXjU8yJuTQanf07b6P',
                        i: 'EKvn1M6shPLnXTb47bugVJblKMuWC0TcLIePP8p98Bby',
                        dt: '2023-08-23T15:16:07.553000+00:00',
                        LEI: '5493001KJTIIGC8Y1R17',
                    },
                },
                d: 'EK72JZyOyz81Jvt--iebptfhIWiw2ZdQg7ondKd-EyJF',
            },
        });

        assert.deepStrictEqual(offerSigs, [
            'AADUeKpUxTKVS1DYRuHC3YDM8T4YMREnQLi00QiJH2Q_WjtMZTd7rBLH12xAJkt8h4KEOn4U_c-jpHdj9S9qKXsO',
        ]);
        assert.equal(offerEnd, '');

        await ipex.submitOffer('multisig', offer, offerSigs, offerEnd, [
            holder,
        ]);
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(
            lastCall[0],
            'http://127.0.0.1:3901/identifiers/multisig/ipex/offer'
        );

        const [agree, agreeSigs, agreeEnd] = await ipex.agree({
            senderName: 'multisig',
            recipient: holder,
            message: 'OK!',
            datetime: mockCredential.sad.a.dt,
            offerSaid: offer.ked.d,
        });

        assert.deepStrictEqual(agree.ked, {
            v: 'KERI10JSON00017b_',
            t: 'exn',
            d: 'EDLk56nlLrPHzhy3-5BHkhBNi-7tWUseWL_83I5QRmZ8',
            i: 'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK',
            p: 'EBkyi_fhfnDWJXi4FW6t_o4F7Oep3PvSZ6E-qT716kfU',
            dt: '2023-08-23T15:16:07.553000+00:00',
            r: '/ipex/agree',
            rp: 'ELjSFdrTdCebJlmvbFNX9-TLhR2PO0_60al1kQp5_e6k',
            q: {},
            a: {
                m: 'OK!',
                i: 'ELjSFdrTdCebJlmvbFNX9-TLhR2PO0_60al1kQp5_e6k',
            },
            e: {},
        });

        assert.deepStrictEqual(agreeSigs, [
            'AADgFlQVwRU7PF_gi4_o-wEgh3lZxzDtiwnIr9XFBrLOxhR6nBJNhrHZ_MkagCQcFHMpFkD9Vhxgq8HkV2gssPcO',
        ]);
        assert.equal(agreeEnd, '');

        await ipex.submitAgree('multisig', agree, agreeSigs, [holder]);
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(
            lastCall[0],
            'http://127.0.0.1:3901/identifiers/multisig/ipex/agree'
        );

        const [grant, gsigs, end] = await ipex.grant({
            senderName: 'multisig',
            recipient: holder,
            message: '',
            acdc: new Serder(acdc),
            iss: iserder,
            anc,
            datetime: mockCredential.sad.a.dt,
            agreeSaid: agree.ked.d,
        });

        assert.deepStrictEqual(grant.ked, {
            v: 'KERI10JSON000511_',
            t: 'exn',
            d: 'ENwwMpAuZ3NaZqqeydm3G18EDZFWuHzeJMfzfwNkb99N',
            i: 'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK',
            p: 'EDLk56nlLrPHzhy3-5BHkhBNi-7tWUseWL_83I5QRmZ8',
            dt: '2023-08-23T15:16:07.553000+00:00',
            r: '/ipex/grant',
            rp: 'ELjSFdrTdCebJlmvbFNX9-TLhR2PO0_60al1kQp5_e6k',
            q: {},
            a: { m: '', i: 'ELjSFdrTdCebJlmvbFNX9-TLhR2PO0_60al1kQp5_e6k' },
            e: {
                acdc: {
                    v: 'ACDC10JSON000197_',
                    d: 'EMwcsEMUEruPXVwPCW7zmqmN8m0I3CihxolBm-RDrsJo',
                    i: 'EMQQpnSkgfUOgWdzQTWfrgiVHKIDAhvAZIPQ6z3EAfz1',
                    ri: 'EGK216v1yguLfex4YRFnG7k1sXRjh3OKY7QqzdKsx7df',
                    s: 'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao',
                    a: {
                        d: 'EK0GOjijKd8_RLYz9qDuuG29YbbXjU8yJuTQanf07b6P',
                        i: 'EKvn1M6shPLnXTb47bugVJblKMuWC0TcLIePP8p98Bby',
                        dt: '2023-08-23T15:16:07.553000+00:00',
                        LEI: '5493001KJTIIGC8Y1R17',
                    },
                },
                iss: {
                    v: 'KERI10JSON0000ed_',
                    t: 'iss',
                    d: 'ENf3IEYwYtFmlq5ZzoI-zFzeR7E3ZNRN2YH_0KAFbdJW',
                    i: 'EMwcsEMUEruPXVwPCW7zmqmN8m0I3CihxolBm-RDrsJo',
                    s: '0',
                    ri: 'EGK216v1yguLfex4YRFnG7k1sXRjh3OKY7QqzdKsx7df',
                    dt: '2023-08-23T15:16:07.553000+00:00',
                },
                anc: {
                    v: 'KERI10JSON0000cd_',
                    t: 'ixn',
                    d: 'ECVCyxNpB4PJkpLbWqI02WXs1wf7VUxPNY2W28SN2qqm',
                    i: 'EMQQpnSkgfUOgWdzQTWfrgiVHKIDAhvAZIPQ6z3EAfz1',
                    s: '1',
                    p: 'EMwcsEMUEruPXVwPCW7zmqmN8m0I3CihxolBm-RDrsJo',
                    a: [{}],
                },
                d: 'EGpSjqjavdzgjQiyt0AtrOutWfKrj5gR63lOUUq-1sL-',
            },
        });

        assert.deepStrictEqual(gsigs, [
            'AAB61_g8jLGO1vx8Fadd6UrDItNACwFAiuAvWGrm_szxWWNZwT21V0N79Q7bRHNdVzZudgAKVUhNUHhnwrUW6jsK',
        ]);
        assert.equal(
            end,
            '-LAg4AACA-e-acdc-IABEMwcsEMUEruPXVwPCW7zmqmN8m0I3CihxolBm-RDrsJo0AAAAAAAAAAAAAAAAAAAAAAAENf3IEYwYtFmlq5Zz' +
                'oI-zFzeR7E3ZNRN2YH_0KAFbdJW-LAW5AACAA-e-iss-VAS-GAB0AAAAAAAAAAAAAAAAAAAAAAAECVCyxNpB4PJkpLbWqI02WXs1wf7VU' +
                'xPNY2W28SN2qqm-LAa5AACAA-e-anc-AABAADMtDfNihvCSXJNp1VronVojcPGo--0YZ4Kh6CAnowRnn4Or4FgZQqaqCEv6XVS413qfZo' +
                'Vp8j2uxTTPkItO7ED'
        );

        const [ng, ngsigs, ngend] = await ipex.grant({
            senderName: 'multisig',
            recipient: holder,
            message: '',
            acdc: new Serder(acdc),
            acdcAttachment: d(serializeACDCAttachment(iserder)),
            iss: iserder,
            issAttachment: d(serializeIssExnAttachment(anc)),
            anc,
            ancAttachment:
                '-AABAADMtDfNihvCSXJNp1VronVojcPGo--0YZ4Kh6CAnowRnn4Or4FgZQqaqCEv6XVS413qfZoVp8j2uxTTPkItO7ED',
            datetime: mockCredential.sad.a.dt,
            agreeSaid: agree.ked.d,
        });

        assert.deepStrictEqual(ng.ked, grant.ked);
        assert.deepStrictEqual(ngsigs, gsigs);
        assert.deepStrictEqual(ngend, ngend);

        await ipex.submitGrant('multisig', ng, ngsigs, ngend, [holder]);
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(
            lastCall[0],
            'http://127.0.0.1:3901/identifiers/multisig/ipex/grant'
        );

        const [admit, asigs, aend] = await ipex.admit({
            senderName: 'holder',
            message: '',
            recipient: holder,
            grantSaid: grant.ked.d,
            datetime: mockCredential.sad.a.dt,
        });

        assert.deepStrictEqual(admit.ked, {
            v: 'KERI10JSON000178_',
            t: 'exn',
            d: 'EPcEK9tPuLOHbLiPm_FETkIVLjHhwuUiZDRDKW6Hh0JF',
            i: 'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK',
            p: 'ENwwMpAuZ3NaZqqeydm3G18EDZFWuHzeJMfzfwNkb99N',
            dt: '2023-08-23T15:16:07.553000+00:00',
            r: '/ipex/admit',
            rp: 'ELjSFdrTdCebJlmvbFNX9-TLhR2PO0_60al1kQp5_e6k',
            q: {},
            a: { m: '', i: 'ELjSFdrTdCebJlmvbFNX9-TLhR2PO0_60al1kQp5_e6k' },
            e: {},
        });

        assert.deepStrictEqual(asigs, [
            'AABqIUE6czxB5BotjxFUZT9Gu8tkFkAx7bOYQzWD422r-HS8z_6gaNuIlpnABHjxlX7PEXFDTj8WnoGVW197XlQP',
        ]);

        await ipex.submitAdmit('multisig', admit, asigs, aend, [holder]);
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(
            lastCall[0],
            'http://127.0.0.1:3901/identifiers/multisig/ipex/admit'
        );

        assert.equal(aend, '');
    });

    it('IPEX - discloser can create an offer without apply', async () => {
        await libsodium.ready;
        const bran = '0123456789abcdefghijk';
        const client = new SignifyClient(url, bran, Tier.low, boot_url);

        await client.boot();
        await client.connect();

        const ipex = client.ipex();

        const holder = 'ELjSFdrTdCebJlmvbFNX9-TLhR2PO0_60al1kQp5_e6k';
        const [, acdc] = Saider.saidify(mockCredential.sad);

        const [offer, offerSigs, offerEnd] = await ipex.offer({
            senderName: 'multisig',
            recipient: holder,
            message: 'Offering this',
            acdc: new Serder(acdc),
            datetime: mockCredential.sad.a.dt,
        });

        assert.deepStrictEqual(offer.ked, {
            v: 'KERI10JSON00032a_',
            t: 'exn',
            d: 'EFmPdhVnJIrMZ0b6Nyk-4s2NP1InR3wgvBGcbxl2Cd8i',
            i: 'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK',
            p: '',
            dt: '2023-08-23T15:16:07.553000+00:00',
            r: '/ipex/offer',
            rp: 'ELjSFdrTdCebJlmvbFNX9-TLhR2PO0_60al1kQp5_e6k',
            q: {},
            a: {
                m: 'Offering this',
                i: 'ELjSFdrTdCebJlmvbFNX9-TLhR2PO0_60al1kQp5_e6k',
            },
            e: {
                acdc: {
                    v: 'ACDC10JSON000197_',
                    d: 'EMwcsEMUEruPXVwPCW7zmqmN8m0I3CihxolBm-RDrsJo',
                    i: 'EMQQpnSkgfUOgWdzQTWfrgiVHKIDAhvAZIPQ6z3EAfz1',
                    ri: 'EGK216v1yguLfex4YRFnG7k1sXRjh3OKY7QqzdKsx7df',
                    s: 'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao',
                    a: {
                        d: 'EK0GOjijKd8_RLYz9qDuuG29YbbXjU8yJuTQanf07b6P',
                        i: 'EKvn1M6shPLnXTb47bugVJblKMuWC0TcLIePP8p98Bby',
                        dt: '2023-08-23T15:16:07.553000+00:00',
                        LEI: '5493001KJTIIGC8Y1R17',
                    },
                },
                d: 'EK72JZyOyz81Jvt--iebptfhIWiw2ZdQg7ondKd-EyJF',
            },
        });

        assert.deepStrictEqual(offerSigs, [
            'AACeQZ8RAcD2qFbkGXiUAQRJpZL4qanNH50a0LnkrflOC9JB2UJo3vvy3buiOSLoo0z9uMNhqa79ToXwVCAxg9MK',
        ]);
        assert.equal(offerEnd, '');

        await ipex.submitOffer('multisig', offer, offerSigs, offerEnd, [
            holder,
        ]);
        const lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!;
        assert.equal(
            lastCall[0],
            'http://127.0.0.1:3901/identifiers/multisig/ipex/offer'
        );
    });
});
