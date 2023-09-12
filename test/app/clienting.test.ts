import {strict as assert} from "assert"
import { SignifyClient } from "../../src/keri/app/clienting"
import { Identifier } from "../../src/keri/app/aiding"
import { Operations, KeyEvents, KeyStates, Oobis } from "../../src/keri/app/coring"
import { Contacts, Challenges } from "../../src/keri/app/contacting"
import { Credentials, Schemas, Registries } from "../../src/keri/app/credentialing"
import { Escrows } from "../../src/keri/app/escrowing"
import { Exchanges } from "../../src/keri/app/exchanging"
import { Groups } from "../../src/keri/app/grouping"
import { Notifications  } from "../../src/keri/app/notifying"

import { Authenticater } from "../../src/keri/core/authing"
import { Salter, Tier } from "../../src/keri/core/salter"
import libsodium from "libsodium-wrappers-sumo"
import fetchMock from "jest-fetch-mock"
import 'whatwg-fetch'

fetchMock.enableMocks();

const url = "http://127.0.0.1:3901"
const boot_url = "http://127.0.0.1:3903"
const bran = "0123456789abcdefghijk"

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

describe('SignifyClient', () => {
    it('SignifyClient initialization', async () => {
        await libsodium.ready;

        let t = () => {new SignifyClient(url, 'short', Tier.low, boot_url)}
        expect(t).toThrow('bran must be 21 characters')

        let client = new SignifyClient(url, bran, Tier.low, boot_url)
        assert.equal(client.bran, "0123456789abcdefghijk")
        assert.equal(client.url, url)
        assert.equal(client.bootUrl, boot_url)
        assert.equal(client.tier, Tier.low)
        assert.equal(client.pidx, 0)
        assert.equal(client.controller.pre, "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose")
        assert.equal(client.controller.stem, "signify:controller")
        assert.equal(client.controller.tier, Tier.low)
        assert.equal(client.controller.serder.raw, '{"v":"KERI10JSON00012b_","t":"icp",'+
                                                    '"d":"ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose",' +
                                                    '"i":"ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose","s":"0",' +
                                                    '"kt":"1","k":["DAbWjobbaLqRB94KiAutAHb_qzPpOHm3LURA_ksxetVc"],' +
                                                    '"nt":"1","n":["EIFG_uqfr1yN560LoHYHfvPAhxQ5sN6xZZT_E3h7d2tL"],' +
                                                    '"bt":"0","b":[],"c":[],"a":[]}')
        assert.deepEqual(client.controller.serder.ked.s, "0")
        
        let res = await client.boot()
        assert.equal(fetchMock.mock.calls[0]![0]!,boot_url+'/boot')
        assert.equal(fetchMock.mock.calls[0]![1]!.body!.toString(),'{"icp":{"v":"KERI10JSON00012b_","t":"icp","d":"ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose","i":"ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose","s":"0","kt":"1","k":["DAbWjobbaLqRB94KiAutAHb_qzPpOHm3LURA_ksxetVc"],"nt":"1","n":["EIFG_uqfr1yN560LoHYHfvPAhxQ5sN6xZZT_E3h7d2tL"],"bt":"0","b":[],"c":[],"a":[]},"sig":"AACJwsJ0mvb4VgxD87H4jIsiT1QtlzznUy9zrX3lGdd48jjQRTv8FxlJ8ClDsGtkvK4Eekg5p-oPYiPvK_1eTXEG","stem":"signify:controller","pidx":1,"tier":"low"}')
        assert.equal(res.status, 202)
        
        await client.connect()

        // validate agent 
        assert(client.agent!.pre, 'EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei')
        assert(client.agent!.anchor, 'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose')
        assert(client.agent!.said, 'EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei')
        assert(client.agent!.state.s,'0')
        assert(client.agent!.state.d,'EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei')

        // validate approve delegation
        assert.equal(client.controller.serder.ked.s, "1")
        assert.equal(client.controller.serder.ked.t, "ixn")
        assert.equal(client.controller.serder.ked.a[0].i, "EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei")
        assert.equal(client.controller.serder.ked.a[0].d, "EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei")
        assert.equal(client.controller.serder.ked.a[0].s, "0")

        let data =client.data
        assert(data[0],url)
        assert(data[0],bran)

        assert.equal(client.identifiers() instanceof Identifier, true)
        assert.equal(client.operations() instanceof Operations, true)
        assert.equal(client.keyEvents() instanceof KeyEvents, true)
        assert.equal(client.keyStates() instanceof KeyStates, true)
        assert.equal(client.keyStates() instanceof KeyStates, true)
        assert.equal(client.credentials() instanceof Credentials, true)
        assert.equal(client.registries() instanceof Registries, true)
        assert.equal(client.schemas() instanceof Schemas, true)
        assert.equal(client.challenges() instanceof Challenges, true)
        assert.equal(client.contacts() instanceof Contacts, true)
        assert.equal(client.notifications() instanceof Notifications, true)
        assert.equal(client.escrows() instanceof Escrows, true)
        assert.equal(client.oobis() instanceof Oobis, true)
        assert.equal(client.exchanges() instanceof Exchanges, true)
        assert.equal(client.groups() instanceof Groups, true)

    })

    it('Signed fetch', async () => { 
        await libsodium.ready
        await libsodium.ready;
        const bran = "0123456789abcdefghijk"
        const client = new SignifyClient(url, bran, Tier.low, boot_url)

        await client.connect()
        
        let resp = await client.fetch('/contacts','GET', undefined)
        assert.equal(resp.status, 202)
        let lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!  
        assert.equal(lastCall[0]!,url+'/contacts')
        assert.equal(lastCall[1]!.method,'GET')
        let lastHeaders = new Headers((lastCall[1]!.headers!))
        assert.equal(lastHeaders.get('signify-resource'),'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose')

        // Headers in error
        let badAgentHeaders = {
            'signify-resource': 'bad_resource',
            'signify-timestamp': '2023-08-20T15:34:31.534673+00:00',
            'signature-input': 'signify=("signify-resource" "@method" "@path" "signify-timestamp");created=1692545671;keyid="EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei";alg="ed25519"',
            'signature': 'indexed="?0";signify="0BDiSoxCv42h2BtGMHy_tpWAqyCgEoFwRa8bQy20mBB2D5Vik4gRp3XwkEHtqy6iy6SUYAytMUDtRbewotAfkCgN"',
            'content-type': 'application/json',
        }
        fetchMock.mockResponseOnce('[]', { status: 202, headers: badAgentHeaders  })
        let t = async () => await client.fetch('/contacts','GET', undefined)
        expect(t).rejects.toThrowError('message from a different remote agent')

        badAgentHeaders = {
            'signify-resource': 'EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei',
            'signify-timestamp': '2023-08-20T15:34:31.534673+00:00',
            'signature-input': 'signify=("signify-resource" "@method" "@path" "signify-timestamp");created=1692545671;keyid="EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei";alg="ed25519"',
            'signature': 'indexed="?0";signify="0BDiSoxCv42h2BtGMHy_tpWAqyCgEoFwRa8bQy20mBB2D5Vik4gRp3XwkEHtqy6iy6SUYAytMUDtRbewotAfkCbad"',
            'content-type': 'application/json'
        }
        fetchMock.mockResponseOnce('[]', { status: 202, headers: badAgentHeaders  })
        t = async () => await client.fetch('/contacts','GET', undefined)
        expect(t).rejects.toThrowError('Signature for EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei invalid.')


        // Other calls
        resp = await client.saveOldPasscode('1234')
        assert.equal(resp.status, 202)
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        assert.equal(lastCall[0]!,url+'/salt/ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose')
        assert.equal(lastCall[1]!.method,'PUT')
        assert.equal(lastCall[1]!.body,'{"salt":"1234"}')

        resp = await client.deletePasscode()
        assert.equal(resp.status, 202)
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        assert.equal(lastCall[0]!,url+'/salt/ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose')
        assert.equal(lastCall[1]!.method,'DELETE')

        resp = await client.rotate("abcdefghijk0123456789",[])
        assert.equal(resp.status, 202)
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        assert.equal(lastCall[0]!,url+'/agent/ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose')
        assert.equal(lastCall[1]!.method,'PUT')
        let lastBody = JSON.parse(lastCall[1]!.body!)
        assert.equal(lastBody.rot.t,'rot')
        assert.equal(lastBody.rot.s,'1')
        assert.deepEqual(lastBody.rot.kt,['1','0'])
        assert.equal(lastBody.rot.d,'EGFi9pCcRaLK8dPh5S7JP9Em62fBMiR1l4gW1ZazuuAO')

        resp = await client.signedFetch('http://example.com','/test','POST',{foo:true},'aid1')
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        assert.equal(lastCall[0]!,'http://example.com/test')
        assert.equal(lastCall[1]!.method,'POST')
        lastBody = JSON.parse(lastCall[1]!.body!)
        assert.deepEqual(lastBody.foo,true)
        lastHeaders = new Headers((lastCall[1]!.headers!))
        assert.equal(lastHeaders.get('signify-resource'),'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK')

    })
    
})