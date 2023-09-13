import {strict as assert} from "assert";
import {b, d, Dict, Diger, exchange, Ilks, MtrDex, Salter, Serder, Tier} from "../../src";
import libsodium from "libsodium-wrappers-sumo";
import { SignifyClient } from "../../src/keri/app/clienting"
import { Authenticater } from "../../src/keri/core/authing"
import fetchMock from "jest-fetch-mock"
import 'whatwg-fetch'

fetchMock.enableMocks();

const url = "http://127.0.0.1:3901"
const boot_url = "http://127.0.0.1:3903"

const mockConnect = '{"agent":{"vn":[1,0],"i":"EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei",' +
    '"s":"0","p":"","d":"EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei","f":"0",' +
    '"dt":"2023-08-19T21:04:57.948863+00:00","et":"dip","kt":"1",' +
    '"k":["DMZh_y-H5C3cSbZZST-fqnsmdNTReZxIh0t2xSTOJQ8a"],"nt":"1",' +
    '"n":["EM9M2EQNCBK0MyAhVYBvR98Q0tefpvHgE-lHLs82XgqC"],"bt":"0","b":[],' +
    '"c":[],"ee":{"s":"0","d":"EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei","br":[],"ba":[]},' +
    '"di":"ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"},"controller":{"state":{"vn":[1,0],' +
    '"i":"ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose","s":"0","p":"",' +
    '"d":"ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose","f":"0","dt":"2023-08-19T21:04:57.959047+00:00",' +
    '"et":"icp","kt":"1","k":["DAbWjobbaLqRB94KiAutAHb_qzPpOHm3LURA_ksxetVc"],"nt":"1",' +
    '"n":["EIFG_uqfr1yN560LoHYHfvPAhxQ5sN6xZZT_E3h7d2tL"],"bt":"0","b":[],"c":[],"ee":{"s":"0",' +
    '"d":"ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose","br":[],"ba":[]},"di":""},' +
    '"ee":{"v":"KERI10JSON00012b_","t":"icp","d":"ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose",' +
    '"i":"ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose","s":"0","kt":"1",' +
    '"k":["DAbWjobbaLqRB94KiAutAHb_qzPpOHm3LURA_ksxetVc"],"nt":"1",' +
    '"n":["EIFG_uqfr1yN560LoHYHfvPAhxQ5sN6xZZT_E3h7d2tL"],"bt":"0","b":[],"c":[],"a":[]}},"ridx":0,' +
    '"pidx":0}'
const mockGetAID = {
    "name": "aid1",
    "prefix": "ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK",
    "salty": {
        "sxlt": "1AAHnNQTkD0yxOC9tSz_ukbB2e-qhDTStH18uCsi5PCwOyXLONDR3MeKwWv_AVJKGKGi6xiBQH25_R1RXLS2OuK3TN3ovoUKH7-A",
        "pidx": 0,
        "kidx": 0,
        "stem": "signify:aid",
        "tier": "low",
        "dcode": "E",
        "icodes": [
            "A"
        ],
        "ncodes": [
            "A"
        ],
        "transferable": true
    },
    "transferable": true,
    "state": {
        "vn": [
            1,
            0
        ],
        "i": "ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK",
        "s": "0",
        "p": "",
        "d": "ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK",
        "f": "0",
        "dt": "2023-08-21T22:30:46.473545+00:00",
        "et": "icp",
        "kt": "1",
        "k": [
            "DPmhSfdhCPxr3EqjxzEtF8TVy0YX7ATo0Uc8oo2cnmY9"
        ],
        "nt": "1",
        "n": [
            "EAORnRtObOgNiOlMolji-KijC_isa3lRDpHCsol79cOc"
        ],
        "bt": "0",
        "b": [],
        "c": [],
        "ee": {
            "s": "0",
            "d": "ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK",
            "br": [],
            "ba": []
        },
        "di": ""
    },
    "windexes": []
}

