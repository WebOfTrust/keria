import { strict as assert } from "assert"
import { SignifyClient, } from "../../src/keri/app/clienting"
import { CreateIdentiferArgs, RotateIdentifierArgs } from "../../src/keri/app/aiding"
import { Authenticater } from "../../src/keri/core/authing"
import { Salter, Tier } from "../../src/keri/core/salter"
import { Algos } from "../../src/keri/core/manager"
import libsodium from "libsodium-wrappers-sumo"
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

describe('Aiding', () => {

    it('Salty identifiers', async () => {
        await libsodium.ready;
        const bran = "0123456789abcdefghijk"

        let client = new SignifyClient(url, bran, Tier.low, boot_url)

        await client.boot()
        await client.connect()

        let identifiers = client.identifiers()

        await identifiers.list()
        let lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!
        assert.equal(lastCall[0]!, url + '/identifiers')
        assert.equal(lastCall[1]!.method, 'GET')

        await client.identifiers().create('aid1', { bran: '0123456789abcdefghijk' })
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!
        let lastBody = JSON.parse(lastCall[1]!.body!.toString())
        assert.equal(lastCall[0]!, url + '/identifiers')
        assert.equal(lastCall[1]!.method, 'POST')
        assert.equal(lastBody.name, 'aid1')
        assert.deepEqual(lastBody.icp, { "v": "KERI10JSON00012b_", "t": "icp", "d": "ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK", "i": "ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK", "s": "0", "kt": "1", "k": ["DPmhSfdhCPxr3EqjxzEtF8TVy0YX7ATo0Uc8oo2cnmY9"], "nt": "1", "n": ["EAORnRtObOgNiOlMolji-KijC_isa3lRDpHCsol79cOc"], "bt": "0", "b": [], "c": [], "a": [] })
        assert.deepEqual(lastBody.sigs, ["AACZZe75PvUZ1lCREPxFAcX59XHo-BGMYTAGni-I4E0eqKznrEoK2d-mtWmWHwKns7tfnjOzTfDUcv7PLFJ52g0A"])
        assert.deepEqual(lastBody.salty.pidx, 0)
        assert.deepEqual(lastBody.salty.kidx, 0)
        assert.deepEqual(lastBody.salty.stem, "signify:aid")
        assert.deepEqual(lastBody.salty.tier, "low")
        assert.deepEqual(lastBody.salty.icodes, ["A"])
        assert.deepEqual(lastBody.salty.ncodes, ["A"])
        assert.deepEqual(lastBody.salty.dcode, "E")
        assert.deepEqual(lastBody.salty.transferable, true)

        await client.identifiers().create('aid2', { count: 3, ncount: 3, isith: "2", nsith: "2", bran: "0123456789lmnopqrstuv" })
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!
        lastBody = JSON.parse(lastCall[1]!.body!.toString())
        assert.equal(lastCall[0]!, url + '/identifiers')
        assert.equal(lastCall[1]!.method, 'POST')
        assert.equal(lastBody.name, 'aid2')
        assert.deepEqual(lastBody.icp, { "v": "KERI10JSON0001e7_", "t": "icp", "d": "EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX", "i": "EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX", "s": "0", "kt": "2", "k": ["DGBw7C7AfC7jbD3jLLRS3SzIWFndM947TyNWKQ52iQx5", "DD_bHYFsgWXuCbz3SD0HjCIe_ITjRvEoCGuZ4PcNFFDz", "DEe9u8k0fm1wMFAuOIsCtCNrpduoaV5R21rAcJl0awze"], "nt": "2", "n": ["EML5FrjCpz8SEl4dh0U15l8bMRhV_O5iDcR1opLJGBSH", "EJpKquuibYTqpwMDqEFAFs0gwq0PASAHZ_iDmSF3I2Vg", "ELplTAiEKdobFhlf-dh1vUb2iVDW0dYOSzs1dR7fQo60"], "bt": "0", "b": [], "c": [], "a": [] })
        assert.deepEqual(lastBody.sigs, ["AAD9_IgPaUEBjAl1Ck61Jkn78ErzsnVkIxpaFBYSdSEAW4NbtXsLiUn1olijzdTQYn_Byq6MaEk-eoMN3Oc0WEEC", "ABBWJ7KkAXXiRK8JyEUpeARHJTTzlBHu_ev-jUrNEhV9sX4_4lI7wxowrQisumt5r50bUNfYBK7pxSwHk8I4IFQP", "ACDTITaEquHdYKkS-94tVCxL3IYrtvhlTt__sSUavTJT6fI3KB-uwXV7L0SfzMq0gFqYxkheH2LdC4HkAW2mH4QJ"])
        assert.deepEqual(lastBody.salty.pidx, 1)
        assert.deepEqual(lastBody.salty.kidx, 0)
        assert.deepEqual(lastBody.salty.stem, "signify:aid")
        assert.deepEqual(lastBody.salty.tier, "low")
        assert.deepEqual(lastBody.salty.icodes, ["A", "A", "A"])
        assert.deepEqual(lastBody.salty.ncodes, ["A", "A", "A"])
        assert.deepEqual(lastBody.salty.dcode, "E")
        assert.deepEqual(lastBody.salty.transferable, true)

        await client.identifiers().rotate('aid1')
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!
        lastBody = JSON.parse(lastCall[1]!.body!.toString())
        assert.equal(lastCall[0]!, url + '/identifiers/aid1')
        assert.equal(lastCall[1]!.method, 'PUT')
        assert.deepEqual(lastBody.rot, { "v": "KERI10JSON000160_", "t": "rot", "d": "EBQABdRgaxJONrSLcgrdtbASflkvLxJkiDO0H-XmuhGg", "i": "ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK", "s": "1", "p": "ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK", "kt": "1", "k": ["DHgomzINlGJHr-XP3sv2ZcR9QsIEYS3LJhs4KRaZYKly"], "nt": "1", "n": ["EJMovBlrBuD6BVeUsGSxLjczbLEbZU9YnTSud9K4nVzk"], "bt": "0", "br": [], "ba": [], "a": [] })
        assert.deepEqual(lastBody.sigs, ["AABWSckRpAWLpfFSrpnDR3SzQASrRSVKGh8AnHxauhN_43qKkqPb9l04utnTm2ixNpGGJ-UB8qdKMjfkEQ61AIQC"])
        assert.deepEqual(lastBody.salty.pidx, 0)
        assert.deepEqual(lastBody.salty.kidx, 1)
        assert.deepEqual(lastBody.salty.stem, "signify:aid")
        assert.deepEqual(lastBody.salty.tier, "low")
        assert.deepEqual(lastBody.salty.icodes, ["A"])
        assert.deepEqual(lastBody.salty.ncodes, ["A"])
        assert.deepEqual(lastBody.salty.dcode, "E")
        assert.deepEqual(lastBody.salty.transferable, true)

        let data = [{ i: "ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK", s: 0, d: "ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK" }]
        await client.identifiers().interact('aid1', data)
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!
        lastBody = JSON.parse(lastCall[1]!.body!.toString())
        assert.equal(lastCall[0]!, url + '/identifiers/aid1?type=ixn')
        assert.equal(lastCall[1]!.method, 'PUT')
        assert.deepEqual(lastBody.ixn, { "v": "KERI10JSON000138_", "t": "ixn", "d": "EPtNJLDft3CB-oz3qIhe86fnTKs-GYWiWyx8fJv3VO5e", "i": "ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK", "s": "1", "p": "ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK", "a": [{ "i": "ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK", "s": 0, "d": "ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK" }] })
        assert.deepEqual(lastBody.sigs, ["AADEzKk-5LT6vH-PWFb_1i1A8FW-KGHORtTOCZrKF4gtWkCr9vN1z_mDSVKRc6MKktpdeB3Ub1fWCGpnS50hRgoJ"])

        await client.identifiers().addEndRole('aid1', 'agent')
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!
        lastBody = JSON.parse(lastCall[1]!.body!.toString())
        assert.equal(lastCall[0]!, url + '/identifiers/aid1/endroles')
        assert.equal(lastCall[1]!.method, 'POST')
        assert.equal(lastBody.rpy.t, 'rpy')
        assert.equal(lastBody.rpy.r, '/end/role/add')
        assert.deepEqual(lastBody.rpy.a, { "cid": "ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK", "role": "agent" })

        await client.identifiers().members('aid1')
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!
        assert.equal(lastCall[0]!, url + '/identifiers/aid1/members')
        assert.equal(lastCall[1]!.method, 'GET')

    })

    it('Randy identifiers', async () => {
        await libsodium.ready;
        const bran = "0123456789abcdefghijk"

        let client = new SignifyClient(url, bran, Tier.low, boot_url)

        await client.boot()
        await client.connect()

        let identifiers = client.identifiers()

        await identifiers.list()
        let lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!
        assert.equal(lastCall[0]!, url + '/identifiers')
        assert.equal(lastCall[1]!.method, 'GET')

        await client.identifiers().create('aid1', { bran: '0123456789abcdefghijk', algo: Algos.randy })
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]!
        let lastBody = JSON.parse(lastCall[1]!.body!.toString())
        assert.equal(lastCall[0]!, url + '/identifiers')
        assert.equal(lastCall[1]!.method, 'POST')
        assert.equal(lastBody.name, 'aid1')
        assert.deepEqual(lastBody.icp.s, "0")
        assert.deepEqual(lastBody.icp.kt, "1")
        assert.deepEqual(lastBody.randy.transferable, true)

    })

    it('CreateIdentiferArgs', () => {
        let args: CreateIdentiferArgs;
        args = {
            isith: 1,
            nsith: 1
        };
        args = {
            isith: "1",
            nsith: "1"
        };
        args = {
            isith: ["1"],
            nsith: ["1"]
        };
        args !== null; // avoids TS6133
    })

    it('RotateIdentifierArgs', () => {
        let args: RotateIdentifierArgs;
        args = {
            nsith: 1
        };
        args = {
            nsith: "1"
        };
        args = {
            nsith: ["1"]
        };
        args !== null; // avoids TS6133
    })



})