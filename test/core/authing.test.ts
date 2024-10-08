import { strict as assert } from 'assert';
import libsodium from 'libsodium-wrappers-sumo';
import { Salter } from '../../src/keri/core/salter';
import { b } from '../../src/keri/core/core';
import { Authenticater } from '../../src/keri/core/authing';
import * as utilApi from '../../src/keri/core/utils';
import { Verfer } from '../../src/keri/core/verfer';

describe('Authenticater.verify', () => {
    it('verify signature on Response', async () => {
        await libsodium.ready;
        const salt = '0123456789abcdef';
        const salter = new Salter({ raw: b(salt) });
        const signer = salter.signer();
        const aaid = 'DMZh_y-H5C3cSbZZST-fqnsmdNTReZxIh0t2xSTOJQ8a';
        const verfer = new Verfer({ qb64: aaid });

        const headers = new Headers([
            ['Content-Length', '898'],
            ['Content-Type', 'application/json'],
            [
                'Signature',
                [
                    'indexed="?0"',
                    'signify="0BDLh8QCytVBx1YMam4Vt8s4b9HAW1dwfE4yU5H_w1V6gUvPBoVGWQlIMdC16T3WFWHDHCbMcuceQzrr6n9OULsK"',
                ].join(';'),
            ],
            [
                'Signature-Input',
                [
                    'signify=("signify-resource" "@method" "@path" "signify-timestamp")',
                    'created=1684715820',
                    'keyid="EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei"',
                    'alg="ed25519"',
                ].join(';'),
            ],
            [
                'Signify-Resource',
                'EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei',
            ],
            ['Signify-Timestamp', '2023-05-22T00:37:00.248708+00:00'],
        ]);

        const authn = new Authenticater(signer, verfer);
        assert.notEqual(authn, undefined);

        assert.equal(
            authn.verify(new Headers(headers), 'GET', '/identifiers/aid1'),
            true
        );
    });
});

describe('Authenticater.sign', () => {
    it('Create signed headers for a request', async () => {
        await libsodium.ready;
        const salt = '0123456789abcdef';
        const salter = new Salter({ raw: b(salt) });
        const signer = salter.signer();
        const aaid = 'DDK2N5_fVCWIEO9d8JLhk7hKrkft6MbtkUhaHQsmABHY';
        const verfer = new Verfer({ qb64: aaid });

        const headers = new Headers([
            ['Content-Type', 'application/json'],
            ['Content-Length', '256'],
            ['Connection', 'close'],
            [
                'Signify-Resource',
                'EWJkQCFvKuyxZi582yJPb0wcwuW3VXmFNuvbQuBpgmIs',
            ],
            ['Signify-Timestamp', '2022-09-24T00:05:48.196795+00:00'],
        ]);
        jest.spyOn(utilApi, 'nowUTC').mockReturnValue(
            new Date('2021-01-01T00:00:00.000000+00:00')
        );

        const authn = new Authenticater(signer, verfer);
        const result = authn.sign(headers, 'POST', '/boot');

        assert.equal(result.has('Signature-Input'), true);
        assert.equal(result.has('Signature'), true);

        const expectedSignatureInput = [
            'signify=("@method" "@path" "signify-resource" "signify-timestamp")',
            'created=1609459200',
            'keyid="DN54yRad_BTqgZYUSi_NthRBQrxSnqQdJXWI5UHcGOQt"',
            'alg="ed25519"',
        ].join(';');
        assert.equal(result.get('Signature-Input'), expectedSignatureInput);

        const expectedSignature = [
            'indexed="?0"',
            'signify="0BChvN_BWAf-mgEuTnWfNnktgHdWOuOh9cWc4o0GFWuZOwra3DyJT5dJ_6BX7AANDOTnIlAKh5Sg_9qGQXHjj5oJ"',
        ].join(';');
        assert.equal(result.get('Signature'), expectedSignature);
    });
});
