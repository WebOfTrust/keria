import {strict as assert} from "assert";
import libsodium from "libsodium-wrappers-sumo"
import { randomPasscode, randomNonce } from "../../src/keri/app/coring";
import { SignifyClient } from "../../src/keri/app/clienting";
import { Authenticater } from "../../src/keri/core/authing"
import { Salter, Tier } from "../../src/keri/core/salter"
import fetchMock from "jest-fetch-mock"
import 'whatwg-fetch'

fetchMock.enableMocks();

const url = "http://127.0.0.1:3901"
const boot_url = "http://127.0.0.1:3903"

fetchMock.enableMocks();

const mockConnect = '{"agent":{"vn":[1,0],"i":"EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei",'+
                                '"s":"0","p":"","d":"EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei","f":"0",'+
                                '"dt":"2023-08-19T21:04:57.948863+00:00","et":"dip","kt":"1",'+
                                '"k":["DMZh_y-H5C3cSbZZST-fqnsmdNTReZxIh0t2xSTOJQ8a"],"nt":"1",'+
                                '"n":["EM9M2EQNCBK0MyAhVYBvR98Q0tefpvHgE-lHLs82XgqC"],"bt":"0","b":[],'+
                                '"c":[],"ee":{"s":"0","d":"EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei","br":[],"ba":[]},'+
                                '"di":"ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"},"controller":{"state":{"vn":[1,0],'+
                                '"i":"ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose","s":"0","p":"",'+
                                '"d":"ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose","f":"0","dt":"2023-08-19T21:04:57.959047+00:00",'+
                                '"et":"icp","kt":"1","k":["DAbWjobbaLqRB94KiAutAHb_qzPpOHm3LURA_ksxetVc"],"nt":"1",'+
                                '"n":["EIFG_uqfr1yN560LoHYHfvPAhxQ5sN6xZZT_E3h7d2tL"],"bt":"0","b":[],"c":[],"ee":{"s":"0",'+
                                '"d":"ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose","br":[],"ba":[]},"di":""},'+
                                '"ee":{"v":"KERI10JSON00012b_","t":"icp","d":"ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose",'+
                                '"i":"ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose","s":"0","kt":"1",'+
                                '"k":["DAbWjobbaLqRB94KiAutAHb_qzPpOHm3LURA_ksxetVc"],"nt":"1",'+
                                '"n":["EIFG_uqfr1yN560LoHYHfvPAhxQ5sN6xZZT_E3h7d2tL"],"bt":"0","b":[],"c":[],"a":[]}},"ridx":0,'+
                                '"pidx":0}'
