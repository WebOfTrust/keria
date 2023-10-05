import {
    Dict,
    Ident,
    Serials,
    versify,
    Versionage,
} from '../../src/keri/core/core';
import { strict as assert } from 'assert';
import { MtrDex } from '../../src/keri/core/matter';
import libsodium from 'libsodium-wrappers-sumo';
import { Saider } from '../../src/keri/core/saider';

describe('Saider', () => {
    it('should create Saidified dicts', async () => {
        await libsodium.ready;

        let kind = Serials.JSON;
        let code = MtrDex.Blake3_256;

        let vs = versify(Ident.KERI, Versionage, kind, 0); // vaccuous size == 0
        assert.equal(vs, 'KERI10JSON000000_');
        let sad4 = {
            v: vs,
            t: 'rep',
            d: '', // vacuous said
            dt: '2020-08-22T17:50:12.988921+00:00',
            r: 'logs/processor',
            a: {
                d: 'EBabiu_JCkE0GbiglDXNB5C4NQq-hiGgxhHKXBxkiojg',
                i: 'EB0_D51cTh_q6uOQ-byFiv5oNXZ-cxdqCqBAa4JmBLtb',
                name: 'John Jones',
                role: 'Founder',
            } as Dict<any>,
        } as Dict<any>;
        let saider = new Saider({}, sad4); // default version string code, kind, and label
        assert.equal(saider.code, code);
        assert.equal(
            saider.qb64,
            'ELzewBpZHSENRP-sL_G_2Ji4YDdNkns9AzFzufleJqdw'
        );
    });
});
