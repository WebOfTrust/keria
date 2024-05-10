import libsodium from 'libsodium-wrappers-sumo';
import {
    Algos,
    Creatory,
    Manager,
    RandyCreator,
    riKey,
    SaltyCreator,
} from '../../src/keri/core/manager';
import { strict as assert } from 'assert';
import { MtrDex } from '../../src/keri/core/matter';
import { Salter, Tier } from '../../src/keri/core/salter';
import { Signer } from '../../src/keri/core/signer';
import { Encrypter } from '../../src/keri/core/encrypter';
import { Decrypter } from '../../src/keri/core/decrypter';
import { Cipher } from '../../src/keri/core/cipher';
import { Verfer } from '../../src/keri/core/verfer';
import { Diger } from '../../src/keri/core/diger';
import { Siger } from '../../src/keri/core/siger';
import { b } from '../../src/keri/core/core';
import { Cigar } from '../../src/keri/core/cigar';
import {
    Keeper,
    KeeperParams,
    KeyManager,
    Prefixer,
    RandyKeeper,
} from '../../src';
import { RandyState, State } from '../../src/keri/core/state';
import { randomUUID } from 'crypto';

describe('RandyCreator', () => {
    it('should create sets of random signers', async () => {
        await libsodium.ready;

        const randy = new RandyCreator();

        // test default arguments
        let keys = randy.create();
        assert.equal(keys.signers.length, 1);
        assert.equal(keys.signers[0].qb64.length, 44);
        assert.equal(keys.signers[0].code, MtrDex.Ed25519_Seed);
        assert.equal(keys.signers[0].transferable, true);

        // Create 5 with default code
        keys = randy.create(undefined, 5);
        assert.equal(keys.signers.length, 5);
        keys.signers.forEach((signer) => {
            assert.equal(signer.qb64.length, 44);
            assert.equal(signer.code, MtrDex.Ed25519_Seed);
            assert.equal(signer.transferable, true);
        });

        // Create 3 with specified codes (the only one we support)
        keys = randy.create([
            MtrDex.Ed25519_Seed,
            MtrDex.Ed25519_Seed,
            MtrDex.Ed25519_Seed,
        ]);
        assert.equal(keys.signers.length, 3);
        keys.signers.forEach((signer) => {
            assert.equal(signer.qb64.length, 44);
            assert.equal(signer.code, MtrDex.Ed25519_Seed);
            assert.equal(signer.transferable, true);
        });
    });
});

describe('SaltyCreator', () => {
    it('should create sets of salty signers', async () => {
        await libsodium.ready;

        // Test default arguments
        let salty = new SaltyCreator();
        assert.equal(salty.salter.code, MtrDex.Salt_128);
        assert.equal(salty.salt, salty.salter.qb64);
        assert.equal(salty.stem, '');
        assert.equal(salty.tier, salty.salter.tier);

        let keys = salty.create();
        assert.equal(keys.signers.length, 1);
        assert.equal(keys.signers[0].qb64.length, 44);
        assert.equal(keys.signers[0].code, MtrDex.Ed25519_Seed);
        assert.equal(keys.signers[0].transferable, true);

        keys = salty.create(undefined, 2, MtrDex.Ed25519_Seed, false);
        assert.equal(keys.signers.length, 2);
        keys.signers.forEach((signer) => {
            assert.equal(signer.code, MtrDex.Ed25519_Seed);
            assert.equal(signer.verfer.code, MtrDex.Ed25519N);
            assert.equal(signer.qb64.length, 44);
        });

        const raw = '0123456789abcdef';
        const salter = new Salter({ raw: b(raw) });
        const salt = salter.qb64;
        assert.equal(salter.qb64, '0AAwMTIzNDU2Nzg5YWJjZGVm');
        salty = new SaltyCreator(salter.qb64);
        assert.equal(salty.salter.code, MtrDex.Salt_128);
        assert.deepStrictEqual(salty.salter.raw, b(raw));
        assert.equal(salty.salter.qb64, salt);
        assert.equal(salty.salt, salty.salter.qb64);
        assert.equal(salty.stem, '');
        assert.equal(salty.tier, salty.salter.tier);
        keys = salty.create();
        assert.equal(keys.signers.length, 1);
        assert.equal(keys.signers[0].code, MtrDex.Ed25519_Seed);
        assert.equal(
            keys.signers[0].qb64,
            'AO0hmkIVsjCoJY1oUe3-QqHlMBVIhFX1tQfN_8SPKiNF'
        );
        assert.equal(keys.signers[0].verfer.code, MtrDex.Ed25519);
        assert.equal(
            keys.signers[0].verfer.qb64,
            'DHHneREQ1eZyQNc5nEsQYx1FqFVL1OTXmvmatTE77Cfe'
        );

        keys = salty.create(
            undefined,
            1,
            MtrDex.Ed25519_Seed,
            false,
            0,
            0,
            0,
            true
        );
        assert.equal(keys.signers.length, 1);
        assert.equal(keys.signers[0].code, MtrDex.Ed25519_Seed);
        assert.equal(
            keys.signers[0].qb64,
            'AOVkNmL_dZ5pjvp-_nS5EJbs0xe32MODcOUOym-0aCBL'
        );
        assert.equal(keys.signers[0].verfer.code, MtrDex.Ed25519N);
        assert.equal(
            keys.signers[0].verfer.qb64,
            'BB-fH5uto5o5XHZjNN3_W3PdT4MIyTCmQWDzMxMZV2kI'
        );
    });
});

