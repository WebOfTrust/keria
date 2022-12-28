import libsodium from "libsodium-wrappers-sumo";
import {b, d, b64ToInt, intToB64, intToB64b} from "../../src/keri/core/core";
import {strict as assert} from "assert";


describe('int to b64 and back', () => {
    it('should encode and decode stuff', async () => {
        await libsodium.ready;
        
        let cs = intToB64(0)
        assert.equal(cs, "A")
        let i = b64ToInt(cs)
        assert.equal(i, 0)

        cs = intToB64(0, 0)
        assert.equal(cs, "")
        assert.throws(() => {
            i = b64ToInt(cs)
        })

        cs = intToB64(undefined, 0)
        assert.equal(cs, "")
        assert.throws(() => {
            i = b64ToInt(cs)
        })

        let csb = intToB64b(0)
        assert.deepStrictEqual(csb, b("A"))
        i = b64ToInt(d(csb))
        assert.equal(i, 0)

        cs = intToB64(27)
        assert.equal(cs, "b")
        i = b64ToInt(cs)
        assert.equal(i, 27)

        csb = intToB64b(27)
        assert.deepStrictEqual(csb, b("b"))
        i = b64ToInt(d(csb))
        assert.equal(i, 27)

        cs = intToB64(27, 2)
        assert.equal(cs, "Ab")
        i = b64ToInt(cs)
        assert.equal(i, 27)

        csb = intToB64b(27, 2)
        assert.deepStrictEqual(csb, b("Ab"))
        i = b64ToInt(d(csb))
        assert.equal(i, 27)

        cs = intToB64(80)
        assert.equal(cs, "BQ")
        i = b64ToInt(cs)
        assert.equal(i, 80)

        csb = intToB64b(80)
        assert.deepStrictEqual(csb, b("BQ"))
        i = b64ToInt(d(csb))
        assert.equal(i, 80)

        cs = intToB64(4095)
        assert.equal(cs, '__')
        i = b64ToInt(cs)
        assert.equal(i, 4095)

        csb = intToB64b(4095)
        assert.deepStrictEqual(csb, b('__'))
        i = b64ToInt(d(csb))
        assert.equal(i, 4095)

        cs = intToB64(4096)
        assert.equal(cs, 'BAA')
        i = b64ToInt(cs)
        assert.equal(i, 4096)

        csb = intToB64b(4096)
        assert.deepStrictEqual(csb, b('BAA'))
        i = b64ToInt(d(csb))
        assert.equal(i, 4096)

        cs = intToB64(6011)
        assert.equal(cs, "Bd7")
        i = b64ToInt(cs)
        assert.equal(i, 6011)

        csb = intToB64b(6011)
        assert.deepStrictEqual(csb, b("Bd7"))
        i = b64ToInt(d(csb))
        assert.equal(i, 6011)
    })
})
