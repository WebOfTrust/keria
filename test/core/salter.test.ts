import {strict as assert} from "assert";
import libsodium from "libsodium-wrappers-sumo";

import { Salter } from '../../src/keri/core/salter';

describe('Salter', () => {
    it('should generate salts', async () => {
        await libsodium.ready;
        let salter = new Salter({})

        assert.notEqual(salter, null)
        assert.equal(salter.qb64.length, 24)

        let salt = new Uint8Array([146, 78, 142, 186, 189, 77, 130, 3, 232, 248, 186, 197, 8, 0, 73, 182])
        salter = new Salter({raw: salt})
        assert.notEqual(salter, null)
        assert.equal(salter.qb64, "0ACSTo66vU2CA-j4usUIAEm2")

        salter = new Salter({qb64: "0ACSTo66vU2CA-j4usUIAEm2"})
        let raw = new Uint8Array([146, 78, 142, 186, 189, 77, 130, 3, 232, 248, 186, 197, 8, 0, 73, 182]);
        assert.deepStrictEqual(salter.raw, raw)

        salter = new Salter({qb64: "0ABa4cx6f0SdfwFawI0A7mOZ"})
        raw = new Uint8Array([90, 225, 204, 122, 127, 68, 157, 127, 1, 90, 192, 141, 0, 238, 99, 153]);
        assert.deepStrictEqual(salter.raw, raw)

    });
});

describe('Salter.signer', () => {
    it('should return a signer', async () => {

        let salter = new Salter({qb64: "0ACSTo66vU2CA-j4usUIAEm2"})
        let signer = salter.signer()
        assert.notEqual(signer, null)
        assert.equal(signer.verfer().qb64, "DD28x2a4KCZ8f6OAcA856jAD1chNOo4pT8ICxyzJUJhj")

    });
});
