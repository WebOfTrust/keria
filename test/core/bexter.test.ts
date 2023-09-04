import {strict as assert} from "assert";
import {Bexter} from "../../src/keri/core/bexter";
import {b, MtrDex} from "../../src";


describe("Bexter", () => {
    it("should bext-ify stuff (and back again)", () => {
        assert.throws(() => {
            new Bexter({})
        })

        let bext = "@!"
        assert.throws(() => {
            new Bexter({}, bext)
        })

        bext = ""
        let bexter = new Bexter({}, bext)
        assert.equal(bexter.code, MtrDex.StrB64_L0)
        assert.equal(bexter.both, '4AAA')
        assert.deepStrictEqual(bexter.raw, b(''))
        assert.equal(bexter.qb64, '4AAA')
        assert.equal(bexter.bext, bext)

        bext = "-"
        bexter = new Bexter({}, bext)
        assert.equal(bexter.code, MtrDex.StrB64_L2)
        assert.equal(bexter.both, '6AAB')
        assert.deepStrictEqual(bexter.raw, b('>'))
        assert.equal(bexter.qb64, '6AABAAA-')
        assert.equal(bexter.bext, bext)

        bext = "-A"
        bexter = new Bexter({}, bext)
        assert.equal(bexter.code, MtrDex.StrB64_L1)
        assert.equal(bexter.both, '5AAB')
        assert.deepStrictEqual(bexter.raw, Uint8Array.from([15, 128]))
        assert.equal(bexter.qb64, '5AABAA-A')
        assert.equal(bexter.bext, bext)

        bext = "-A-"
        bexter = new Bexter({}, bext)
        assert.equal(bexter.code, MtrDex.StrB64_L0)
        assert.equal(bexter.both, '4AAB')
        assert.deepStrictEqual(bexter.raw, Uint8Array.from([3, 224, 62]))
        assert.equal(bexter.qb64, '4AABA-A-')
        assert.equal(bexter.bext, bext)

        bext = "-A-B"
        bexter = new Bexter({}, bext)
        assert.equal(bexter.code, MtrDex.StrB64_L0)
        assert.equal(bexter.both, '4AAB')
        assert.deepStrictEqual(bexter.raw, Uint8Array.from([248, 15, 129]))
        assert.equal(bexter.qb64, '4AAB-A-B')
        assert.equal(bexter.bext, bext)

        bext = "A"
        bexter = new Bexter({}, bext)
        assert.equal(bexter.code, MtrDex.StrB64_L2)
        assert.equal(bexter.both, '6AAB')
        assert.deepStrictEqual(bexter.raw, Uint8Array.from([0]))
        assert.equal(bexter.qb64, '6AABAAAA')
        assert.equal(bexter.bext, bext)

        bext = "AA"
        bexter = new Bexter({}, bext)
        assert.equal(bexter.code, MtrDex.StrB64_L1)
        assert.equal(bexter.both, '5AAB')
        assert.deepStrictEqual(bexter.raw, Uint8Array.from([0, 0]))
        assert.equal(bexter.qb64, '5AABAAAA')
        assert.equal(bexter.bext, bext)

        bext = "AAA"
        bexter = new Bexter({}, bext)
        assert.equal(bexter.code, MtrDex.StrB64_L0)
        assert.equal(bexter.both, '4AAB')
        assert.deepStrictEqual(bexter.raw, Uint8Array.from([0, 0, 0]))
        assert.equal(bexter.qb64, '4AABAAAA')
        assert.equal(bexter.bext, bext)

        bext = "AAAA"
        bexter = new Bexter({}, bext)
        assert.equal(bexter.code, MtrDex.StrB64_L0)
        assert.equal(bexter.both, '4AAB')
        assert.deepStrictEqual(bexter.raw, Uint8Array.from([0, 0, 0]))
        assert.equal(bexter.qb64, '4AABAAAA')
        assert.equal(bexter.bext, "AAA")
        assert.notEqual(bexter.bext, bext)

        bext = "ABB"
        bexter = new Bexter({}, bext)
        assert.equal(bexter.code, MtrDex.StrB64_L0)
        assert.equal(bexter.both, '4AAB')
        assert.deepStrictEqual(bexter.raw, Uint8Array.from([0, 0, 65]))
        assert.equal(bexter.qb64, '4AABAABB')
        assert.equal(bexter.bext, bext)

        bext = "BBB"
        bexter = new Bexter({}, bext)
        assert.equal(bexter.code, MtrDex.StrB64_L0)
        assert.equal(bexter.both, '4AAB')
        assert.deepStrictEqual(bexter.raw, Uint8Array.from([0, 16, 65]))
        assert.equal(bexter.qb64, '4AABABBB')
        assert.equal(bexter.bext, bext)

        bext = "ABBB"
        bexter = new Bexter({}, bext)
        assert.equal(bexter.code, MtrDex.StrB64_L0)
        assert.equal(bexter.both, '4AAB')
        assert.deepStrictEqual(bexter.raw, Uint8Array.from([0, 16, 65]))
        assert.equal(bexter.qb64, '4AABABBB')
        assert.equal(bexter.bext, 'BBB')
        assert.notEqual(bexter.bext, bext)
    })
})