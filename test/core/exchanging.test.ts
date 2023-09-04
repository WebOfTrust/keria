import {strict as assert} from "assert";
import {b, d, Dict, Diger, exchange, Ilks, MtrDex, Salter, Serder, Tier} from "../../src";
import libsodium from "libsodium-wrappers-sumo";


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
})