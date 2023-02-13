import {strict as assert} from "assert";
import libsodium from "libsodium-wrappers-sumo";
import {Salter} from "../../src/keri/core/salter";
import {b} from "../../src/keri/core/core";
import {siginput, desiginput, SiginputArgs} from "../../src/keri/core/httping";
import * as utilApi from "../../src/keri/core/utils";


describe('siginput', () => {
    it('create valid Signature-Input header with signature', async () => {
        await libsodium.ready;
        let salt = '0123456789abcdef'
        let salter = new Salter({raw: b(salt)})
        let signer = salter.signer()

        let headers: Headers = new Headers([
            ["Content-Type", "application/json"],
            ["Content-Length", "256"],
            ["Connection", "close"],
            ["Signify-Resource", "EWJkQCFvKuyxZi582yJPb0wcwuW3VXmFNuvbQuBpgmIs"],
            ["Signify-Timestamp", "2022-09-24T00:05:48.196795+00:00"],
        ])
        jest.spyOn(utilApi, "nowUTC").mockReturnValue(new Date("2021-01-01T00:00:00.000000+00:00"))


        let [header, sig] = siginput(signer, {
            name: "sig0",
            method: "POST",
            path: "/signify",
            headers,
            fields: ["Signify-Resource", "@method", "@path", "Signify-Timestamp"],
            alg: "ed25519",
            keyid: signer.verfer.qb64
        } as SiginputArgs)

        assert.equal(header.size, 1)
        assert.equal(header.has("Signature-Input"), true)
        let sigipt = header.get("Signature-Input")
        assert.equal(sigipt, 'sig0=("Signify-Resource" "@method" "@path" "Signify-Timestamp");created=1609459200;keyid="DN54yRad_BTqgZYUSi_NthRBQrxSnqQdJXWI5UHcGOQt";alg="ed25519"')
        assert.equal(sig.qb64, "0BAU6RvYeiudxVDADCeG2I4S2Y0HVdu97lleiGtUt_swYgSKflVzrqAQJBfrt6vaIO7-dvnPhxfNGTLhONBnqFMJ")
    })
})

describe("desiginput", () => {
    it('create valid Signature-Input header with signature', async () => {
        await libsodium.ready;
        let siginput = 'sig0=("signify-resource" "@method" "@path" "signify-timestamp");created=1609459200;keyid="EIaGMMWJFPmtXznY1IIiKDIrg-vIyge6mBl2QV8dDjI3";alg="ed25519"'

        let inputs = desiginput(siginput)
        assert.equal(inputs.length, 1)
        let input = inputs[0]
        assert.deepStrictEqual(input.fields, ["signify-resource","@method", "@path", "signify-timestamp",])
        assert.equal(input.created, 1609459200)
        assert.equal(input.alg, "ed25519")
        assert.equal(input.keyid, "EIaGMMWJFPmtXznY1IIiKDIrg-vIyge6mBl2QV8dDjI3")
        assert.equal(input.expires, undefined)
        assert.equal(input.nonce, undefined)
        assert.equal(input.context, undefined)
    })
})