describe('Creator', () => {
    it('should create Randy or Salty creator', async () => {
        await libsodium.ready;

        const raw = '0123456789abcdef';
        const salter = new Salter({ raw: b(raw) });
        const salt = salter.qb64;

        let creator = new Creatory(Algos.salty).make(salt) as SaltyCreator;
        assert.equal(creator instanceof SaltyCreator, true);
        assert.equal(creator.salter.qb64, salt);

        creator = new Creatory().make(salt) as SaltyCreator;
        assert.equal(creator instanceof SaltyCreator, true);
        assert.equal(creator.salter.qb64, salt);

        const rcreator = new Creatory(Algos.randy).make(salt) as RandyCreator;
        assert.equal(rcreator instanceof RandyCreator, true);
    });
});

const ser =
    '{"vs":"KERI10JSON0000fb_","pre":"EvEnZMhz52iTrJU8qKwtDxzmypyosgG' +
    '70m6LIjkiCdoI","sn":"0","ilk":"icp","sith":"1","keys":["DSuhyBcP' +
    'ZEZLK-fcw5tzHn2N46wRCG_ZOoeKtWTOunRA"],"nxt":"EPYuj8mq_PYYsoBKkz' +
    'X1kxSPGYBWaIya3slgCOyOtlqU","toad":"0","wits":[],"cnfg":[]}-AABA' +
    'ApYcYd1cppVg7Inh2YCslWKhUwh59TrPpIoqWxN2A38NCbTljvmBPBjSGIFDBNOv' +
    'VjHpdZlty3Hgk6ilF8pVpAQ';

