import libsodium from "libsodium-wrappers-sumo";
import {Algos, Creatory, Manager, RandyCreator, riKey, SaltyCreator} from "../../src/keri/core/manager";
import {strict as assert} from "assert";
import {MtrDex} from "../../src/keri/core/matter";
import {Salter, Tier} from "../../src/keri/core/salter";
import {Signer} from "../../src/keri/core/signer";
import {Encrypter} from "../../src/keri/core/encrypter";
import {Decrypter} from "../../src/keri/core/decrypter";
import {Cipher} from "../../src/keri/core/cipher";
import {Verfer} from "../../src/keri/core/verfer";
import {Diger} from "../../src/keri/core/diger";
import {Siger} from "../../src/keri/core/siger";
import {b} from "../../src/keri/core/core";
import {Cigar} from "../../src/keri/core/cigar";


describe('RandyCreator', () => {
    it('should create sets of random signers', async () => {
        await libsodium.ready;

        let randy = new RandyCreator()

        // test default arguments
        let signers = randy.create()
        assert.equal(signers.length, 1)
        assert.equal(signers[0].qb64.length, 44)
        assert.equal(signers[0].code, MtrDex.Ed25519_Seed)
        assert.equal(signers[0].transferable, true)

        // Create 5 with default code
        signers = randy.create(undefined, 5)
        assert.equal(signers.length, 5)
        signers.forEach((signer) => {
            assert.equal(signer.qb64.length, 44)
            assert.equal(signer.code, MtrDex.Ed25519_Seed)
            assert.equal(signer.transferable, true)
        })

        // Create 3 with specified codes (the only one we support)
        signers = randy.create([MtrDex.Ed25519_Seed, MtrDex.Ed25519_Seed, MtrDex.Ed25519_Seed])
        assert.equal(signers.length, 3)
        signers.forEach((signer) => {
            assert.equal(signer.qb64.length, 44)
            assert.equal(signer.code, MtrDex.Ed25519_Seed)
            assert.equal(signer.transferable, true)
        })
    })
})


describe('SaltyCreator', () => {
    it('should create sets of salty signers', async () => {
        await libsodium.ready;

        // Test default arguments
        let salty = new SaltyCreator()
        assert.equal(salty.salter.code, MtrDex.Salt_128)
        assert.equal(salty.salt, salty.salter.qb64)
        assert.equal(salty.stem, "")
        assert.equal(salty.tier, salty.salter.tier)

        let signers = salty.create()
        assert.equal(signers.length, 1)
        assert.equal(signers[0].qb64.length, 44)
        assert.equal(signers[0].code, MtrDex.Ed25519_Seed)
        assert.equal(signers[0].transferable, true)

        signers = salty.create(undefined, 2, MtrDex.Ed25519_Seed, false)
        assert.equal(signers.length, 2)
        signers.forEach((signer) => {
            assert.equal(signer.code, MtrDex.Ed25519_Seed)
            assert.equal(signer.verfer.code, MtrDex.Ed25519N)
            assert.equal(signer.qb64.length, 44)
        })

        let raw = "0123456789abcdef"
        let salter = new Salter({raw: b(raw)})
        let salt = salter.qb64
        assert.equal(salter.qb64, "0AAwMTIzNDU2Nzg5YWJjZGVm")
        salty = new SaltyCreator(salter.qb64)
        assert.equal(salty.salter.code, MtrDex.Salt_128)
        assert.deepStrictEqual(salty.salter.raw, b(raw))
        assert.equal(salty.salter.qb64, salt)
        assert.equal(salty.salt, salty.salter.qb64)
        assert.equal(salty.stem, "")
        assert.equal(salty.tier, salty.salter.tier)
        signers = salty.create()
        assert.equal(signers.length, 1)
        assert.equal(signers[0].code, MtrDex.Ed25519_Seed)
        assert.equal(signers[0].qb64, "APMJe0lwOpwnX9PkvX1mh26vlzGYl6RWgWGclc8CAQJ9")
        assert.equal(signers[0].verfer.code, MtrDex.Ed25519)
        assert.equal(signers[0].verfer.qb64, "DMZy6qbgnKzvCE594tQ4SPs6pIECXTYQBH7BkC4hNY3E")

        signers = salty.create(undefined, 1, MtrDex.Ed25519_Seed, false, 0, 0, 0, true)
        assert.equal(signers.length, 1)
        assert.equal(signers[0].code, MtrDex.Ed25519_Seed)
        assert.equal(signers[0].qb64, "AMGrAM0noxLpRteO9mxGT-yzYSrKFwJMuNI4KlmSk26e")
        assert.equal(signers[0].verfer.code, MtrDex.Ed25519N)
        assert.equal(signers[0].verfer.qb64, "BFRtyHAjSuJaRX6TDPva35GN11VHAruaOXMc79ZYDKsT")

    })
})

