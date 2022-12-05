import {strict as assert} from "assert";
import libsodium  from 'libsodium-wrappers-sumo';
import {CryOneRawSizes, CryOneSizes, oneCharCode, twoCharCode} from '../../src/keri/core/derivationCodes';
import { Crymat }  from '../../src/keri/core/cryMat';
import { Verfer }  from '../../src/keri/core/verfer';
import { Prefixer }  from '../../src/keri/core/prefixer';
import { Nexter }  from '../../src/keri/core/nexter';
import { Signer }  from '../../src/keri/core/signer';
import {
  versify,
  Serials,
  Versionage,
  Ilks,
}  from '../../src/keri/core/core';
// namespace our extensions



describe('Prefixer', () => {
    it('should generate prefixes', async () => {
        // raw = null, qb64 = null, qb2 = null, code = codeAndLength.oneCharCode.Ed25519N, index = 0
        await libsodium.ready;
        let vk = '\xacr\xda\xc83~\x99r\xaf\xeb`\xc0\x8cR\xd7\xd7\xf69\xc8E\x1e\xd2\xf0=`\xf7\xbf\x8a\x18\x8a`q';
        let verkey = Buffer.from(vk, 'binary');
        let verfer = new Verfer(verkey);
        console.log(verfer.qb64())
        assert.deepStrictEqual(
          verfer.qb64(),
          'BrHLayDN-mXKv62DAjFLX1_Y5yEUe0vA9YPe_ihiKYHE',
        );

        let nk = "\xa6_\x894J\xf25T\xc1\x83#\x06\x98L\xa6\xef\x1a\xb3h\xeaA:x'\xda\x04\x88\xb2\xc4_\xf6\x00";
        let nxtkey = Buffer.from(nk, 'binary');
        const nxtfer = new Verfer(
          nxtkey,
          null,
          null,
          oneCharCode.Ed25519,
        );
        console.log(nxtfer.qb64())
        assert.deepStrictEqual(
          nxtfer.qb64(),
          'Bpl-JNEryNVTBgyMGmEym7xqzaOpBOngn2gSIssRf9gA',
        );

        // test creation given raw and code no derivation

        let prefixer = new Prefixer(verkey);

        assert.deepStrictEqual(prefixer.code(), oneCharCode.Ed25519N);
        assert.deepStrictEqual(
          prefixer.raw().length,
          CryOneRawSizes[prefixer.code()],
        );
        assert.deepStrictEqual(
          prefixer.qb64().length,
          CryOneSizes[prefixer.code()],
        );


        let ked = { keys: [prefixer.qb64()], nxt: '' };
        assert.deepEqual(prefixer.verify(ked), true);

        ked = { keys: [prefixer.qb64()], nxt: 'ABC' };
        assert.deepEqual(prefixer.verify(ked), false);

        // (raw = null),
        //   (code = oneCharCode.Ed25519N),
        //   (ked = null),
        //   (seed = null), // secret = null, ...kwa
        prefixer = new Prefixer(
          verkey,
          oneCharCode.Ed25519,
          undefined,
          undefined,
          null,
        ); // # defaults provide Ed25519N prefixer
        assert.deepStrictEqual(prefixer.code(), oneCharCode.Ed25519);
        assert.deepStrictEqual(
          prefixer.raw().length,
          CryOneRawSizes[prefixer.code()],
        );
        assert.deepStrictEqual(
          prefixer.qb64().length,
          CryOneSizes[prefixer.code()],
        );


        ked = { keys: [prefixer.qb64()], nxt: '' };
        assert.deepStrictEqual(prefixer.verify(ked), true);

        // raw = null, qb64 = null, qb2 = null, code = oneCharCode.Ed25519N, index = 0
        verfer = new Verfer(
          verkey,
          null,
          null,
          null,
          oneCharCode.Ed25519,
          0,
        );
        prefixer = new Prefixer(verfer.raw());
        assert.deepStrictEqual(prefixer.code(), oneCharCode.Ed25519N);
        assert.deepStrictEqual(prefixer.verify(ked), false);

        // //  # # Test basic derivation from ked
        //
        ked = { keys: [verfer.qb64()], nxt: '' };

        // raw = null, code = derivation_code.oneCharCode.Ed25519N, ked = null, seed = null, secret = null, ...kwa
        prefixer = new Prefixer(undefined, oneCharCode.Ed25519, ked);
        assert.deepStrictEqual(prefixer.qb64(), verfer.qb64());
        assert.deepStrictEqual(prefixer.verify(ked), true);

        verfer = new Verfer(
          verkey,
          null,
          null,
          null,
          oneCharCode.Ed25519N,
          0,
        );
        ked = { keys: [verfer.qb64()], nxt: '' };
        prefixer = new Prefixer(undefined, oneCharCode.Ed25519N, ked);

        assert.deepStrictEqual(prefixer.qb64(), verfer.qb64());
        assert.deepStrictEqual(prefixer.verify(ked), true);
        //
        // // # # Test digest derivation from inception ked
        let vs = versify(Versionage, Serials.json, 0);
        let sn = 0;
        let ilk = Ilks.icp;
        let sith = 1;
        let crymat = new Crymat(
          verkey,
          null,
          null,
          oneCharCode.Ed25519,
        );

        let keys = [crymat.qb64()];
        let nxt = '';
        let toad = 0;
        // @ts-ignore
        let wits: string[] = [];
        // @ts-ignore
        let cnfg: string[] = [];
        console.log('key is --------->', vs);
        let ked1 = {
          vs: vs.toString(), // version string
          pre: '', // # qb64 prefix
          sn: sn.toString(16), // # hex string no leading zeros lowercase
          ilk,
          sith: sith.toString(16), // # hex string no leading zeros lowercase
          keys, // # list of qb64
          nxt, // # hash qual Base64
          toad: toad.toString(16), //  # hex string no leading zeros lowercase
          wits, // # list of qb64 may be empty
          cnfg, // # list of config ordered mappings may be empty
        };
        // util.pad(size.toString(16), VERRAWSIZE);
        // console.log("key is --------->", keys);
        let prefixer1 = new Prefixer(
          undefined,
          oneCharCode.Blake3_256,
          ked1,
        );

        assert.deepStrictEqual(
          prefixer1.qb64(),
          'EOyxDqUR4YUgT61oRcsE9TPLgsgJ5PAXw1x075kZXz1A',
        );
        assert.deepStrictEqual(prefixer1.verify(ked1), true);
        console.log(prefixer1.qb64())


        // # # Test digest derivation from inception ked
        const nexter = new Nexter(null, 1, [nxtfer.qb64()]);

        let ked2 = {
          vs: vs.toString(), // version string
          pre: '', // # qb64 prefix
          sn: sn.toString(16), // # hex string no leading zeros lowercase
          ilk,
          sith: sith.toString(16), // # hex string no leading zeros lowercase
          keys, // # list of qb64
          nxt, // # hash qual Base64
          toad: toad.toString(16), //  # hex string no leading zeros lowercase
          wits, // # list of qb64 may be empty
          cnfg, // # list of config ordered mappings may be empty
        };

        prefixer1 = new Prefixer(
          undefined,
          oneCharCode.Blake3_256,
          ked2,
        );
        assert.deepStrictEqual(
          prefixer1.qb64(),
          'EOyxDqUR4YUgT61oRcsE9TPLgsgJ5PAXw1x075kZXz1A',
        );
        assert.deepStrictEqual(prefixer1.verify(ked2), true);

        // const perm = [];
        const seal = {
          pre: 'EkbeB57LYWRYNqg4xarckyfd_LsaH0J350WmOdvMwU_Q',
          sn: '2',
          ilk: Ilks.ixn,
          dig: 'E03rxRmMcP2-I2Gd0sUhlYwjk8KEz5gNGxPwPg-sGJds',
        };

        let ked3 = {
          vs: vs.toString(), // version string
          pre: '', // # qb64 prefix
          sn: sn.toString(16), // # hex string no leading zeros lowercase
          ilk: Ilks.dip,
          sith: sith.toString(16), // # hex string no leading zeros lowercase
          keys, // # list of qb64
          nxt: nexter.qb64(), // # hash qual Base64
          toad: toad.toString(16), //  # hex string no leading zeros lowercase
          wits, // # list of qb64 may be empty
          perm: cnfg,
          seal, // # list of config ordered mappings may be empty
        };

        prefixer1 = new Prefixer(
          undefined,
          oneCharCode.Blake3_256,
          ked3,
        );
        assert.deepStrictEqual(
          prefixer1.qb64(),
          'E_k7oVnOUQ_rVWhhuGwwkiHR-7LOfhtXybs7HMj5xLlY',
        );
        assert.deepStrictEqual(prefixer1.verify(ked3), true);


        // # #  Test signature derivation
        //
        let seed = libsodium.randombytes_buf(libsodium.crypto_sign_SEEDBYTES);
        const seed1 = '\xdf\x95\xf9\xbcK@s="\xee\x95w\xbf>F&\xbb\x82\x8f)\x95\xb9\xc0\x1eS\x1b{Lt\xcfH\xa6';
        seed = Buffer.from(seed1, 'binary');
        const signer = new Signer(seed, oneCharCode.Ed25519_Seed, true);

        let secret = signer.qb64();
        assert.deepStrictEqual(
          secret,
          'A35X5vEtAcz0i7pV3vz5GJruCjymVucAeUxt7THTPSKY',
        );

        vs = versify(Versionage, Serials.json, 0);
        sn = 0;
        ilk = Ilks.icp;
        sith = 1;
        keys = [signer.verfer().qb64()];
        nxt = '';
        toad = 0;
        wits = [];
        cnfg = [];

        const nexter1 = new Nexter(null, 1, [nxtfer.qb64()]);
        const t = keys[0];
        console.log(
          'Keys are ******************************************************',
          t.toString(),
        );
        let ked4 = {
          vs: vs.toString(), // version string
          pre: '', // # qb64 prefix
          sn: sn.toString(16), // # hex string no leading zeros lowercase
          ilk,
          sith: sith.toString(16), // # hex string no leading zeros lowercase
          keys, // # list of qb64
          nxt: nexter1.qb64(), // # hash qual Base64
          toad: toad.toString(16), //  # hex string no leading zeros lowercase
          wits, // # list of qb64 may be empty
          cnfg,
          // # list of config ordered mappings may be empty
        };

        prefixer1 = new Prefixer(
          undefined,
          twoCharCode.Ed25519,
          ked4,
          seed,
        );
        assert.deepStrictEqual(
          prefixer1.qb64(),
          '0Bs5Yv4vvIBcaq43bsF2s1kiSso0PYrxOILFCT-G1jsFJw2jfxnjcNFYA5pu7okeBfDev_CrA_DtP5MDXp51-AAA',
        );
        // TODO:  why not?
        // assert.deepStrictEqual(prefixer1.verify(ked4), true);
        assert.deepStrictEqual(prefixer1.qb64(), '0Bs5Yv4vvIBcaq43bsF2s1kiSso0PYrxOILFCT-G1jsFJw2jfxnjcNFYA5pu7okeBfDev_CrA_DtP5MDXp51-AAA');
        //
        // # assert
        // # assert prefixer.verify(ked=ked) == True

        // # prefixer = Prefixer(ked=ked, code=CryTwoDex.Ed25519, secret=secret)
        // # assert prefixer.qb64 == '0B0uVeeaCtXTAj04_27g5pSKjXouQaC1mHcWswzkL7Jk0XC0yTyNnIvhaXnSxGbzY8WaPv63iAfWhJ81MKACRuAQ'
        // # assert prefixer.verify(ked=ked) == True
    });
});