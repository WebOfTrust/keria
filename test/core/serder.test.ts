export {};
const assert = require('assert').strict;

const {Serder} = require('../../src/keri/core/serder');
const {
    versify,
    Serials,
    Versionage,
    Ilks,
} = require('../../src/keri/core/core');

const {TraitCodex} = require("../../src/keri/eventing/TraitCodex")

// const msgpack = require('msgpack5')();
// const {encode} = msgpack;
// const {decode} = msgpack;

describe('Serder', () => {
    // it('should create Serder objects', async () => {
    //     const e1 = {
    //         v: versify(null, Serials.json, 0),
    //         i: 'ABCDEFG',
    //         s: '0001',
    //         t: 'rot',
    //     };
    //     console.log('e1 is --------------------->', e1);
    //     const Version = Versionage;
    //
    //     const serder = new Serder(null, e1);
    //     serder.set_kind();
    //
    //     serder.set_raw(Buffer.from(JSON.stringify(e1), 'binary'));
    //
    //     assert.deepStrictEqual(serder.getKed, e1);
    //     assert.deepStrictEqual(serder.getKind, Serials.json);
    //     assert.deepStrictEqual(serder.version(), Version);
    //
    //     assert.deepStrictEqual(
    //         serder.dig(),
    //         'EaDVEkrFdx8W0ZZAsfwf9mjxhgBt6PvfCmFPdr7RIcfY',
    //     );
    //     assert.deepStrictEqual(
    //         serder.digb(),
    //         Buffer.from('EaDVEkrFdx8W0ZZAsfwf9mjxhgBt6PvfCmFPdr7RIcfY', 'binary'),
    //     );
    //     assert.deepStrictEqual(serder.size(), 66);
    //     assert.deepStrictEqual(
    //         serder.raw(),
    //         Buffer.from(
    //             '{"vs":"KERI10JSON000042_","pre":"ABCDEFG","sn":"0001","ilk":"rot"}',
    //             'binary',
    //         ),
    //     );
    //
    //     // ------------------------- SERDER VERFER IS PENDING -----------------------
    //     assert.deepStrictEqual(serder.verfers(), []);
    //
    //     const e1s = Buffer.from(JSON.stringify(e1), 'binary');
    //     console.log('Els length is ------>', e1s.length);
    //     let vs = versify(null, Serials.json, e1s.length);
    //     assert.equal(vs, 'KERI10JSON000042_');
    //
    //     // // let   [kind1, vers1, size1] = serder._sniff(e1s.slice(0,VERFULLSIZE))
    //     // //  console.log("e1s[:MINSNIFFSIZE] =========================>",e1s.slice(0,VERFULLSIZE))
    //     // let [kind1, vers1, size1] = serder._sniff(e1s.slice(0,MINSNIFFSIZE ))
    //     // // assert.deepStrictEqual(kind1,Serials.json)
    //     // // assert.deepStrictEqual(size1,66)
    //
    //     const [kind1, vers1, size1] = serder.sniff(e1s);
    //     // assert.deepStrictEqual(kind1,Serials.json)
    //     //  assert.deepStrictEqual(size1,66)
    //     // const e1ss = e1s + Buffer.from('extra attached at the end.', 'binary');
    //     const e1ss = e1s;
    //     const [ked1, knd1, vrs1, siz1] = serder.inhale(e1ss);
    //     assert.deepStrictEqual(ked1, e1);
    //     assert.deepStrictEqual(knd1, kind1);
    //     assert.deepStrictEqual(vrs1, vers1);
    //     assert.deepStrictEqual(siz1, size1);
    //
    //     const [raw1, knd2, ked2, ver1] = serder.exhale(e1);
    //     assert.deepStrictEqual(Buffer.from(raw1, 'binary'), e1s);
    //     assert.deepStrictEqual(knd2, kind1);
    //     assert.deepStrictEqual(ked2, e1);
    //     assert.deepStrictEqual(vrs1, vers1);
    //     console.log(ver1)
    //
    //     const e2 = {
    //         vs: versify(null, Serials.json, 0),
    //         pre: 'ABCDEFG',
    //         sn: '0001',
    //         ilk: 'rot',
    //     };
    //     e2.vs = versify(null, Serials.mgpk, 0);
    //     console.log('==========================>', e2.vs);
    //     const e2s = encode(e2);
    //     const e2s1 = e2s;
    //     const msgBuffer = Buffer.from(
    //         '\x84\xa2vs\xb1KERI10MGPK000000_\xa3pre\xa7ABCDEFG\xa2sn\xa40001\xa3ilk\xa3rot',
    //         'binary',
    //     );
    //     assert.deepStrictEqual(e2s, msgBuffer);
    //
    //     vs = versify(null, Serials.mgpk, e2s.length); // # use real length
    //     assert.deepStrictEqual(vs, 'KERI10MGPK000032_');
    //     e2s1.vs = versify(null, Serials.mgpk, e2s.length);
    //     assert.deepStrictEqual(e2s1, e2s);
    //     // console.log("e2s ==========+>",decode(e2s))
    //     // console.log("e2 ==========+>",encode(e2))
    //     // console.log("if true or false ",(e2s == encode(e2)))
    //     assert.deepStrictEqual(decode(e2s), e2);
    //
    //     const e3 = {
    //         vs: versify(null, Serials.json, 0),
    //         pre: 'ABCDEFG',
    //         sn: '0001',
    //         ilk: 'rot',
    //     };
    //     e3.vs = versify(null, Serials.cbor, 0);
    //     // let e3s = cbor.encode(e3);
    //     // assert.deepEqual(
    //     //     e3s,
    //     //     Buffer.from(
    //     //         '\xa4bvsqKERI10CBOR000000_cpregABCDEFGbsnd0001cilkcrot',
    //     //         'binary',
    //     //     ),
    //     // );
    //     // vs = versify(null, Serials.cbor, e3s.length); // # use real length
    //     // assert.equal(vs, 'KERI10CBOR000032_');
    //     // e3.vs = vs; // # has real length
    //
    //     // const e5 = {
    //     //   vs: versify(null, Serials.cbor, 0),
    //     //   pre: 'ABCDEFG',
    //     //   sn: '0001',
    //     //   ilk: 'rot',
    //     // };
    //     // e3s = cbor.encode(e3);
    //     // console.log('e3s =============>', cbor.decode(e3s));
    //     // const [kind3, vers3, size3] = serder.sniff(e3s.slice(0, MINSNIFFSIZE));
    //     // assert.deepStrictEqual(kind3, Serials.cbor);
    //     // assert.equal(size3, 50);
    //
    //     // const [kind3a, vers3a, size3a] = serder.sniff(e3s);
    //     // console.log(vers3a)
    //     // assert.deepStrictEqual(kind3a, Serials.cbor);
    //     // assert.deepStrictEqual(size3a, 50);
    //     // let e3ss = cbor.encode(e3) +
    //     // const encodedText = cbor.encode('extra attached at the end.');
    //     // const encodedE3 = cbor.encode(e3);
    //     // const e3ss = Buffer.concat([encodedE3, encodedText]);
    //     // console.log('DECODING CBROR', e3ss);
    //
    //     // const [ked3b, knd3b, vrs3b, siz3b] = serder.inhale(e3ss);
    //     //
    //     // // --------------------- This case is getting failed ---------------------
    //     // assert.deepStrictEqual(ked3b[0], e3);
    //     // // ----------------------------
    //     // assert.deepStrictEqual(knd3b, kind3);
    //     // assert.deepStrictEqual(vrs3b, vers3);
    //     // assert.deepStrictEqual(siz3b, size3);
    //     //
    //     // // # with pytest.raises(ShortageError):  # test too short
    //     // // #     ked3, knd3, vrs3, siz3 = serder._inhale(e3ss[:size3-1])
    //     // console.log('e3 is- --------->', e5);
    //     // let [raw3c, knd3c, ked3c, ver3c] = serder.exhale(e5);
    //     // assert.deepStrictEqual(raw3c, e3s);
    //     // assert.deepStrictEqual(knd3c, kind3);
    //     // assert.deepStrictEqual(ked3c, e3);
    //     // assert.deepStrictEqual(vrs3b, vers3a);
    //
    //     // console.log(
    //     //   "versify(null,Serials.json,0) =================>",
    //     //   versify(null, Serials.json, 0)
    //     // );
    //     // let e7 = {
    //     //   vs: versify(null, Serials.json, e1s.length),
    //     //   pre: "ABCDEFG",
    //     //   sn: "0001",
    //     //   ilk: "rot",
    //     // };
    //     // let t =
    //     //   Buffer.from(JSON.stringify(e7), "binary") +
    //     //   Buffer.from("extra attached at the end.", "binary");
    //     // console.log("vaue of t is --->", t);
    //     // let evt1 = new Serder(t);
    //     // evt1.set_raw(t);
    //     // console.log("e3ss =============>", t);
    //     // assert.deepStrictEqual(evt1.kind(), kind1);
    //     // assert.deepStrictEqual(evt1.raw(), e1s);
    //     // assert.deepStrictEqual(evt1.ked(), ked1);
    //     // assert.deepStrictEqual(evt1.size(), size1);
    //     // assert.deepStrictEqual(evt1.raw().toString(), t.slice(0, size1));
    //     // assert.deepStrictEqual(evt1.version(), vers1);
    //
    //     // # # test digest properties .diger and .dig
    //     // # assert evt1.diger.qb64 == evt1.dig
    //     // # assert evt1.diger.code == CryOneDex.Blake3_256
    //     // # assert len(evt1.diger.raw) == 32
    //     // # assert len(evt1.dig) == 44
    //     // # assert len(evt1.dig) == CryOneSizes[CryOneDex.Blake3_256]
    //     // # assert evt1.dig == 'EaDVEkrFdx8W0ZZAsfwf9mjxhgBt6PvfCmFPdr7RIcfY'
    //     // # assert evt1.diger.verify(evt1.raw)
    //
    //     // console.log(
    //     //   "versify(null,Serials.json,0) =================>",
    //     //   versify(null, Serials.json, 0)
    //     // );
    //     //  e7 = {
    //     //   vs: versify(null, Serials.json, e1s.length),
    //     //   pre: "ABCDEFG",
    //     //   sn: "0001",
    //     //   ilk: "rot",
    //     // };
    //     //  t =
    //     //   Buffer.from(JSON.stringify(e7), "binary") +
    //     //   Buffer.from("extra attached at the end.", "binary");
    //     // console.log("vaue of t is --->", t);
    //     //  evt1 = new Serder(null, ked1);
    //     // evt1.set_raw(t);
    //     // assert.deepStrictEqual(evt1.kind(), kind1);
    //     // assert.deepStrictEqual(evt1.raw(), e1s);
    //     // assert.deepStrictEqual(evt1.ked(), ked1);
    //     // assert.deepStrictEqual(evt1.size(), size1);
    //     // assert.deepStrictEqual(evt1.raw().toString(), t.slice(0, size1));
    //     // assert.deepStrictEqual(evt1.version(), vers1);
    //
    //     // let evt2 = new  Serder(e2ss)
    //     // # assert evt2.kind == kind2
    //     // # assert evt2.raw == e2s
    //     // # assert evt2.ked == ked2
    //     // # assert evt2.version == vers2
    //
    //     // # evt2 = Serder(ked=ked2)
    //     // # assert evt2.kind == kind2
    //     // # assert evt2.raw == e2s
    //     // # assert evt2.ked == ked2
    //     // # assert evt2.size == size2
    //     // # assert evt2.raw == e2ss[:size2]
    //     // # assert evt2.version == vers2
    //
    //     // # evt3 = Serder(raw=e3ss)
    //     // # assert evt3.kind == kind3
    //     // # assert evt3.raw == e3s
    //     // # assert evt3.ked == ked3
    //     // # assert evt3.version == vers3
    //
    //     // # evt3 = Serder(ked=ked3)
    //     // # assert evt3.kind == kind3
    //     // # assert evt3.raw == e3s
    //     // # assert evt3.ked == ked3
    //     // # assert evt3.size == size3
    //     // # assert evt3.raw == e3ss[:size3]
    //     // # assert evt3.version == vers3
    //
    //     // # #  round trip
    //     // # evt2 = Serder(ked=evt1.ked)
    //     // # assert evt2.kind == evt1.kind
    //     // # assert evt2.raw == evt1.raw
    //     // # assert evt2.ked == evt1.ked
    //     // # assert evt2.size == evt1.size
    //     // # assert evt2.version == vers2
    //
    //     // # # Test change in kind by Serder
    //     // # evt1 = Serder(ked=ked1, kind=Serials.mgpk)  # ked is json but kind mgpk
    //     // # assert evt1.kind == kind2
    //     // # assert evt1.raw == e2s
    //     // # assert evt1.ked == ked2
    //     // # assert evt1.size == size2
    //     // # assert evt1.raw == e2ss[:size2]
    //     // # assert evt1.version == vers1
    //
    //     // # #  round trip
    //     // # evt2 = Serder(raw=evt1.raw)
    //     // # assert evt2.kind == evt1.kind
    //     // # assert evt2.raw == evt1.raw
    //     // # assert evt2.ked == evt1.ked
    //     // # assert evt2.size == evt1.size
    //     // # assert evt2.version == vers2
    //
    //     // # evt1 = Serder(ked=ked1, kind=Serials.cbor)  # ked is json but kind mgpk
    //     // # assert evt1.kind == kind3
    //     // # assert evt1.raw == e3s
    //     // # assert evt1.ked == ked3
    //     // # assert evt1.size == size3
    //     // # assert evt1.raw == e3ss[:size3]
    //     // # assert evt1.version == vers1
    //
    //     // # #  round trip
    //     // # evt2 = Serder(raw=evt1.raw)
    //     // # assert evt2.kind == evt1.kind
    //     // # assert evt2.raw == evt1.raw
    //     // # assert evt2.ked == evt1.ked
    //     // # assert evt2.size == evt1.size
    //     // # assert evt2.version == vers2
    //
    //     // # # use kind setter property
    //     // # assert evt2.kind == Serials.cbor
    //     // # evt2.kind = Serials.json
    //     // # assert evt2.kind == Serials.json
    //     // # knd, version, size = Deversify(evt2.ked['vs'])
    //     // # assert knd == Serials.json
    //     // """Done Test """
    // });
});


describe('Serder', () => {
    it('should create Serder objects', async () => {
        const nxt = "E2k1CecxqNtJq8sNVJ0UisOwDgRW7n3MB1-mw3If8c2U"
        const icp = {
            v: versify(null, Serials.json, 0),
            i: '',
            s: '0',
            t: Ilks.icp,
            kt: "1",
            k: [],  // Add generated public keys here
            n: nxt,
            bt: "1",
            b: [],
            c: [TraitCodex.EstOnly],
            a: []

        };
        // console.log('icp is --------------------->', icp);

        const Version = Versionage;

        const serder = new Serder(null, icp);
        serder.set_kind();
        assert.deepStrictEqual(serder.getKed, icp);
        assert.deepStrictEqual(serder.getKind, Serials.json);
        assert.deepStrictEqual(serder.version(), Version);

        console.log(serder.dig())
        assert.deepStrictEqual(
            serder.dig(),
            "ETzQBq0omlsr15K0gQcvHzhVLlK7UbF2gjLusXDrjusg",
        );
    });
});