describe('Creator', () => {
    it('should create Randy or Salty creator', async () => {
        await libsodium.ready;

        let raw = "0123456789abcdef"
        let salter = new Salter({raw: b(raw)})
        let salt = salter.qb64

        let creator = new Creatory(Algos.salty).make(salt)
        assert.equal(creator instanceof SaltyCreator, true)
        assert.equal(creator.salter.qb64, salt)

        creator = new Creatory().make(salt)
        assert.equal(creator instanceof SaltyCreator, true)
        assert.equal(creator.salter.qb64, salt)

        creator = new Creatory(Algos.randy).make(salt)
        assert.equal(creator instanceof RandyCreator, true)
    })
})

describe('Manager', () => {
    it('should manage key pairs for identifiers', async () => {
        await libsodium.ready;

        let ser = '{"vs":"KERI10JSON0000fb_","pre":"EvEnZMhz52iTrJU8qKwtDxzmypyosgG' +
        '70m6LIjkiCdoI","sn":"0","ilk":"icp","sith":"1","keys":["DSuhyBcP' +
        'ZEZLK-fcw5tzHn2N46wRCG_ZOoeKtWTOunRA"],"nxt":"EPYuj8mq_PYYsoBKkz' +
        'X1kxSPGYBWaIya3slgCOyOtlqU","toad":"0","wits":[],"cnfg":[]}-AABA' +
        'ApYcYd1cppVg7Inh2YCslWKhUwh59TrPpIoqWxN2A38NCbTljvmBPBjSGIFDBNOv' +
        'VjHpdZlty3Hgk6ilF8pVpAQ'

        let raw = "0123456789abcdef"
        let salter = new Salter({raw: b(raw)})
        let salt = salter.qb64
        assert.equal(salt, "0AAwMTIzNDU2Nzg5YWJjZGVm")
        let stem = "red"


        // Create a Manager without encryption should raise an exception
        assert.throws(() => {
            new Manager({salt: salt})
        })

        // cryptseed0 = b('h,#|\x8ap"\x12\xc43t2\xa6\xe1\x18\x19\xf0f2,y\xc4\xc21@\xf5@\x15.\xa2\x1a\xcf')
        let cryptseed0 = new Uint8Array([104, 44, 35, 124, 138, 112, 34, 18, 196, 51, 116, 50, 166, 225, 24, 25, 240, 102, 50, 44, 121, 196, 194, 49, 64, 245, 64, 21, 46, 162, 26, 207])
        let cryptsigner0 = new Signer({raw: cryptseed0, code: MtrDex.Ed25519_Seed, transferable: false})
        let seed0 = cryptsigner0.qb64
        let seed0b = cryptsigner0.qb64b
        let aeid0 = cryptsigner0.verfer.qb64
        assert.equal(aeid0, "BCa7mK96FwxkU0TdF54Yqg3qBDXUWpOhQ_Mtr7E77yZB")
        let decrypter0 = new Decrypter({}, seed0b)
        let encrypter0 = new Encrypter({}, b(aeid0))
        assert.equal(encrypter0.verifySeed(seed0b), true)

        // cryptseed1 = (b"\x89\xfe{\xd9'\xa7\xb3\x89#\x19\xbec\xee\xed\xc0\xf9\x97\xd0\x8f9\x1dyNI"
        //                b'I\x98\xbd\xa4\xf6\xfe\xbb\x03')
        let cryptseed1 = new Uint8Array([137, 254, 123, 217, 39, 167, 179, 137, 35, 25, 190, 99, 238, 237, 192, 249, 151, 208, 143, 57, 29, 121, 78, 73, 73, 152, 189, 164, 246, 254, 187, 3])
        let cryptsigner1 = new Signer({raw: cryptseed1, code: MtrDex.Ed25519_Seed, transferable: false})
        let seed1 = cryptsigner1.qb64b
        let aeid1 = cryptsigner1.verfer.qb64
        assert.equal(aeid1, "BEcOrMrG_7r_NWaLl6h8UJapwIfQWIkjrIPXkCZm2fFM")
        // let decrypter1 = new Decrypter({}, seed1)
        let encrypter1 = new Encrypter({}, b(aeid1))
        assert.equal(encrypter1.verifySeed(seed1), true)

        let manager = new Manager({seed: seed0, salt: salt, aeid: aeid0})
        assert.equal(manager.encrypter.qb64, encrypter0.qb64)
        assert.equal(manager.decrypter.qb64, decrypter0.qb64)
        assert.equal(manager.seed, seed0)
        assert.equal(manager.aeid, aeid0)

        assert.equal(manager.algo, Algos.salty)
        assert.equal(manager.salt, salt)
        assert.equal(manager.pidx, 0)
        assert.equal(manager.tier, Tier.low)
        let saltCipher0 = new Cipher({qb64: manager.ks.getGbls("salt")})
        assert.equal(saltCipher0.decrypt(undefined, seed0b).qb64, salt)

        let [verfers, digers] = manager.incept({salt: salt, temp: true})
        assert.equal(verfers.length, 1)
        assert.equal(digers.length, 1)
        assert.equal(manager.pidx, 1)

        let spre = verfers[0].qb64
        assert.equal(spre, "DFRtyHAjSuJaRX6TDPva35GN11VHAruaOXMc79ZYDKsT")

        let pp = manager.ks.getPrms(spre)!
        assert.equal(pp.pidx, 0)
        assert.equal(pp.algo, Algos.salty)
        assert.equal(manager.decrypter.decrypt(b(pp.salt)).qb64, salt)
        assert.equal(pp.stem, "")
        assert.equal(pp.tier, Tier.low)

        let ps = manager.ks.getSits(spre)!
        assert.deepStrictEqual(ps.old.pubs, [])
        assert.equal(ps.new.pubs.length, 1)
        assert.deepStrictEqual(ps.new.pubs, ['DFRtyHAjSuJaRX6TDPva35GN11VHAruaOXMc79ZYDKsT'])
        assert.equal(ps.new.ridx, 0)
        assert.equal(ps.new.kidx, 0)
        assert.equal(ps.nxt.pubs.length, 1)
        assert.deepStrictEqual(ps.nxt.pubs, ['DHByVjuBrM1D9K71TuE5dq1HVDNS5-aLD-wcIlHiVoXX'])
        assert.equal(ps.nxt.ridx, 1)
        assert.equal(ps.nxt.kidx, 1)

        let keys = Array.from(verfers, (verfer: Verfer) => verfer.qb64)
        assert.deepStrictEqual(keys, ps.new.pubs)

        let pl = manager.ks.getPubs(riKey(spre, ps.new.ridx))!
        assert.deepStrictEqual(pl.pubs, ps.new.pubs)
        pl = manager.ks.getPubs(riKey(spre, ps.nxt.ridx))!
        assert.deepStrictEqual(pl.pubs, ps.nxt.pubs)

        let digs = Array.from(digers, (diger: Diger) => diger.qb64)
        assert.deepStrictEqual(digs, ['EBhBRqVbqhhP7Ciah5pMIOdsY5Mm1ITm2Fjqb028tylu'])

        let oldspre = spre
        spre = "DCu5o5cxzv1lgMqxMVG3IcCNK4lpFfpMM-9rfkY3XVUc"
        manager.move(oldspre, spre)

        pl = manager.ks.getPubs(riKey(spre, ps.new.ridx))!
        assert.deepStrictEqual(pl.pubs, ps.new.pubs)
        pl = manager.ks.getPubs(riKey(spre, ps.nxt.ridx))!
        assert.deepStrictEqual(pl.pubs, ps.nxt.pubs)

        let serb = b(ser)
        let psigers = manager.sign({ser: serb, pubs: ps.new.pubs})
        assert.equal(psigers.length, 1)
        assert.equal(psigers[0] instanceof Siger, true)
        let vsigers = manager.sign({ser: serb, verfers: verfers})
        let psigs = Array.from(psigers as Array<Siger>, (psiger) => psiger.qb64)
        let vsigs = Array.from(vsigers as Array<Siger>, (vsiger) => vsiger.qb64)
        assert.deepStrictEqual(psigs, vsigs)
        assert.equal(psigs[0], 'AAAa70b4QnTOtGOsMqcezMtVzCFuRJHGeIMkWYHZ5ZxGIXM0XDVAzkYdCeadfPfzlKC6dkfiwuJ0IzLOElaanUgH')

        // Test sign with indices
        let indices = [3]
        psigers = manager.sign({ser: serb, pubs: ps.new.pubs, indices: indices}) as Array<Siger>
        assert.equal(psigers.length, 1)
        assert.equal(psigers[0] instanceof Siger, true)
        assert.equal(psigers[0].index, indices[0])
        psigs = Array.from(psigers as Array<Siger>, (psiger) => psiger.qb64)
        assert.equal(psigs[0], 'ADAa70b4QnTOtGOsMqcezMtVzCFuRJHGeIMkWYHZ5ZxGIXM0XDVAzkYdCeadfPfzlKC6dkfiwuJ0IzLOElaanUgH')

        vsigers = manager.sign({ser: serb, verfers: verfers, indices: indices}) as Array<Siger>
        assert.equal(vsigers.length, 1)
        assert.equal(vsigers[0] instanceof Siger, true)
        assert.equal(vsigers[0].index, indices[0])
        vsigs = Array.from(vsigers as Array<Siger>, (vsiger) => vsiger.qb64)
        assert.deepStrictEqual(psigs, vsigs)

        let pcigars = manager.sign({ser: serb, pubs: ps.new.pubs, indexed: false})
        assert.equal(pcigars.length, 1)
        assert.equal(pcigars[0] instanceof Cigar, true)
        let vcigars = manager.sign({ser: serb, verfers: verfers, indexed: false})
        assert.equal(vcigars.length , 1)
        let pcigs = Array.from(pcigars as Array<Cigar>, (psiger) => psiger.qb64)
        let vcigs = Array.from(vcigars as Array<Cigar>, (vsiger) => vsiger.qb64)
        assert.deepStrictEqual(vcigs, pcigs)
        assert.equal(pcigs[0], '0BAa70b4QnTOtGOsMqcezMtVzCFuRJHGeIMkWYHZ5ZxGIXM0XDVAzkYdCeadfPfzlKC6dkfiwuJ0IzLOElaanUgH')

        let oldpubs = Array.from(verfers, (verfer) => verfer.qb64)
        let hashes = manager.rotate({pre: spre})
        verfers = hashes[0]
        digers = hashes[1]

        assert.equal(verfers.length, 1)
        assert.equal(digers.length, 1)
        pp = manager.ks.getPrms(spre)!
        assert.equal(pp.pidx, 0)
        assert.equal(pp.algo, Algos.salty)
        assert.equal(manager.decrypter.decrypt(b(pp.salt)).qb64, salt)
        assert.equal(pp.stem, '')
        assert.equal(pp.tier, Tier.low)

        ps = manager.ks.getSits(spre)!
        assert.deepStrictEqual(ps.old.pubs, ['DFRtyHAjSuJaRX6TDPva35GN11VHAruaOXMc79ZYDKsT'])
        assert.equal(ps.new.pubs.length, 1)
        assert.deepStrictEqual(ps.new.pubs, ['DHByVjuBrM1D9K71TuE5dq1HVDNS5-aLD-wcIlHiVoXX'])
        assert.equal(ps.new.ridx, 1)
        assert.equal(ps.new.kidx, 1)
        assert.equal(ps.nxt.pubs.length, 1)
        assert.deepStrictEqual(ps.nxt.pubs, ['DAoQ1WxT29XtCFtOpJZyuO2q38BD8KTefktf7X0WN4YW'])
        assert.equal(ps.nxt.ridx, 2)
        assert.equal(ps.nxt.kidx, 2)

        keys = Array.from(verfers, (verfer: Verfer) => verfer.qb64)
        assert.deepStrictEqual(keys, ps.new.pubs )

        digs = Array.from(digers, (diger: Diger) => diger.qb64)
        assert.deepStrictEqual(digs, ['EJczV8HmnEWZiEHw2lVuSatrvzCmJOZ3zpa7JFfrnjau'])

        assert.deepStrictEqual(oldpubs, ps.old.pubs)

        oldpubs = Array.from(verfers, (verfer: Verfer) => verfer.qb64)
        let deadpubs = ps.old.pubs

        manager.rotate({pre: spre})

        pp = manager.ks.getPrms(spre)!
        assert.equal(pp.pidx, 0)

        ps = manager.ks.getSits(spre)!
        assert.deepStrictEqual(oldpubs, ps.old.pubs)

        deadpubs.forEach((pub: string) => {
            assert.notEqual(manager.ks.getPris(pub, decrypter0), undefined)
        })

        pl = manager.ks.getPubs(riKey(spre, ps.new.ridx))!
        assert.deepStrictEqual(pl.pubs, ps.new.pubs)

        pl = manager.ks.getPubs(riKey(spre, ps.nxt.ridx))!
        assert.deepStrictEqual(pl.pubs, ps.nxt.pubs)

        hashes = manager.rotate({pre: spre, ncount: 0})
        digers = hashes[1]
        pp = manager.ks.getPrms(spre)!
        assert.equal(pp.pidx, 0)

        ps = manager.ks.getSits(spre)!
        assert.equal(ps.nxt.pubs.length, 0)
        assert.equal(digers.length, 0)

        assert.throws(() => {
            manager.rotate({pre: spre})
        })

        // randy algo support
        hashes = manager.incept({algo: Algos.randy})
        verfers = hashes[0]
        digers = hashes[1]

        assert.equal(verfers.length, 1)
        assert.equal(digers.length, 1)
        assert.equal(manager.pidx, 2)
        let rpre = verfers[0].qb64

        pp = manager.ks.getPrms(rpre)!
        assert.equal(pp.pidx, 1)
        assert.equal(pp.algo, Algos.randy)
        assert.equal(pp.salt, '')
        assert.equal(pp.stem, '')
        assert.equal(pp.tier, '')

        ps = manager.ks.getSits(rpre)!
        assert.deepStrictEqual(ps.old.pubs, [])
        assert.equal(ps.new.pubs.length, 1)
        assert.deepStrictEqual(ps.new.pubs.length, 1)
        assert.equal(ps.new.ridx, 0)
        assert.equal(ps.new.kidx, 0)
        assert.equal(ps.nxt.pubs.length, 1)
        assert.equal(ps.nxt.ridx, 1)
        assert.equal(ps.nxt.kidx, 1)

        keys = Array.from(verfers, (verfer: Verfer) => verfer.qb64)
        keys.forEach((key) => {
            assert.notEqual(manager.ks.getPris(key, decrypter0), undefined)
        })

        let oldrpre = rpre
        rpre = 'DMqxMVG3IcCNK4lpFfCu5o5cxzv1lgpMM-9rfkY3XVUc'
        manager.move(oldrpre, rpre)

        oldpubs = Array.from(verfers, (verfer: Verfer) => verfer.qb64)
        manager.rotate({pre: rpre})

        pp = manager.ks.getPrms(rpre)!
        assert.equal(pp.pidx, 1)
        ps = manager.ks.getSits(rpre)!
        assert.deepStrictEqual(oldpubs, ps.old.pubs)

        // randy algo incept with null nxt
        hashes = manager.incept({algo: Algos.randy, ncount: 0})
        verfers = hashes[0]
        digers = hashes[1]

        assert.equal(manager.pidx, 3)
        rpre = verfers[0].qb64

        pp = manager.ks.getPrms(rpre)!
        assert.equal(pp.pidx, 2)

        ps = manager.ks.getSits(rpre)!
        assert.deepStrictEqual(ps.nxt.pubs, [])
        assert.deepStrictEqual(digers, [])

        // attempt to rotate after null
        assert.throws(() => {
            manager.rotate({pre: rpre})
        })

        // salty algorithm incept with stem
        hashes = manager.incept({salt: salt, stem: stem, temp: true})
        verfers = hashes[0]
        digers = hashes[1]

        assert.equal(verfers.length, 1)
        assert.equal(digers.length, 1)
        assert.equal(manager.pidx, 4)

        spre = verfers[0].qb64
        assert.equal(spre, "DOtu4gX3oc4feusD8wWIykLhjkpiJHXEe29eJ2b_1CyM")

        pp = manager.ks.getPrms(spre)!
        assert.equal(pp.pidx, 3)
        assert.equal(pp.algo, Algos.salty)
        assert.equal(manager.decrypter.decrypt(b(pp.salt)).qb64, salt)
        assert.equal(pp.stem, 'red')
        assert.equal(pp.tier, Tier.low)

        ps = manager.ks.getSits(spre)!
        assert.deepStrictEqual(ps.old.pubs, [])
        assert.equal(ps.new.pubs.length, 1)
        assert.deepStrictEqual(ps.new.pubs, ['DOtu4gX3oc4feusD8wWIykLhjkpiJHXEe29eJ2b_1CyM'])
        assert.equal(ps.new.ridx, 0)
        assert.equal(ps.new.kidx, 0)
        assert.equal(ps.nxt.pubs.length, 1)
        assert.deepStrictEqual(ps.nxt.pubs, ['DBzZ6vejSNAZpXv1SDRnIF_P1UqcW5d2pu2U-v-uhXvE'])
        assert.equal(ps.nxt.ridx, 1)
        assert.equal(ps.nxt.kidx, 1)

        keys = Array.from(verfers, (verfer: Verfer) => verfer.qb64)
        assert.deepStrictEqual(keys, ps.new.pubs)

        digs = Array.from(digers, (diger: Diger) => diger.qb64)
        assert.deepStrictEqual(digs, ['EIGjhyyBRcqCkPE9bmkph7morew0wW0ak-rQ-dHCH-M2'])

        assert.throws(() => {
            manager.incept({salt: salt, stem: stem, temp: true})
        })

        oldspre = spre
        spre = 'DCNK4lpFfpMM-9rfkY3XVUcCu5o5cxzv1lgMqxMVG3Ic'
        manager.move(oldspre, spre)

        assert.throws(() => {
            manager.incept({salt: salt, stem: stem, temp: true})
        })

        hashes = manager.incept({ncount: 0, salt: salt, stem: 'wit0', transferable: false, temp: true})
        verfers = hashes[0]
        digers = hashes[1]

        let witpre0 = verfers[0].qb64
        assert.equal(verfers[0].qb64, 'BOTNI4RzN706NecNdqTlGEcMSTWiFUvesEqmxWR_op8n')
        assert.equal(verfers[0].code, MtrDex.Ed25519N)
        assert.notEqual(digers, undefined)

        hashes = manager.incept({ncount: 0, salt: salt, stem: 'wit1', transferable: false, temp: true})
        verfers = hashes[0]
        digers = hashes[1]

        let witpre1 = verfers[0].qb64
        assert.equal(verfers[0].qb64, 'BAB_5xNXH4hoxDCtAHPFPDedZ6YwTo8mbdw_v0AOHOMt')
        assert.equal(verfers[0].code, MtrDex.Ed25519N)
        assert.notEqual(digers, undefined)

        assert.notEqual(witpre0, witpre1)
    })
})
