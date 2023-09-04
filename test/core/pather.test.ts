import {strict as assert} from "assert";
import {Pather} from "../../src/keri/core/pather";
import {b} from "../../src";


describe("Pather", () => {
    it("should path-ify stuff (and back again)", () => {
        assert.throws(() => {
            new Pather({})
        })

        let path: string[] = []
        let pather = new Pather({}, undefined, path)
        assert.equal(pather.bext, "-")
        assert.equal(pather.qb64, "6AABAAA-")
        assert.deepStrictEqual(pather.raw, b('>'))
        assert.deepStrictEqual(pather.path, path)

        path = ["a", "b", "c"]
        pather = new Pather({}, undefined, path)
        assert.equal(pather.bext, "-a-b-c")
        assert.equal(pather.qb64, "5AACAA-a-b-c")
        assert.deepStrictEqual(pather.raw, new Uint8Array( [15, 154, 249, 191, 156]))
        assert.deepStrictEqual(pather.path, path)

        path = ["0", "1", "2"]
        pather = new Pather({}, undefined, path)
        assert.equal(pather.bext, "-0-1-2")
        assert.equal(pather.qb64, "5AACAA-0-1-2")
        assert.deepStrictEqual(pather.raw, new Uint8Array( [15, 180, 251, 95, 182]))
        assert.deepStrictEqual(pather.path, path)

        path = ["field0", "1", "0"]
        pather = new Pather({}, undefined, path)
        assert.equal(pather.bext, "-field0-1-0")
        assert.equal(pather.qb64, "4AADA-field0-1-0")
        assert.deepStrictEqual(pather.raw, new Uint8Array( [3, 231, 226, 122, 87, 116, 251, 95, 180]))
        assert.deepStrictEqual(pather.path, path)

        path = ["Not$Base64", "@moreso", "*again"]
        assert.throws(() => {
            new Pather({}, undefined, path)
        })

    })
})