const mockCredential = { "sad": { "v": "ACDC10JSON000197_", "d": "EMwcsEMUEruPXVwPCW7zmqmN8m0I3CihxolBm-RDrsJo", "i": "EMQQpnSkgfUOgWdzQTWfrgiVHKIDAhvAZIPQ6z3EAfz1", "ri": "EGK216v1yguLfex4YRFnG7k1sXRjh3OKY7QqzdKsx7df", "s": "EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao", "a": { "d": "EK0GOjijKd8_RLYz9qDuuG29YbbXjU8yJuTQanf07b6P", "i": "EKvn1M6shPLnXTb47bugVJblKMuWC0TcLIePP8p98Bby", "dt": "2023-08-23T15:16:07.553000+00:00", "LEI": "5493001KJTIIGC8Y1R17" } }, "pre": "EMQQpnSkgfUOgWdzQTWfrgiVHKIDAhvAZIPQ6z3EAfz1", "sadsigers": [{ "path": "-", "pre": "EMQQpnSkgfUOgWdzQTWfrgiVHKIDAhvAZIPQ6z3EAfz1", "sn": 0, "d": "EMQQpnSkgfUOgWdzQTWfrgiVHKIDAhvAZIPQ6z3EAfz1" }], "sadcigars": [], "chains": [], "status": { "v": "KERI10JSON000135_", "i": "EMwcsEMUEruPXVwPCW7zmqmN8m0I3CihxolBm-RDrsJo", "s": "0", "d": "ENf3IEYwYtFmlq5ZzoI-zFzeR7E3ZNRN2YH_0KAFbdJW", "ri": "EGK216v1yguLfex4YRFnG7k1sXRjh3OKY7QqzdKsx7df", "ra": {}, "a": { "s": 2, "d": "EIpgyKVF0z0Pcn2_HgbWhEKmJhOXFeD4SA62SrxYXOLt" }, "dt": "2023-08-23T15:16:07.553000+00:00", "et": "iss" } }


fetchMock.mockResponse(req => {
    if (req.url.startsWith(url + '/agent')) {
        return Promise.resolve({ body: mockConnect, init: { status: 202 } })
    } else if (req.url == boot_url + '/boot') {
        return Promise.resolve({ body: "", init: { status: 202 } })
    } else {
        let headers = new Headers()
        let signed_headers = new Headers()

        headers.set('Signify-Resource', "EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei")
        headers.set('Signify-Timestamp', new Date().toISOString().replace('Z', '000+00:00'))
        headers.set('Content-Type', 'application/json')

        const requrl = new URL(req.url)
        let salter = new Salter({ qb64: '0AAwMTIzNDU2Nzg5YWJjZGVm' })
        let signer = salter.signer("A", true, "agentagent-ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose00", Tier.low)

        let authn = new Authenticater(signer!, signer!.verfer)
        signed_headers = authn.sign(headers, req.method, requrl.pathname.split('?')[0])
        let body = req.url.startsWith(url + '/identifiers/aid1/credentials') ? mockCredential : mockGetAID

        return Promise.resolve({ body: JSON.stringify(body), init: { status: 202, headers: signed_headers } })
    }

})


