import {strict as assert} from "assert";
import libsodium from "libsodium-wrappers-sumo";
import {Salter} from "../../src/keri/core/salter";
import {b} from "../../src/keri/core/core";
import {Authenticater} from "../../src/keri/core/authing";
import * as utilApi from "../../src/keri/core/utils";


describe('Authenticater.verify', () => {
    it('verify signature on Response', async () => {
        await libsodium.ready;
        let salt = '0123456789abcdef'
        let salter = new Salter({raw: b(salt)})
        let signer = salter.signer()
        let aaid = "DDK2N5_fVCWIEO9d8JLhk7hKrkft6MbtkUhaHQsmABHY"

        let headers = new Headers([
            ['Connection', 'close'],
            ['Content-Length', '256'],
            ['Content-Type', 'application/json'],
            ['Signature', ('indexed="?0";signify="bipHos8-XTOzLq0He4tz8mIeZGq4h5WdIndNVCSX2H5eYCqwYOQT7EysiMkgp0HwYBIgmg7wuTQgtJKJ__EBCA=="')],
            ['Signature-Input', ('signify=("signify-resource" "@method" "@path" "signify-timestamp");created=1609459200;keyid="EAM6vT0VYoaEWxRTgr24g0nZHmPSUBgs19WB43zEKHnz";alg="ed25519"')],
            ['Signify-Resource', 'EWJkQCFvKuyxZi582yJPb0wcwuW3VXmFNuvbQuBpgmIs'],
            ['Signify-Timestamp', '2022-09-24T00:05:48.196795+00:00'],
        ])

        let authn = new Authenticater(signer, aaid)
        assert.notEqual(authn, undefined)

        assert.equal(authn.verify(new Headers(headers), "POST", "/boot"), true)
    })
})

describe("Authenticater.sign", () => {
    it('Create signed headers for a request', async () => {
        await libsodium.ready;
        let salt = '0123456789abcdef'
        let salter = new Salter({raw: b(salt)})
        let signer = salter.signer()
        let aaid = "DDK2N5_fVCWIEO9d8JLhk7hKrkft6MbtkUhaHQsmABHY"

        let headers = new Headers([
            ["Content-Type", "application/json"],
            ["Content-Length", "256"],
            ["Connection", "close"],
            ["Signify-Resource", "EWJkQCFvKuyxZi582yJPb0wcwuW3VXmFNuvbQuBpgmIs"],
            ["Signify-Timestamp", "2022-09-24T00:05:48.196795+00:00"],
        ])
        jest.spyOn(utilApi, "nowUTC").mockReturnValue(new Date("2021-01-01T00:00:00.000000+00:00"))

        let authn = new Authenticater(signer, aaid)
        headers = authn.sign(headers, "POST", "/boot")

        assert.equal(headers.has("Signature-Input"), true)
        assert.equal(headers.has("Signature"), true)
        assert.equal(headers.get("Signature-Input"), 'signify=("Signify-Resource" "@method" "@path" "Signify-Timestamp");created=1609459200;keyid="DN54yRad_BTqgZYUSi_NthRBQrxSnqQdJXWI5UHcGOQt";alg="ed25519"')
        assert.equal(headers.get("Signature"), 'indexed="?0";DN54yRad_BTqgZYUSi_NthRBQrxSnqQdJXWI5UHcGOQt="0BDLBHkG4X37TLcNkb-ZORKfez-rWy-d5C1n1i9wFN8Ho8Wh8buKmZ-AHKt97-MzGYXZ18mVDy4Y3Xi75iiwtmMG"')
    })
})