import {Habery} from "../../src/keri/app/habery";
import {strict as assert} from "assert";
import libsodium from "libsodium-wrappers-sumo";
import {Salter} from "../../src/keri/core/salter";
import {b} from "../../src/keri/core/core";

describe('Habery', () => {
    it('should manage AID creation and rotation', async () => {
        await libsodium.ready;
        let salt = new Salter({raw: b('0123456789abcdef')}).qb64
        let hab = new Habery({name: "signify", salt: salt, passcode: "0123456789abcdefghijk"})

        assert.equal(hab.mgr.aeid, "BMbZTXzB7LmWPT2TXLGV88PQz5vDEM2L2flUs2yxn3U9")

        let icp = hab.makeHab({})

        assert.deepStrictEqual(icp["keys"], ["DC7Zg7BasK65MdK1hgVd8nB9_2Dj_i1DruqNN9VBsrRd"])
        assert.deepStrictEqual(icp["ndigs"], ["EBRJBDoLKcD9s5tGg0uXLgt79iClVnlceMJHi1qdwRdC"])
    })
})