describe('Manager', () => {
    it('should manage key pairs for identifiers', async () => {
        await libsodium.ready;

        const raw = '0123456789abcdef';
        const salter = new Salter({ raw: b(raw) });
        const salt = salter.qb64;
        assert.equal(salt, '0AAwMTIzNDU2Nzg5YWJjZGVm');
        const stem = 'red';

        // Create a randy Manager without encryption should raise an exception
        assert.throws(() => {
            new Manager({ algo: Algos.randy });
        });

        // cryptseed0 = b('h,#|\x8ap"\x12\xc43t2\xa6\xe1\x18\x19\xf0f2,y\xc4\xc21@\xf5@\x15.\xa2\x1a\xcf')
        const cryptseed0 = new Uint8Array([
            104, 44, 35, 124, 138, 112, 34, 18, 196, 51, 116, 50, 166, 225, 24,
            25, 240, 102, 50, 44, 121, 196, 194, 49, 64, 245, 64, 21, 46, 162,
            26, 207,
        ]);
        const cryptsigner0 = new Signer({
            raw: cryptseed0,
            code: MtrDex.Ed25519_Seed,
            transferable: false,
        });
        const seed0 = cryptsigner0.qb64;
        const seed0b = cryptsigner0.qb64b;
        const aeid0 = cryptsigner0.verfer.qb64;
        assert.equal(aeid0, 'BCa7mK96FwxkU0TdF54Yqg3qBDXUWpOhQ_Mtr7E77yZB');
        const decrypter0 = new Decrypter({}, seed0b);
        const encrypter0 = new Encrypter({}, b(aeid0));
        assert.equal(encrypter0.verifySeed(seed0b), true);

        // cryptseed1 = (b"\x89\xfe{\xd9'\xa7\xb3\x89#\x19\xbec\xee\xed\xc0\xf9\x97\xd0\x8f9\x1dyNI"
        //                b'I\x98\xbd\xa4\xf6\xfe\xbb\x03')
        const cryptseed1 = new Uint8Array([
            137, 254, 123, 217, 39, 167, 179, 137, 35, 25, 190, 99, 238, 237,
            192, 249, 151, 208, 143, 57, 29, 121, 78, 73, 73, 152, 189, 164,
            246, 254, 187, 3,
        ]);
        const cryptsigner1 = new Signer({
            raw: cryptseed1,
            code: MtrDex.Ed25519_Seed,
            transferable: false,
        });
        const seed1 = cryptsigner1.qb64b;
        const aeid1 = cryptsigner1.verfer.qb64;
        assert.equal(aeid1, 'BEcOrMrG_7r_NWaLl6h8UJapwIfQWIkjrIPXkCZm2fFM');
        // let decrypter1 = new Decrypter({}, seed1)
        const encrypter1 = new Encrypter({}, b(aeid1));
        assert.equal(encrypter1.verifySeed(seed1), true);

        const manager = new Manager({
            seed: seed0,
            salter: salter,
            aeid: aeid0,
        });
        assert.equal(manager.encrypter!.qb64, encrypter0.qb64);
        assert.equal(manager.decrypter!.qb64, decrypter0.qb64);
        assert.equal(manager.seed, seed0);
        assert.equal(manager.aeid, aeid0);

        assert.equal(manager.algo, Algos.salty);
        assert.equal(manager.salt, salt);
        assert.equal(manager.pidx, 0);
        assert.equal(manager.tier, Tier.low);
        const saltCipher0 = new Cipher({ qb64: manager.ks.getGbls('salt') });
        assert.equal(saltCipher0.decrypt(undefined, seed0b).qb64, salt);

        let [verfers, digers] = manager.incept({ salt: salt, temp: true });
        assert.equal(verfers.length, 1);
        assert.equal(digers.length, 1);
        assert.equal(manager.pidx, 1);

        let spre = verfers[0].qb64;
        assert.equal(spre, 'DB-fH5uto5o5XHZjNN3_W3PdT4MIyTCmQWDzMxMZV2kI');

        let pp = manager.ks.getPrms(spre)!;
        assert.equal(pp.pidx, 0);
        assert.equal(pp.algo, Algos.salty);
        assert.equal(manager.decrypter!.decrypt(b(pp.salt)).qb64, salt);
        assert.equal(pp.stem, '');
        assert.equal(pp.tier, Tier.low);

        let ps = manager.ks.getSits(spre)!;
        assert.deepStrictEqual(ps.old.pubs, []);
        assert.equal(ps.new.pubs.length, 1);
        assert.deepStrictEqual(ps.new.pubs, [
            'DB-fH5uto5o5XHZjNN3_W3PdT4MIyTCmQWDzMxMZV2kI',
        ]);
        assert.equal(ps.new.ridx, 0);
        assert.equal(ps.new.kidx, 0);
        assert.equal(ps.nxt.pubs.length, 1);
        assert.deepStrictEqual(ps.nxt.pubs, [
            'DB-fH5uto5o5XHZjNN3_W3PdT4MIyTCmQWDzMxMZV2kI',
        ]);
        assert.equal(ps.nxt.ridx, 1);
        assert.equal(ps.nxt.kidx, 1);

        let keys = Array.from(verfers, (verfer: Verfer) => verfer.qb64);
        assert.deepStrictEqual(keys, ps.new.pubs);

        let pl = manager.ks.getPubs(riKey(spre, ps.new.ridx))!;
        assert.deepStrictEqual(pl.pubs, ps.new.pubs);
        pl = manager.ks.getPubs(riKey(spre, ps.nxt.ridx))!;
        assert.deepStrictEqual(pl.pubs, ps.nxt.pubs);

        let digs = Array.from(digers, (diger: Diger) => diger.qb64);
        assert.deepStrictEqual(digs, [
            'ENmcKrctbztF36MttN7seUYJqH2IMnkavBgGLR6Mj2-B',
        ]);

        const oldspre = spre;
        spre = 'DCu5o5cxzv1lgMqxMVG3IcCNK4lpFfpMM-9rfkY3XVUc';
        manager.move(oldspre, spre);

        pl = manager.ks.getPubs(riKey(spre, ps.new.ridx))!;
        assert.deepStrictEqual(pl.pubs, ps.new.pubs);
        pl = manager.ks.getPubs(riKey(spre, ps.nxt.ridx))!;
        assert.deepStrictEqual(pl.pubs, ps.nxt.pubs);

        const serb = b(ser);
        let psigers = manager.sign({ ser: serb, pubs: ps.new.pubs });
        assert.equal(psigers.length, 1);
        assert.equal(psigers[0] instanceof Siger, true);
        let vsigers = manager.sign({ ser: serb, verfers: verfers });
        let psigs = Array.from(
            psigers as Array<Siger>,
            (psiger) => psiger.qb64
        );
        let vsigs = Array.from(
            vsigers as Array<Siger>,
            (vsiger) => vsiger.qb64
        );
        assert.deepStrictEqual(psigs, vsigs);
        assert.equal(
            psigs[0],
            'AACRPqO6vdXm1oSSa82rmVVHikf7NdN4JXjOWEk30Ub5JHChL0bW6DzJfA-7VlgLm_B1XR0Z61FweP87bBQpVawI'
        );

        // Test sign with indices
        const indices = [3];
        psigers = manager.sign({
            ser: serb,
            pubs: ps.new.pubs,
            indices: indices,
        }) as Array<Siger>;
        assert.equal(psigers.length, 1);
        assert.equal(psigers[0] instanceof Siger, true);
        assert.equal(psigers[0].index, indices[0]);
        psigs = Array.from(psigers as Array<Siger>, (psiger) => psiger.qb64);
        assert.equal(
            psigs[0],
            'ADCRPqO6vdXm1oSSa82rmVVHikf7NdN4JXjOWEk30Ub5JHChL0bW6DzJfA-7VlgLm_B1XR0Z61FweP87bBQpVawI'
        );

        vsigers = manager.sign({
            ser: serb,
            verfers: verfers,
            indices: indices,
        }) as Array<Siger>;
        assert.equal(vsigers.length, 1);
        assert.equal(vsigers[0] instanceof Siger, true);
        assert.equal(vsigers[0].index, indices[0]);
        vsigs = Array.from(vsigers as Array<Siger>, (vsiger) => vsiger.qb64);
        assert.deepStrictEqual(psigs, vsigs);

        const pcigars = manager.sign({
            ser: serb,
            pubs: ps.new.pubs,
            indexed: false,
        });
        assert.equal(pcigars.length, 1);
        assert.equal(pcigars[0] instanceof Cigar, true);
        const vcigars = manager.sign({
            ser: serb,
            verfers: verfers,
            indexed: false,
        });
        assert.equal(vcigars.length, 1);
        const pcigs = Array.from(
            pcigars as Array<Cigar>,
            (psiger) => psiger.qb64
        );
        const vcigs = Array.from(
            vcigars as Array<Cigar>,
            (vsiger) => vsiger.qb64
        );
        assert.deepStrictEqual(vcigs, pcigs);
        assert.equal(
            pcigs[0],
            '0BCRPqO6vdXm1oSSa82rmVVHikf7NdN4JXjOWEk30Ub5JHChL0bW6DzJfA-7VlgLm_B1XR0Z61FweP87bBQpVawI'
        );

        let oldpubs = Array.from(verfers, (verfer) => verfer.qb64);
        let hashes = manager.rotate({ pre: spre });
        verfers = hashes[0];
        digers = hashes[1];

        assert.equal(verfers.length, 1);
        assert.equal(digers.length, 1);
        pp = manager.ks.getPrms(spre)!;
        assert.equal(pp.pidx, 0);
        assert.equal(pp.algo, Algos.salty);
        assert.equal(manager.decrypter!.decrypt(b(pp.salt)).qb64, salt);
        assert.equal(pp.stem, '');
        assert.equal(pp.tier, Tier.low);

        ps = manager.ks.getSits(spre)!;
        assert.deepStrictEqual(ps.old.pubs, [
            'DB-fH5uto5o5XHZjNN3_W3PdT4MIyTCmQWDzMxMZV2kI',
        ]);
        assert.equal(ps.new.pubs.length, 1);
        assert.deepStrictEqual(ps.new.pubs, [
            'DB-fH5uto5o5XHZjNN3_W3PdT4MIyTCmQWDzMxMZV2kI',
        ]);
        assert.equal(ps.new.ridx, 1);
        assert.equal(ps.new.kidx, 1);
        assert.equal(ps.nxt.pubs.length, 1);
        assert.deepStrictEqual(ps.nxt.pubs, [
            'DHHneREQ1eZyQNc5nEsQYx1FqFVL1OTXmvmatTE77Cfe',
        ]);
        assert.equal(ps.nxt.ridx, 2);
        assert.equal(ps.nxt.kidx, 2);

        keys = Array.from(verfers, (verfer: Verfer) => verfer.qb64);
        assert.deepStrictEqual(keys, ps.new.pubs);

        digs = Array.from(digers, (diger: Diger) => diger.qb64);
        assert.deepStrictEqual(digs, [
            'ECl1Env_5PQHqVMpHgoqg9H9mT7ENtk0Q499cmMT6Fvz',
        ]);

        assert.deepStrictEqual(oldpubs, ps.old.pubs);

        oldpubs = Array.from(verfers, (verfer: Verfer) => verfer.qb64);
        const deadpubs = ps.old.pubs;

        manager.rotate({ pre: spre });

        pp = manager.ks.getPrms(spre)!;
        assert.equal(pp.pidx, 0);

        ps = manager.ks.getSits(spre)!;
        assert.deepStrictEqual(oldpubs, ps.old.pubs);

        deadpubs.forEach((pub: string) => {
            assert.equal(manager.ks.getPris(pub, decrypter0), undefined);
        });

        pl = manager.ks.getPubs(riKey(spre, ps.new.ridx))!;
        assert.deepStrictEqual(pl.pubs, ps.new.pubs);

        pl = manager.ks.getPubs(riKey(spre, ps.nxt.ridx))!;
        assert.deepStrictEqual(pl.pubs, ps.nxt.pubs);

        hashes = manager.rotate({ pre: spre, ncount: 0 });
        digers = hashes[1];
        pp = manager.ks.getPrms(spre)!;
        assert.equal(pp.pidx, 0);

        ps = manager.ks.getSits(spre)!;
        assert.equal(ps.nxt.pubs.length, 0);
        assert.equal(digers.length, 0);

        assert.throws(() => {
            manager.rotate({ pre: spre });
        });

        // randy algo support
        hashes = manager.incept({ algo: Algos.randy });
        verfers = hashes[0];
        digers = hashes[1];

        assert.equal(verfers.length, 1);
        assert.equal(digers.length, 1);
        assert.equal(manager.pidx, 2);
        let rpre = verfers[0].qb64;

        pp = manager.ks.getPrms(rpre)!;
        assert.equal(pp.pidx, 1);
        assert.equal(pp.algo, Algos.randy);
        assert.equal(pp.salt, '');
        assert.equal(pp.stem, '');
        assert.equal(pp.tier, '');

        ps = manager.ks.getSits(rpre)!;
        assert.deepStrictEqual(ps.old.pubs, []);
        assert.equal(ps.new.pubs.length, 1);
        assert.deepStrictEqual(ps.new.pubs.length, 1);
        assert.equal(ps.new.ridx, 0);
        assert.equal(ps.new.kidx, 0);
        assert.equal(ps.nxt.pubs.length, 1);
        assert.equal(ps.nxt.ridx, 1);
        assert.equal(ps.nxt.kidx, 1);

        keys = Array.from(verfers, (verfer: Verfer) => verfer.qb64);
        keys.forEach((key) => {
            assert.notEqual(manager.ks.getPris(key, decrypter0), undefined);
        });

        const oldrpre = rpre;
        rpre = 'DMqxMVG3IcCNK4lpFfCu5o5cxzv1lgpMM-9rfkY3XVUc';
        manager.move(oldrpre, rpre);

        oldpubs = Array.from(verfers, (verfer: Verfer) => verfer.qb64);
        manager.rotate({ pre: rpre });

        pp = manager.ks.getPrms(rpre)!;
        assert.equal(pp.pidx, 1);
        ps = manager.ks.getSits(rpre)!;
        assert.deepStrictEqual(oldpubs, ps.old.pubs);

        // randy algo incept with null nxt
        hashes = manager.incept({ algo: Algos.randy, ncount: 0 });
        verfers = hashes[0];
        digers = hashes[1];

        assert.equal(manager.pidx, 3);
        rpre = verfers[0].qb64;

        pp = manager.ks.getPrms(rpre)!;
        assert.equal(pp.pidx, 2);

        ps = manager.ks.getSits(rpre)!;
        assert.deepStrictEqual(ps.nxt.pubs, []);
        assert.deepStrictEqual(digers, []);

        // attempt to rotate after null
        assert.throws(() => {
            manager.rotate({ pre: rpre });
        });

        // salty algorithm incept with stem
        hashes = manager.incept({ salt: salt, stem: stem, temp: true });
        verfers = hashes[0];
        digers = hashes[1];

        assert.equal(verfers.length, 1);
        assert.equal(digers.length, 1);
        assert.equal(manager.pidx, 4);

        spre = verfers[0].qb64;
        assert.equal(spre, 'DOtu4gX3oc4feusD8wWIykLhjkpiJHXEe29eJ2b_1CyM');

        pp = manager.ks.getPrms(spre)!;
        assert.equal(pp.pidx, 3);
        assert.equal(pp.algo, Algos.salty);
        assert.equal(manager.decrypter!.decrypt(b(pp.salt)).qb64, salt);
        assert.equal(pp.stem, 'red');
        assert.equal(pp.tier, Tier.low);

        ps = manager.ks.getSits(spre)!;
        assert.deepStrictEqual(ps.old.pubs, []);
        assert.equal(ps.new.pubs.length, 1);
        assert.deepStrictEqual(ps.new.pubs, [
            'DOtu4gX3oc4feusD8wWIykLhjkpiJHXEe29eJ2b_1CyM',
        ]);
        assert.equal(ps.new.ridx, 0);
        assert.equal(ps.new.kidx, 0);
        assert.equal(ps.nxt.pubs.length, 1);
        assert.deepStrictEqual(ps.nxt.pubs, [
            'DBzZ6vejSNAZpXv1SDRnIF_P1UqcW5d2pu2U-v-uhXvE',
        ]);
        assert.equal(ps.nxt.ridx, 1);
        assert.equal(ps.nxt.kidx, 1);

        keys = Array.from(verfers, (verfer: Verfer) => verfer.qb64);
        assert.deepStrictEqual(keys, ps.new.pubs);

        digs = Array.from(digers, (diger: Diger) => diger.qb64);
        assert.deepStrictEqual(digs, [
            'EIGjhyyBRcqCkPE9bmkph7morew0wW0ak-rQ-dHCH-M2',
        ]);

        hashes = manager.incept({
            ncount: 0,
            salt: salt,
            stem: 'wit0',
            transferable: false,
            temp: true,
        });
        verfers = hashes[0];
        digers = hashes[1];

        const witpre0 = verfers[0].qb64;
        assert.equal(
            verfers[0].qb64,
            'BOTNI4RzN706NecNdqTlGEcMSTWiFUvesEqmxWR_op8n'
        );
        assert.equal(verfers[0].code, MtrDex.Ed25519N);
        assert.notEqual(digers, undefined);

        hashes = manager.incept({
            ncount: 0,
            salt: salt,
            stem: 'wit1',
            transferable: false,
            temp: true,
        });
        verfers = hashes[0];
        digers = hashes[1];

        const witpre1 = verfers[0].qb64;
        assert.equal(
            verfers[0].qb64,
            'BAB_5xNXH4hoxDCtAHPFPDedZ6YwTo8mbdw_v0AOHOMt'
        );
        assert.equal(verfers[0].code, MtrDex.Ed25519N);
        assert.notEqual(digers, undefined);

        assert.notEqual(witpre0, witpre1);
    });

    it('should support only Salty/Encrypted, Salty/Unencrypted and Randy/Encrypted', async () => {
        await libsodium.ready;

        // Support Salty/Unencrypted - pass only stretched passcode as Salt.
        const passcode = '0123456789abcdefghijk';
        const salter = new Salter({ raw: b(passcode) });
        const salt = salter.qb64;

        const manager = new Manager({ salter: salter });
        assert.equal(manager.encrypter, undefined);

        let [verfers, digers] = manager.incept({ salt: salt, temp: true });
        assert.equal(verfers.length, 1);
        assert.equal(digers.length, 1);
        assert.equal(manager.pidx, 1);

        let spre = verfers[0].qb64;
        assert.equal(spre, 'DB-fH5uto5o5XHZjNN3_W3PdT4MIyTCmQWDzMxMZV2kI');
        let ps = manager.ks.getSits(spre)!;

        let keys = Array.from(verfers, (verfer: Verfer) => verfer.qb64);
        assert.deepStrictEqual(keys, ps.new.pubs);

        let pl = manager.ks.getPubs(riKey(spre, ps.new.ridx))!;
        assert.deepStrictEqual(pl.pubs, ps.new.pubs);
        pl = manager.ks.getPubs(riKey(spre, ps.nxt.ridx))!;
        assert.deepStrictEqual(pl.pubs, ps.nxt.pubs);

        let ppt = manager.ks.getPths(ps.new.pubs[0]);
        assert.equal(ppt!.path, '0');
        assert.equal(ppt!.code, 'A');
        assert.equal(ppt!.tier, 'low');
        assert.equal(ppt!.temp, true);

        let digs = Array.from(digers, (diger: Diger) => diger.qb64);
        assert.deepStrictEqual(digs, [
            'ENmcKrctbztF36MttN7seUYJqH2IMnkavBgGLR6Mj2-B',
        ]);

        const serb = b(ser);
        let psigers = manager.sign({ ser: serb, pubs: ps.new.pubs });
        assert.equal(psigers.length, 1);
        assert.equal(psigers[0] instanceof Siger, true);
        let vsigers = manager.sign({ ser: serb, verfers: verfers });
        let psigs = Array.from(
            psigers as Array<Siger>,
            (psiger) => psiger.qb64
        );
        let vsigs = Array.from(
            vsigers as Array<Siger>,
            (vsiger) => vsiger.qb64
        );
        assert.deepStrictEqual(psigs, vsigs);
        assert.equal(
            psigs[0],
            'AACRPqO6vdXm1oSSa82rmVVHikf7NdN4JXjOWEk30Ub5JHChL0bW6DzJfA-7VlgLm_B1XR0Z61FweP87bBQpVawI'
        );

        const oldspre = spre;
        spre = 'DCu5o5cxzv1lgMqxMVG3IcCNK4lpFfpMM-9rfkY3XVUc';
        manager.move(oldspre, spre);

        const oldpubs = Array.from(verfers, (verfer) => verfer.qb64);
        const hashes = manager.rotate({ pre: spre });
        verfers = hashes[0];
        digers = hashes[1];

        assert.equal(verfers.length, 1);
        assert.equal(digers.length, 1);
        const pp = manager.ks.getPrms(spre)!;
        assert.equal(pp.pidx, 0);
        assert.equal(pp.algo, Algos.salty);
        assert.equal(pp.salt, '');
        assert.equal(pp.stem, '');
        assert.equal(pp.tier, Tier.low);

        ps = manager.ks.getSits(spre)!;
        assert.deepStrictEqual(ps.old.pubs, [
            'DB-fH5uto5o5XHZjNN3_W3PdT4MIyTCmQWDzMxMZV2kI',
        ]);
        assert.equal(ps.new.pubs.length, 1);
        assert.deepStrictEqual(ps.new.pubs, [
            'DB-fH5uto5o5XHZjNN3_W3PdT4MIyTCmQWDzMxMZV2kI',
        ]);
        assert.equal(ps.new.ridx, 1);
        assert.equal(ps.new.kidx, 1);
        assert.equal(ps.nxt.pubs.length, 1);
        assert.deepStrictEqual(ps.nxt.pubs, [
            'DHHneREQ1eZyQNc5nEsQYx1FqFVL1OTXmvmatTE77Cfe',
        ]);
        assert.equal(ps.nxt.ridx, 2);
        assert.equal(ps.nxt.kidx, 2);

        keys = Array.from(verfers, (verfer: Verfer) => verfer.qb64);
        assert.deepStrictEqual(keys, ps.new.pubs);

        digs = Array.from(digers, (diger: Diger) => diger.qb64);
        assert.deepStrictEqual(digs, [
            'ECl1Env_5PQHqVMpHgoqg9H9mT7ENtk0Q499cmMT6Fvz',
        ]);

        assert.deepStrictEqual(oldpubs, ps.old.pubs);

        ppt = manager.ks.getPths(ps.new.pubs[0]);
        assert.equal(ppt!.path, '0');
        assert.equal(ppt!.code, 'A');
        assert.equal(ppt!.tier, 'low');
        assert.equal(ppt!.temp, true);

        psigers = manager.sign({ ser: serb, pubs: ps.new.pubs });
        assert.equal(psigers.length, 1);
        assert.equal(psigers[0] instanceof Siger, true);
        vsigers = manager.sign({ ser: serb, verfers: verfers });
        psigs = Array.from(psigers as Array<Siger>, (psiger) => psiger.qb64);
        vsigs = Array.from(vsigers as Array<Siger>, (vsiger) => vsiger.qb64);
        assert.deepStrictEqual(psigs, vsigs);
        assert.equal(
            psigs[0],
            'AACRPqO6vdXm1oSSa82rmVVHikf7NdN4JXjOWEk30Ub5JHChL0bW6DzJfA-7VlgLm_B1XR0Z61FweP87bBQpVawI'
        );
    });

    it('Should support creating and getting randy keeper', async () => {
        const passcode = '0123456789abcdefghijk';
        const salter = new Salter({ raw: b(passcode) });

        const manager = new KeyManager(salter, []);

        const keeper0 = manager.new(Algos.randy, 0, {}) as RandyKeeper;
        const [keys] = await keeper0.incept(false);
        const prefixes = new Prefixer({ qb64: keys[0] });

        const keeper1 = manager.get({
            prefix: prefixes.qb64,
            name: '',
            state: {} as State,
            randy: keeper0.params() as RandyState,
            transferable: false,
            windexes: [],
        });

        assert(keeper0 instanceof RandyKeeper);
        assert(keeper1 instanceof RandyKeeper);
    });

    it('Should throw if algo is not supported', async () => {
        const passcode = '0123456789abcdefghijk';
        const salter = new Salter({ raw: b(passcode) });

        const manager = new KeyManager(salter, []);

        expect(() => manager.new(randomUUID() as Algos, 0, {})).toThrow(
            'Unknown algo'
        );
        expect(() =>
            manager.get({
                prefix: '',
                name: '',
                state: {} as State,
                transferable: false,
                windexes: [],
            })
        ).toThrow('Algo not allowed yet');
    });

    describe('External Module ', () => {
        class MockModule implements jest.Mocked<Keeper> {
            #params: Record<string, unknown>;

            constructor(
                public pidx: number,
                params: KeeperParams
            ) {
                this.#params = params;
            }

            signers: Signer[] = [];
            sign = jest.fn();
            algo: Algos = Algos.extern;
            incept = jest.fn();
            rotate = jest.fn();
            params = jest.fn(() => this.#params);
        }

        it('Should support creating external keeper module', async () => {
            const passcode = '0123456789abcdefghijk';
            const salter = new Salter({ raw: b(passcode) });

            const manager = new KeyManager(salter, [
                { module: MockModule, name: 'mock', type: 'mock' },
            ]);

            const param = randomUUID();
            const keeper = manager.new(Algos.extern, 0, {
                extern_type: 'mock',
                param,
            });

            assert(keeper instanceof MockModule);
            expect(keeper.params()).toMatchObject({ param });
        });

        it('Should throw if external keeper module is not addede', async () => {
            const passcode = '0123456789abcdefghijk';
            const salter = new Salter({ raw: b(passcode) });

            const manager = new KeyManager(salter, []);

            const param = randomUUID();
            expect(() =>
                manager.new(Algos.extern, 0, {
                    extern_type: 'mock',
                    param,
                })
            ).toThrow('unsupported external module type mock');
        });

        it('Should support getting external keeper module', async () => {
            const passcode = '0123456789abcdefghijk';
            const salter = new Salter({ raw: b(passcode) });

            const manager = new KeyManager(salter, [
                { module: MockModule, name: 'mock', type: 'mock' },
            ]);

            const param = randomUUID();

            const keeper = manager.get({
                name: randomUUID(),
                prefix: '',
                state: {} as unknown as State,
                windexes: [],
                extern: {
                    extern_type: 'mock',
                    pidx: 3,
                    param,
                },
                transferable: true,
            });

            assert(keeper instanceof MockModule);
            expect(keeper.params()).toMatchObject({ param, pidx: 3 });
        });

        it('Should throw when trying to get external keeper that is not registered', async () => {
            const passcode = '0123456789abcdefghijk';
            const salter = new Salter({ raw: b(passcode) });

            const manager = new KeyManager(salter, []);

            const param = randomUUID();

            expect(() =>
                manager.get({
                    name: randomUUID(),
                    prefix: '',
                    state: {} as unknown as State,
                    windexes: [],
                    extern: {
                        extern_type: 'mock',
                        pidx: 3,
                        param,
                    },
                    transferable: true,
                })
            ).toThrow('unsupported external module type mock');
        });
    });
});
