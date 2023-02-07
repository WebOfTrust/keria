import {strict as assert} from "assert";
import libsodium from "libsodium-wrappers-sumo";
import {Salter, Tier} from "../../src/keri/core/salter";
import {b} from "../../src/keri/core/core";
import {MtrDex} from "../../src/keri/core/matter";
import {designature, Signage, signature} from "../../src/keri/end/ending";
import {Siger} from "../../src/keri/core/siger";
import {Cigar} from "../../src/keri/core/cigar";


describe('ending_signature_designature', () => {
    it('should create and parse signature headers', async () => {
        await libsodium.ready;

        let name = "Hilga"
        let temp = true

        let salter = new Salter({raw: b('0123456789abcdef')})
        let signer0 = salter.signer(MtrDex.Ed25519_Seed, true, `${name}00`, Tier.low, temp)
        let signer1 = salter.signer(MtrDex.Ed25519_Seed, true, `${name}01`, Tier.low, temp)
        let signer2 = salter.signer(MtrDex.Ed25519_Seed, true, `${name}02`, Tier.low, temp)
        let signers = [signer0, signer1, signer2]

        let text = b('{"seid":"BA89hKezugU2LFKiFVbitoHAxXqJh6HQ8Rn9tH7fxd68","name":"wit0","dts":"2021-01-01T00' +
            ':00:00.000000+00:00","scheme":"http","host":"localhost","port":8080,"path":"/witness"}')

        let sigers = Array.from(signers, (signer, idx) => signer.sign(text, idx))
        let pre = "EGqHykT1gVyuWxsVW6LUUsz_KtLJGYMi_SrohInwvjC-"  // Hab.pre from KERIpy test
        let digest = pre

        let signage = new Signage(sigers)
        let header = signature([signage])
        assert.equal(header.has("Signature"), true)
        assert.equal(header.get("Signature"), 'indexed="?1";0="AACsufRGYI-sRvS2c0rsOueSoSRtrjODaf48DYLJbLvvD8aHe7b2sWGebZ-y9ichhsxMF3Hhn-3LYSKIrnmH3oIN";1="ABDs7m2-h5l7vpjYtbFXtksicpZK5Oclm43EOkE2xoQOfr08doj73VrlKZOKNfJmRumD3tfaiFFgVZqPgiHuFVoA";2="ACDVOy2LvGgFINUneL4iwA55ypJR6vDpLLbdleEsiANmFazwZARypJMiw9vu2Iu0oL7XCUiUT4JncU8P3HdIp40F"')

        let signages = designature(header.get("Signature")!)
        assert.equal(signages.length, 1)
        signage = signages[0]
        assert.equal(signage.markers.size, 3)
        signage.markers.forEach((item: string|Siger|Cigar, tag: string) => {
            let marker = item as Siger
            let idx = parseInt(tag)
            let siger = sigers[idx] as Siger
            assert.equal(marker.qb64, siger.qb64)
            assert.equal(parseInt(tag), siger.index)
        })

        signage = new Signage(sigers, true, pre, "0", digest, "CESR")
        header = signature([signage])
        assert.equal(header.has("Signature"), true)
        assert.equal(header.get("Signature"), 'indexed="?1";signer="EGqHykT1gVyuWxsVW6LUUsz_KtLJGYMi_SrohInwvjC-";ordinal="0";digest="EGqHykT1gVyuWxsVW6LUUsz_KtLJGYMi_SrohInwvjC-";kind="CESR";0="AACsufRGYI-sRvS2c0rsOueSoSRtrjODaf48DYLJbLvvD8aHe7b2sWGebZ-y9ichhsxMF3Hhn-3LYSKIrnmH3oIN";1="ABDs7m2-h5l7vpjYtbFXtksicpZK5Oclm43EOkE2xoQOfr08doj73VrlKZOKNfJmRumD3tfaiFFgVZqPgiHuFVoA";2="ACDVOy2LvGgFINUneL4iwA55ypJR6vDpLLbdleEsiANmFazwZARypJMiw9vu2Iu0oL7XCUiUT4JncU8P3HdIp40F"')

        signages = designature(header.get("Signature")!)
        assert.equal(signages.length, 1)
        signage = signages[0]
        assert.equal(signage.indexed, true)
        assert.equal(signage.signer, pre)
        assert.equal(signage.digest, digest)
        assert.equal(signage.kind, "CESR")

        assert.equal(signage.markers.size, 3)
        signage.markers.forEach((item: string|Siger|Cigar, tag: string) => {
            let marker = item as Siger
            let idx = parseInt(tag)
            let siger = sigers[idx] as Siger
            assert.equal(marker.qb64, siger.qb64)
            assert.equal(parseInt(tag), siger.index)
        })

        let cigars = Array.from(signers, (signer) => signer.sign(text))
        signage = new Signage(cigars)
        header = signature([signage])
        assert.equal(header.has("Signature"), true)
        assert.equal(header.get("Signature"), 'indexed="?0";DAi2TaRNVtGmV8eSUvqHIBzTzIgrQi57vKzw5Svmy7jw="0BCsufRGYI-sRvS2c0rsOueSoSRtrjODaf48DYLJbLvvD8aHe7b2sWGebZ-y9ichhsxMF3Hhn-3LYSKIrnmH3oIN";DNK2KFnL0jUGlmvZHRse7HwNGVdtkM-ORvTZfFw7mDbt="0BDs7m2-h5l7vpjYtbFXtksicpZK5Oclm43EOkE2xoQOfr08doj73VrlKZOKNfJmRumD3tfaiFFgVZqPgiHuFVoA";DDvIoIYqeuXJ4Zb8e2luWfjPTg4FeIzfHzIO8lC56WjD="0BDVOy2LvGgFINUneL4iwA55ypJR6vDpLLbdleEsiANmFazwZARypJMiw9vu2Iu0oL7XCUiUT4JncU8P3HdIp40F"')
        signages = designature(header.get("Signature")!)
        assert.equal(signages.length, 1)
        signage = signages[0]
        assert.equal(signage.indexed, false)
        assert.equal(signage.markers.size, 3)
        signage.markers.forEach((marker: Cigar, tag: string) => {
            let cigar = cigars.find((cigar) => cigar.verfer!.qb64 == tag)
            assert.notEqual(cigar, undefined)
            assert.equal(marker.qb64, cigar!.qb64)
            assert.equal(tag, cigar!.verfer!.qb64)
        })

        // now combine into one header
        signages = new Array<Signage>()
        signages.push(new Signage(sigers, true, pre, undefined, undefined, "CESR"))
        signages.push(new Signage(cigars, false, pre, undefined, undefined, "CESR"))

        header = signature(signages)
        assert.equal(header.has("Signature"), true)
        assert.equal(header.get("Signature"), 'indexed="?1";signer="EGqHykT1gVyuWxsVW6LUUsz_KtLJGYMi_SrohInwvjC-";kind="CESR";0="AACsufRGYI-sRvS2c0rsOueSoSRtrjODaf48DYLJbLvvD8aHe7b2sWGebZ-y9ichhsxMF3Hhn-3LYSKIrnmH3oIN";1="ABDs7m2-h5l7vpjYtbFXtksicpZK5Oclm43EOkE2xoQOfr08doj73VrlKZOKNfJmRumD3tfaiFFgVZqPgiHuFVoA";2="ACDVOy2LvGgFINUneL4iwA55ypJR6vDpLLbdleEsiANmFazwZARypJMiw9vu2Iu0oL7XCUiUT4JncU8P3HdIp40F",indexed="?0";signer="EGqHykT1gVyuWxsVW6LUUsz_KtLJGYMi_SrohInwvjC-";kind="CESR";DAi2TaRNVtGmV8eSUvqHIBzTzIgrQi57vKzw5Svmy7jw="0BCsufRGYI-sRvS2c0rsOueSoSRtrjODaf48DYLJbLvvD8aHe7b2sWGebZ-y9ichhsxMF3Hhn-3LYSKIrnmH3oIN";DNK2KFnL0jUGlmvZHRse7HwNGVdtkM-ORvTZfFw7mDbt="0BDs7m2-h5l7vpjYtbFXtksicpZK5Oclm43EOkE2xoQOfr08doj73VrlKZOKNfJmRumD3tfaiFFgVZqPgiHuFVoA";DDvIoIYqeuXJ4Zb8e2luWfjPTg4FeIzfHzIO8lC56WjD="0BDVOy2LvGgFINUneL4iwA55ypJR6vDpLLbdleEsiANmFazwZARypJMiw9vu2Iu0oL7XCUiUT4JncU8P3HdIp40F"')
        signages = designature(header.get("Signature")!)
        assert.equal(signages.length, 2)

        signage = signages[0]
        assert.equal(signage.indexed, true)
        assert.equal(signage.signer, pre)
        assert.equal(signage.kind, "CESR")
        assert.equal(signage.markers.size, 3)
        signage.markers.forEach((item: string|Siger|Cigar, tag: string) => {
            let marker = item as Siger
            let idx = parseInt(tag)
            let siger = sigers[idx] as Siger
            assert.equal(marker.qb64, siger.qb64)
            assert.equal(parseInt(tag), siger.index)
        })

        signage = signages[1]
        assert.equal(signage.indexed, false)
        assert.equal(signage.signer, pre)
        assert.equal(signage.kind, "CESR")
        assert.equal(signage.markers.size, 3)
        signage.markers.forEach((marker: Cigar, tag: string) => {
            let cigar = cigars.find((cigar) => cigar.verfer!.qb64 == tag)
            assert.notEqual(cigar, undefined)
            assert.equal(marker.qb64, cigar!.qb64)
            assert.equal(tag, cigar!.verfer!.qb64)
        })

    })
})