const mockGetAID ={
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

const mockCredential = {"sad":{"v":"ACDC10JSON000197_","d":"EMwcsEMUEruPXVwPCW7zmqmN8m0I3CihxolBm-RDrsJo","i":"EMQQpnSkgfUOgWdzQTWfrgiVHKIDAhvAZIPQ6z3EAfz1","ri":"EGK216v1yguLfex4YRFnG7k1sXRjh3OKY7QqzdKsx7df","s":"EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao","a":{"d":"EK0GOjijKd8_RLYz9qDuuG29YbbXjU8yJuTQanf07b6P","i":"EKvn1M6shPLnXTb47bugVJblKMuWC0TcLIePP8p98Bby","dt":"2023-08-23T15:16:07.553000+00:00","LEI":"5493001KJTIIGC8Y1R17"}},"pre":"EMQQpnSkgfUOgWdzQTWfrgiVHKIDAhvAZIPQ6z3EAfz1","sadsigers":[{"path":"-","pre":"EMQQpnSkgfUOgWdzQTWfrgiVHKIDAhvAZIPQ6z3EAfz1","sn":0,"d":"EMQQpnSkgfUOgWdzQTWfrgiVHKIDAhvAZIPQ6z3EAfz1"}],"sadcigars":[],"chains":[],"status":{"v":"KERI10JSON000135_","i":"EMwcsEMUEruPXVwPCW7zmqmN8m0I3CihxolBm-RDrsJo","s":"0","d":"ENf3IEYwYtFmlq5ZzoI-zFzeR7E3ZNRN2YH_0KAFbdJW","ri":"EGK216v1yguLfex4YRFnG7k1sXRjh3OKY7QqzdKsx7df","ra":{},"a":{"s":2,"d":"EIpgyKVF0z0Pcn2_HgbWhEKmJhOXFeD4SA62SrxYXOLt"},"dt":"2023-08-23T15:16:07.553000+00:00","et":"iss"}}


fetchMock.mockResponse(req => {
    if (req.url.startsWith(url+'/agent')) {
        return Promise.resolve({body: mockConnect, init:{ status: 202 }})
    } else if (req.url == boot_url+'/boot') {
        return Promise.resolve({body: "", init:{ status: 202 }})
    } else {
        let headers = new Headers()
        let signed_headers = new Headers()

        headers.set('Signify-Resource', "EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei")
        headers.set('Signify-Timestamp', new Date().toISOString().replace('Z', '000+00:00'))
        headers.set('Content-Type', 'application/json')

        const requrl = new URL(req.url)
        let salter = new Salter({qb64: '0AAwMTIzNDU2Nzg5YWJjZGVm'})
        let signer = salter.signer("A",true,"agentagent-ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose00",Tier.low)

        let authn = new Authenticater(signer!,signer!.verfer)
        signed_headers = authn.sign(headers, req.method, requrl.pathname.split('?')[0])
        let body = req.url.startsWith(url+'/identifiers/aid1/credentials')? mockCredential: mockGetAID
        
        return Promise.resolve({body: JSON.stringify(body), init:{ status: 202, headers:signed_headers }})
    }

})

describe('Coring', () => {
    it('Random passcode', async () => {
        await libsodium.ready;
        let passcode = randomPasscode()
        assert.equal(passcode.length, 22)
    })

    it('Random nonce', async () => {
        await libsodium.ready;
        let nonce = randomNonce()
        assert.equal(nonce.length, 44)
    })

    it('OOBIs', async () => {
        await libsodium.ready;
        const bran = "0123456789abcdefghijk"

        let client = new SignifyClient(url, bran, Tier.low, boot_url)

        await client.boot()
        await client.connect()

        let oobis = client.oobis()

        await oobis.get("aid","agent")
        let lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        assert.equal(lastCall[0]!,url+'/identifiers/aid/oobis?role=agent')
        assert.equal(lastCall[1]!.method,'GET')

        await oobis.resolve("http://oobiurl.com")
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        let lastBody = JSON.parse(lastCall[1]!.body!.toString())
        assert.equal(lastCall[0]!,url+'/oobis')
        assert.equal(lastCall[1]!.method,'POST')
        assert.deepEqual(lastBody.url,"http://oobiurl.com")
        
        await oobis.resolve("http://oobiurl.com","witness")
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        lastBody = JSON.parse(lastCall[1]!.body!.toString())
        assert.equal(lastCall[0]!,url+'/oobis')
        assert.equal(lastCall[1]!.method,'POST')
        assert.deepEqual(lastBody.url,"http://oobiurl.com")
        assert.deepEqual(lastBody.oobialias,"witness")

    })

    it('Operations', async () => {
        await libsodium.ready;
        const bran = "0123456789abcdefghijk"

        let client = new SignifyClient(url, bran, Tier.low, boot_url)

        await client.boot()
        await client.connect()

        let ops = client.operations()

        await ops.get("operationName")
        let lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        assert.equal(lastCall[0]!,url+'/operations/operationName')
        assert.equal(lastCall[1]!.method,'GET')


    })

    it('Events and states', async () => {
        await libsodium.ready;
        const bran = "0123456789abcdefghijk"

        let client = new SignifyClient(url, bran, Tier.low, boot_url)

        await client.boot()
        await client.connect()

        let keyEvents = client.keyEvents()
        let keyStates = client.keyStates()

        await keyEvents.get("EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX")
        let lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        assert.equal(lastCall[0]!,url+'/events?pre=EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX')
        assert.equal(lastCall[1]!.method,'GET')

        await keyStates.get("EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX")
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        assert.equal(lastCall[0]!,url+'/states?pre=EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX')
        assert.equal(lastCall[1]!.method,'GET')

        await keyStates.list(["EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX","ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK"])
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        assert.equal(lastCall[0]!,url+'/states?pre=EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX&pre=ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK')
        assert.equal(lastCall[1]!.method,'GET')

        await keyStates.query("EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX",1,"EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao")
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        let lastBody = JSON.parse(lastCall[1]!.body!.toString())
        assert.equal(lastCall[0]!,url+'/queries')
        assert.equal(lastCall[1]!.method,'POST')
        assert.equal(lastBody.pre,"EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX")
        assert.equal(lastBody.sn,1)
        assert.equal(lastBody.anchor,"EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao")
    })

})