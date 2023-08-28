import {strict as assert} from "assert"
import { SignifyClient, Identifier, Operations, KeyEvents, KeyStates, Contacts, Notifications, Credentials, Registries, Schemas, Challenges, Escrows, Oobis} from "../../src/keri/app/signify"
import { Authenticater } from "../../src/keri/core/authing"
import { Salter, Tier } from "../../src/keri/core/salter"
import { Algos } from "../../src/keri/core/manager"
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

    it('Salty identifiers', async () => {
        await libsodium.ready;
        const bran = "0123456789abcdefghijk"

        let client = new SignifyClient(url, bran, Tier.low, boot_url)

        await client.boot()
        await client.connect()

        let identifiers = client.identifiers()

        await identifiers.list()
        let lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        assert.equal(lastCall[0]!,url+'/identifiers')
        assert.equal(lastCall[1]!.method,'GET')

        await client.identifiers().create('aid1', {bran: '0123456789abcdefghijk'})
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        let lastBody = JSON.parse(lastCall[1]!.body!.toString())
        assert.equal(lastCall[0]!,url+'/identifiers')
        assert.equal(lastCall[1]!.method,'POST')
        assert.equal(lastBody.name,'aid1')
        assert.deepEqual(lastBody.icp,{"v":"KERI10JSON00012b_","t":"icp","d":"ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK","i":"ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK","s":"0","kt":"1","k":["DPmhSfdhCPxr3EqjxzEtF8TVy0YX7ATo0Uc8oo2cnmY9"],"nt":"1","n":["EAORnRtObOgNiOlMolji-KijC_isa3lRDpHCsol79cOc"],"bt":"0","b":[],"c":[],"a":[]})
        assert.deepEqual(lastBody.sigs,["AACZZe75PvUZ1lCREPxFAcX59XHo-BGMYTAGni-I4E0eqKznrEoK2d-mtWmWHwKns7tfnjOzTfDUcv7PLFJ52g0A"])
        assert.deepEqual(lastBody.salty.pidx,0)
        assert.deepEqual(lastBody.salty.kidx,0)
        assert.deepEqual(lastBody.salty.stem,"signify:aid")
        assert.deepEqual(lastBody.salty.tier,"low")
        assert.deepEqual(lastBody.salty.icodes,["A"])
        assert.deepEqual(lastBody.salty.ncodes,["A"])
        assert.deepEqual(lastBody.salty.dcode,"E")
        assert.deepEqual(lastBody.salty.transferable,true)

        await client.identifiers().create('aid2', {count:3, ncount:3, isith:"2", nsith:"2", bran:"0123456789lmnopqrstuv"})
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        lastBody = JSON.parse(lastCall[1]!.body!.toString())
        assert.equal(lastCall[0]!,url+'/identifiers')
        assert.equal(lastCall[1]!.method,'POST')
        assert.equal(lastBody.name,'aid2')
        assert.deepEqual(lastBody.icp,{"v":"KERI10JSON0001e7_","t":"icp","d":"EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX","i":"EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX","s":"0","kt":"2","k":["DGBw7C7AfC7jbD3jLLRS3SzIWFndM947TyNWKQ52iQx5","DD_bHYFsgWXuCbz3SD0HjCIe_ITjRvEoCGuZ4PcNFFDz","DEe9u8k0fm1wMFAuOIsCtCNrpduoaV5R21rAcJl0awze"],"nt":"2","n":["EML5FrjCpz8SEl4dh0U15l8bMRhV_O5iDcR1opLJGBSH","EJpKquuibYTqpwMDqEFAFs0gwq0PASAHZ_iDmSF3I2Vg","ELplTAiEKdobFhlf-dh1vUb2iVDW0dYOSzs1dR7fQo60"],"bt":"0","b":[],"c":[],"a":[]})
        assert.deepEqual(lastBody.sigs,["AAD9_IgPaUEBjAl1Ck61Jkn78ErzsnVkIxpaFBYSdSEAW4NbtXsLiUn1olijzdTQYn_Byq6MaEk-eoMN3Oc0WEEC","ABBWJ7KkAXXiRK8JyEUpeARHJTTzlBHu_ev-jUrNEhV9sX4_4lI7wxowrQisumt5r50bUNfYBK7pxSwHk8I4IFQP","ACDTITaEquHdYKkS-94tVCxL3IYrtvhlTt__sSUavTJT6fI3KB-uwXV7L0SfzMq0gFqYxkheH2LdC4HkAW2mH4QJ"])
        assert.deepEqual(lastBody.salty.pidx,1)
        assert.deepEqual(lastBody.salty.kidx,0)
        assert.deepEqual(lastBody.salty.stem,"signify:aid")
        assert.deepEqual(lastBody.salty.tier,"low")
        assert.deepEqual(lastBody.salty.icodes,["A","A","A"])
        assert.deepEqual(lastBody.salty.ncodes,["A","A","A"])
        assert.deepEqual(lastBody.salty.dcode,"E")
        assert.deepEqual(lastBody.salty.transferable,true)

        await client.identifiers().rotate('aid1')
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        lastBody = JSON.parse(lastCall[1]!.body!.toString())
        assert.equal(lastCall[0]!,url+'/identifiers/aid1')
        assert.equal(lastCall[1]!.method,'PUT')
        assert.deepEqual(lastBody.rot,{"v":"KERI10JSON000160_","t":"rot","d":"EBQABdRgaxJONrSLcgrdtbASflkvLxJkiDO0H-XmuhGg","i":"ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK","s":"1","p":"ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK","kt":"1","k":["DHgomzINlGJHr-XP3sv2ZcR9QsIEYS3LJhs4KRaZYKly"],"nt":"1","n":["EJMovBlrBuD6BVeUsGSxLjczbLEbZU9YnTSud9K4nVzk"],"bt":"0","br":[],"ba":[],"a":[]})
        assert.deepEqual(lastBody.sigs,["AABWSckRpAWLpfFSrpnDR3SzQASrRSVKGh8AnHxauhN_43qKkqPb9l04utnTm2ixNpGGJ-UB8qdKMjfkEQ61AIQC"])
        assert.deepEqual(lastBody.salty.pidx,0)
        assert.deepEqual(lastBody.salty.kidx,1)
        assert.deepEqual(lastBody.salty.stem,"signify:aid")
        assert.deepEqual(lastBody.salty.tier,"low")
        assert.deepEqual(lastBody.salty.icodes,["A"])
        assert.deepEqual(lastBody.salty.ncodes,["A"])
        assert.deepEqual(lastBody.salty.dcode,"E")
        assert.deepEqual(lastBody.salty.transferable,true)

        let data = [{i:"ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK",s:0,d:"ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK"}]
        await client.identifiers().interact('aid1',data)
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        lastBody = JSON.parse(lastCall[1]!.body!.toString())
        assert.equal(lastCall[0]!,url+'/identifiers/aid1?type=ixn')
        assert.equal(lastCall[1]!.method,'PUT')
        assert.deepEqual(lastBody.ixn,{"v":"KERI10JSON000138_","t":"ixn","d":"EPtNJLDft3CB-oz3qIhe86fnTKs-GYWiWyx8fJv3VO5e","i":"ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK","s":"1","p":"ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK","a":[{"i":"ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK","s":0,"d":"ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK"}]})
        assert.deepEqual(lastBody.sigs,["AADEzKk-5LT6vH-PWFb_1i1A8FW-KGHORtTOCZrKF4gtWkCr9vN1z_mDSVKRc6MKktpdeB3Ub1fWCGpnS50hRgoJ"])

        await client.identifiers().addEndRole('aid1','agent')
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        lastBody = JSON.parse(lastCall[1]!.body!.toString())
        assert.equal(lastCall[0]!,url+'/identifiers/aid1/endroles')
        assert.equal(lastCall[1]!.method,'POST')
        assert.equal(lastBody.rpy.t,'rpy')
        assert.equal(lastBody.rpy.r,'/end/role/add')
        assert.deepEqual(lastBody.rpy.a,{"cid":"ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK","role":"agent"})

        await client.identifiers().members('aid1')
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        assert.equal(lastCall[0]!,url+'/identifiers/aid1/members')
        assert.equal(lastCall[1]!.method,'GET')

    })

    it('Randy identifiers', async () => {
        await libsodium.ready;
        const bran = "0123456789abcdefghijk"

        let client = new SignifyClient(url, bran, Tier.low, boot_url)

        await client.boot()
        await client.connect()

        let identifiers = client.identifiers()

        await identifiers.list()
        let lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        assert.equal(lastCall[0]!,url+'/identifiers')
        assert.equal(lastCall[1]!.method,'GET')

        await client.identifiers().create('aid1', {bran: '0123456789abcdefghijk',algo: Algos.randy})
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        let lastBody = JSON.parse(lastCall[1]!.body!.toString())
        assert.equal(lastCall[0]!,url+'/identifiers')
        assert.equal(lastCall[1]!.method,'POST')
        assert.equal(lastBody.name,'aid1')
        assert.deepEqual(lastBody.icp.s,"0")
        assert.deepEqual(lastBody.icp.kt,"1")
        assert.deepEqual(lastBody.randy.transferable,true)

    })

    it('Registries and schemas', async () => {
        await libsodium.ready;
        const bran = "0123456789abcdefghijk"

        let client = new SignifyClient(url, bran, Tier.low, boot_url)

        await client.boot()
        await client.connect()

        let registries = client.registries()

        await registries.list("aid")
        let lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        assert.equal(lastCall[0]!,url+'/identifiers/aid/registries')
        assert.equal(lastCall[1]!.method,'GET')

        await registries.create("aid", "reg1","ALGn4yvn-VoiEuKgSZcAyM-QyPHIZFHn9CKZz0DOI5ue")
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        let lastBody = JSON.parse(lastCall[1]!.body!.toString())
        assert.equal(lastCall[0]!,url+'/identifiers/aid/registries')
        assert.equal(lastCall[1]!.method,'POST')
        assert.equal(lastBody.name,"reg1")
        assert.deepEqual(lastBody.vcp,{"v":"KERI10JSON000113_","t":"vcp","d":"EG2XjQN-3jPN5rcR4spLjaJyM4zA6Lgg-Hd5vSMymu5p","i":"EG2XjQN-3jPN5rcR4spLjaJyM4zA6Lgg-Hd5vSMymu5p","ii":"ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK","s":"0","c":["NB"],"bt":"0","b":[],"n":"ALGn4yvn-VoiEuKgSZcAyM-QyPHIZFHn9CKZz0DOI5ue"})
        assert.deepEqual(lastBody.ixn,{"v":"KERI10JSON00013a_","t":"ixn","d":"EMMF0C7NyqdEUZwLhRqe6Ki4bEMwdmnDFKkejhQwQDUD","i":"ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK","s":"1","p":"ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK","a":[{"i":"EG2XjQN-3jPN5rcR4spLjaJyM4zA6Lgg-Hd5vSMymu5p","s":"0","d":"EG2XjQN-3jPN5rcR4spLjaJyM4zA6Lgg-Hd5vSMymu5p"}]})
        assert.deepEqual(lastBody.sigs,["AABtw7U9CsMBd5Iq9j5SsQsHSK3-E85SjzWCqakyTVGbO_8UrSDXjg2a6O5xsDwu2rVjhs8HsHYjMu5mOoriWQgD"])

        let schemas = client.schemas()

        await schemas.list()
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        assert.equal(lastCall[0]!,url+'/schema')
        assert.equal(lastCall[1]!.method,'GET')

        const schemaSAID = "EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao"
        await schemas.get(schemaSAID)
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        assert.equal(lastCall[0]!,url+'/schema/'+schemaSAID)
        assert.equal(lastCall[1]!.method,'GET')

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

    it('Credentials', async () => {
        await libsodium.ready;
        const bran = "0123456789abcdefghijk"

        let client = new SignifyClient(url, bran, Tier.low, boot_url)

        await client.boot()
        await client.connect()

        let credentials = client.credentials()

        let kargs = {
            filter:{"-i": {"$eq": "EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX"}},
            sort: [{"-s": 1}],
            limit: 25,
            skip: 5
        }
        await credentials.list("aid1",kargs)
        let lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        let lastBody = JSON.parse(lastCall[1]!.body!.toString())
        assert.equal(lastCall[0]!,url+'/identifiers/aid1/credentials/query')
        assert.equal(lastCall[1]!.method,'POST')
        assert.deepEqual(lastBody,kargs)

        await credentials.get("aid1","EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao",true)
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        assert.equal(lastCall[0]!,url+'/identifiers/aid1/credentials/EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao')
        assert.equal(lastCall[1]!.method,'GET')

        const registry = "EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX"
        const schema = "EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao"
        const isuee = "EG2XjQN-3jPN5rcR4spLjaJyM4zA6Lgg-Hd5vSMymu5p"
        await credentials.issue('aid1',registry,schema,isuee,{LEI: '1234'},{},{},false)
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        lastBody = JSON.parse(lastCall[1]!.body!.toString())
        assert.equal(lastCall[0]!,url+'/identifiers/aid1/credentials')
        assert.equal(lastCall[1]!.method,'POST')
        assert.equal(lastBody.cred.ri,registry)
        assert.equal(lastBody.cred.s,schema)
        assert.equal(lastBody.cred.a.i,isuee)
        assert.equal(lastBody.cred.a.LEI,'1234')
        assert.equal(lastBody.iss.s,"0")
        assert.equal(lastBody.iss.t,"iss")
        assert.equal(lastBody.iss.ri,registry)
        assert.equal(lastBody.iss.i,lastBody.cred.d)
        assert.equal(lastBody.ixn.t,"ixn")
        assert.equal(lastBody.ixn.i,lastBody.cred.i)
        assert.equal(lastBody.ixn.p,lastBody.cred.i)
        assert.equal(lastBody.path,'6AABAAA-')
        assert.equal(lastBody.csigs[0].substring(0,2),'AA')
        assert.equal(lastBody.csigs[0].length,88)
        assert.equal(lastBody.sigs[0].substring(0,2),'AA')
        assert.equal(lastBody.sigs[0].length,88)

        const credential = lastBody.cred.i
        await credentials.revoke('aid1',credential)
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        lastBody = JSON.parse(lastCall[1]!.body!.toString())
        assert.equal(lastCall[0]!,url+'/identifiers/aid1/credentials/'+credential)
        assert.equal(lastCall[1]!.method,'DELETE')
        assert.equal(lastBody.rev.s,"1")
        assert.equal(lastBody.rev.t,"rev")
        assert.equal(lastBody.rev.ri,"EGK216v1yguLfex4YRFnG7k1sXRjh3OKY7QqzdKsx7df")
        assert.equal(lastBody.rev.i,"ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK")
        assert.equal(lastBody.ixn.t,"ixn")
        assert.equal(lastBody.ixn.i,"ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK")
        assert.equal(lastBody.ixn.p,"ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK")
        assert.equal(lastBody.sigs[0].substring(0,2),'AA')
        assert.equal(lastBody.sigs[0].length,88)

        await credentials.present('aid1',credential, "EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX",false)
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        lastBody = JSON.parse(lastCall[1]!.body!.toString())
        assert.equal(lastCall[0]!,url+'/identifiers/aid1/credentials/'+credential+'/presentations')
        assert.equal(lastCall[1]!.method,'POST')
        assert.equal(lastBody.exn.t,"exn")
        assert.equal(lastBody.exn.r,"/presentation")
        assert.equal(lastBody.exn.a.n,"ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK")
        assert.equal(lastBody.exn.a.s,schema)
        assert.equal(lastBody.sig.length,144)
        assert.equal(lastBody.recipient,"EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX")
        assert.equal(lastBody.include, false)

        await credentials.request('aid1', "EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX", credential,"EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX")
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        lastBody = JSON.parse(lastCall[1]!.body!.toString())
        assert.equal(lastCall[0]!,url+'/identifiers/aid1/requests')
        assert.equal(lastCall[1]!.method,'POST')
        assert.equal(lastBody.exn.t,"exn")
        assert.equal(lastBody.exn.r,"/presentation/request")
        assert.equal(lastBody.exn.a.i,registry)
        assert.equal(lastBody.exn.a.s,"ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK")
        assert.equal(lastBody.sig.length,144)
        assert.equal(lastBody.recipient,"EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX")

    })

    it('Contacts', async () => {
        await libsodium.ready;
        const bran = "0123456789abcdefghijk"

        let client = new SignifyClient(url, bran, Tier.low, boot_url)

        await client.boot()
        await client.connect()

        let contacts = client.contacts()


        await contacts.list("mygroup","company","mycompany")
        let lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        assert.equal(lastCall[0]!,url+'/contacts?group=mygroup&company=mycompany')
        assert.equal(lastCall[1]!.method,'GET')


        await contacts.get("EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao")
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        assert.equal(lastCall[0]!,url+'/contacts/EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao')
        assert.equal(lastCall[1]!.method,'GET')

        let info = {
            "name": "John Doe",
            "company": "My Company"
        }
        await contacts.add("EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao",info)
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        let lastBody = JSON.parse(lastCall[1]!.body!.toString())
        assert.equal(lastCall[0]!,url+'/contacts/EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao')
        assert.equal(lastCall[1]!.method,'POST')
        assert.deepEqual(lastBody,info)

        await contacts.update("EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao",info)
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        lastBody = JSON.parse(lastCall[1]!.body!.toString())
        assert.equal(lastCall[0]!,url+'/contacts/EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao')
        assert.equal(lastCall[1]!.method,'PUT')
        assert.deepEqual(lastBody,info)

        await contacts.delete("EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao")
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        lastBody = JSON.parse(lastCall[1]!.body!.toString())
        assert.equal(lastCall[0]!,url+'/contacts/EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao')
        assert.equal(lastCall[1]!.method,'DELETE')

    })

    it('Challenges', async () => {
        await libsodium.ready;
        const bran = "0123456789abcdefghijk"

        let client = new SignifyClient(url, bran, Tier.low, boot_url)

        await client.boot()
        await client.connect()

        let challenges = client.challenges()


        await challenges.generate(128)
        let lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        assert.equal(lastCall[0]!,url+'/challenges?strength=128')
        assert.equal(lastCall[1]!.method,'GET')

        const words = ["shell", "gloom", "mimic", "cereal", "stool", "furnace", "nominee", "nation", "sauce", "sausage", "rather", "venue"]
        await challenges.respond("aid1","EG2XjQN-3jPN5rcR4spLjaJyM4zA6Lgg-Hd5vSMymu5p",words)
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        assert.equal(lastCall[0]!,url+'/challenges/aid1')
        assert.equal(lastCall[1]!.method,'POST')
        let lastBody = JSON.parse(lastCall[1]!.body!.toString())
        assert.deepEqual(lastBody.words,words)
        assert.equal(lastBody.recipient,"EG2XjQN-3jPN5rcR4spLjaJyM4zA6Lgg-Hd5vSMymu5p")
        assert.equal(lastBody.exn.r,"/challenge/response")
        assert.equal(lastBody.exn.a.i,"ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK")
        assert.deepEqual(lastBody.exn.a.words,words)
        assert.equal(lastBody.sig.length,144)

        await challenges.accept("aid1","EG2XjQN-3jPN5rcR4spLjaJyM4zA6Lgg-Hd5vSMymu5p","EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao")
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        assert.equal(lastCall[0]!,url+'/challenges/aid1')
        assert.equal(lastCall[1]!.method,'PUT')
        lastBody = JSON.parse(lastCall[1]!.body!.toString())
        assert.equal(lastBody.aid,"EG2XjQN-3jPN5rcR4spLjaJyM4zA6Lgg-Hd5vSMymu5p")
        assert.equal(lastBody.said,"EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao")

    })

    it('Notifications', async () => {
        await libsodium.ready;
        const bran = "0123456789abcdefghijk"

        let client = new SignifyClient(url, bran, Tier.low, boot_url)

        await client.boot()
        await client.connect()

        let notifications = client.notifications()
        let escrows = client.escrows()

        await notifications.list(20, 40)
        let lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        assert.equal(lastCall[0]!,url+'/notifications')
        assert.equal(lastCall[1]!.method,'GET')
        let lastHeaders = new Headers((lastCall[1]!.headers!))
        assert.equal(lastHeaders.get('Range'),'notes=20-40')

        await notifications.mark("notificationSAID")
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        assert.equal(lastCall[0]!,url+'/notifications/notificationSAID')
        assert.equal(lastCall[1]!.method,'PUT')

        await notifications.delete("notificationSAID")
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        assert.equal(lastCall[0]!,url+'/notifications/notificationSAID')
        assert.equal(lastCall[1]!.method,'DELETE')

        await escrows.listReply('/presentation/request')
        lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        assert.equal(lastCall[0]!,url+'/escrows/rpy?route=%2Fpresentation%2Frequest')
        assert.equal(lastCall[1]!.method,'GET')

    })

    it('Messages', async () => {
        await libsodium.ready;
        const bran = "0123456789abcdefghijk"

        let client = new SignifyClient(url,bran,Tier.low,boot_url)

        await client.boot()
        await client.connect()

        let messages = client.messages()

        await messages.list('ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose','EMQQpnSkgfUOgWdzQTWfrgiVHKIDAhvAZIPQ6z3EAfz1',0, 10)
        let lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length-1]!
        assert.equal(lastCall[0]!,url+'/messages?sender=ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose&recipient=EMQQpnSkgfUOgWdzQTWfrgiVHKIDAhvAZIPQ6z3EAfz1')
        assert.equal(lastCall[1]!.method,'GET')
        
        let lastHeaders = new Headers((lastCall[1]!.headers!))
        assert.equal(lastHeaders.get('Range'),'messages=0-10')
    })
})