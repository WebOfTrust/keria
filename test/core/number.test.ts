import {strict as assert} from "assert";
import {CesrNumber} from "../../src/keri/core/number";

describe('THolder', () => {
    it('should hold thresholds', async () => {
        let n = new CesrNumber({}, undefined, "0")
        assert.equal(n.num, 0)
        assert.equal(n.numh, "0")
        n = new CesrNumber({}, 0)
        assert.equal(n.num, 0)
        assert.equal(n.numh, "0")

        n = new CesrNumber({}, 1)
        assert.equal(n.num, 1)
        assert.equal(n.numh, "1")

        n = new CesrNumber({}, 15)
        assert.equal(n.num, 15)
        assert.equal(n.numh, "f")

        n = new CesrNumber({}, undefined,"1")
        assert.equal(n.num, 1)
        assert.equal(n.numh, "1")

        n = new CesrNumber({}, undefined,"f")
        assert.equal(n.num, 15)
        assert.equal(n.numh, "f")

        n = new CesrNumber({}, undefined,"15")
        assert.equal(n.num, 21)
        assert.equal(n.numh, "15")
    })
})