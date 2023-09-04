import {strict as assert} from "assert";
import libsodium from "libsodium-wrappers-sumo";

import { Signer } from '../../src';
import {Matter, MtrDex} from "../../src";
import {b} from "../../src";

describe('Signer', () => {
    it('should sign things', async () => {
        await libsodium.ready;

        let signer = new Signer({})  // defaults provide Ed25519 signer Ed25519 verfer
        assert.equal(signer.code, MtrDex.Ed25519_Seed)
        assert.equal(signer.raw.length, Matter._rawSize(signer.code))
        assert.equal(signer.verfer.code, MtrDex.Ed25519)
        assert.equal(signer.verfer.raw.length, Matter._rawSize(signer.verfer.code))

        let ser = b('abcdefghijklmnopqrstuvwxyz0123456789')

        let cigar = signer.sign(ser)
        assert.equal(cigar.code, MtrDex.Ed25519_Sig)
        assert.equal(cigar.raw.length, Matter._rawSize(cigar.code))
        let result = signer.verfer.verify(cigar.raw, ser)
        assert.equal(result, true)
    });
});