describe("exchange", () => {
    it("should create an exchange message with no transposed attachments", async () => {
        await libsodium.ready
        let dt = "2023-08-30T17:22:54.183Z"

        let [exn, end] = exchange("/multisig/vcp", {}, "test", undefined, dt)
        assert.deepStrictEqual(exn.ked, {
                "a": {}, "d": "EMhxioc6Ud9b3JZ4X9o79uytSRIXXNDUf27ruwiOmNdQ", "dt": "2023-08-30T17:22:54.183Z", "e": {},
                "i": "test",
                "p": "", "q": {}, "r": "/multisig/vcp", "t": "exn", "v": "KERI10JSON0000b1_"
            }
        )
        assert.deepStrictEqual(end, new Uint8Array())

        let sith = 1
        let nsith = 1
        let sn = 0
        let toad = 0

        let raw = new Uint8Array([5, 170, 143, 45, 83, 154, 233, 250, 85, 156, 2, 156, 155, 8, 72, 117])
        let salter = new Salter({raw: raw})
        let skp0 = salter.signer(MtrDex.Ed25519_Seed, true, "A", Tier.low, true)
        let keys = [skp0.verfer.qb64]

        let skp1 = salter.signer(MtrDex.Ed25519_Seed, true, "N", Tier.low, true)
        let ndiger = new Diger({}, skp1.verfer.qb64b)
        let nxt = [ndiger.qb64]
        assert.deepStrictEqual(nxt, ['EAKUR-LmLHWMwXTLWQ1QjxHrihBmwwrV2tYaSG7hOrWj'])

        let ked0 = {
            v: "KERI10JSON000000_",
            t: Ilks.icp,
            d: "",
            i: "",
            s: sn.toString(16),
            kt: sith.toString(16),
            k: keys,
            nt: nsith.toString(16),
            n: nxt,
            bt: toad.toString(16),
            b: [],
            c: [],
            a: [],
        } as Dict<any>

        let serder = new Serder(ked0)
        let siger = skp0.sign(b(serder.raw), 0)
        assert.equal(siger.qb64, "AAAPkMTS3LrrhVuQB0k4UndDN0xIfEiKYaN7rTlQ_q9ImnBcugwNO8VWTALXzWoaldJEC1IOpEGkEnjZfxxIleoI")

        let ked1 = {
            v: "KERI10JSON000000_",
            t: Ilks.vcp,
            d: "",
            i: "",
            s: "0",
            bt: toad.toString(16),
            b: []
        } as Dict<any>
        let vcp = new Serder(ked1)


        let embeds = {
            icp: [serder, siger.qb64],
            vcp: [vcp, undefined]
        } as Dict<any>

        [exn, end] = exchange("/multisig/vcp", {}, "test", undefined, dt, undefined, undefined, embeds)

        assert.deepStrictEqual(exn.ked, {
            "a": {},
            "d": "EHDEXQx-i0KlQ8iVnITMLa144dAb7Kjq2KDTufDUyLcm",
            "dt": "2023-08-30T17:22:54.183Z",
            "e": {
                "d": "EDPWpKtMoPwro_Of8TQzpNMGdtmfyWzqTcRKQ01fGFRi",
                "icp": {
                    "a": [],
                    "b": [],
                    "bt": "0",
                    "c": [],
                    "d": "",
                    "i": "",
                    "k": ["DAUDqkmn-hqlQKD8W-FAEa5JUvJC2I9yarEem-AAEg3e"],
                    "kt": "1",
                    "n": ["EAKUR-LmLHWMwXTLWQ1QjxHrihBmwwrV2tYaSG7hOrWj"],
                    "nt": "1",
                    "s": "0",
                    "t": "icp",
                    "v": "KERI10JSON0000d3_"
                },
                "vcp": {"b": [], "bt": "0", "d": "", "i": "", "s": "0", "t": "vcp", "v": "KERI10JSON000049_"}
            },
            "i": "test",
            "p": "",
            "q": {},
            "r": "/multisig/vcp",
            "t": "exn",
            "v": "KERI10JSON00020d_"
        })
        assert.equal(d(end), "-LAZ5AACAA-e-icpAAAPkMTS3LrrhVuQB0k4UndDN0xIfEiKYaN7rTlQ_q9ImnBcugwNO8VWTALXzWoaldJEC1IOpEGkEnjZfxxIleoI")


    })

    it('SendFromEvents', async () => {
        await libsodium.ready;
        const bran = "0123456789abcdefghijk"

        let client = new SignifyClient(url, bran, Tier.low, boot_url)

        await client.boot()
        await client.connect()

        let exchange = client.exchanges()
        let sith = 1
        let nsith = 1
        let sn = 0
        let toad = 0

        let raw = new Uint8Array([5, 170, 143, 45, 83, 154, 233, 250, 85, 156, 2, 156, 155, 8, 72, 117])
        let salter = new Salter({raw: raw})
        let skp0 = salter.signer(MtrDex.Ed25519_Seed, true, "A", Tier.low, true)
        let keys = [skp0.verfer.qb64]

        let skp1 = salter.signer(MtrDex.Ed25519_Seed, true, "N", Tier.low, true)
        let ndiger = new Diger({}, skp1.verfer.qb64b)
        let nxt = [ndiger.qb64]
        assert.deepStrictEqual(nxt, ['EAKUR-LmLHWMwXTLWQ1QjxHrihBmwwrV2tYaSG7hOrWj'])

        let ked0 = {
            v: "KERI10JSON000000_",
            t: Ilks.icp,
            d: "",
            i: "",
            s: sn.toString(16),
            kt: sith.toString(16),
            k: keys,
            nt: nsith.toString(16),
            n: nxt,
            bt: toad.toString(16),
            b: [],
            c: [],
            a: [],
        } as Dict<any>

        let serder = new Serder(ked0)

        let lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!
        await exchange.sendFromEvents('aid1','',serder,[''],'',[])
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!
        assert.equal(lastCall[0]!, url + '/identifiers/aid1/exchanges')
        assert.equal(lastCall[1]!.method, 'POST')

    })
})