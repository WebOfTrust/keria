import {Algos, Manager} from "../core/manager";
import {MtrDex} from "../core/matter";
import {Salter} from "../core/salter";
import {Verfer} from "../core/verfer";
import {Diger} from "../core/diger";
import {incept} from "../core/eventing";
import {Serder} from "../core/serder";


export class TraitCodex {
    EstOnly: string = 'EO'  // Only allow establishment events
    DoNotDelegate: string = 'DND'  // Dot not allow delegated identifiers
}

export const TraitDex = new TraitCodex()

export interface HaberyArgs {
    name: string
    passcode?: string
    seed?: string | undefined
    aeid?: string | undefined
    pidx?: number | undefined
    salt?: string | undefined
    tier?: string | undefined

}

export interface MakeHabArgs {
    code?: string
    transferable?: boolean
    isith?: string
    icount?: number
    nsith?: string
    ncount?: number
    toad?: string | number
    wits?: Array<string>
    delpre?: string
    estOnly?: boolean
    DnD?: boolean
    data?: any
}

export class Hab {
    public name: string
    public serder: Serder

    constructor(name: string, icp: Serder) {
        this.name = name
        this.serder = icp
    }

    get pre(): string {
        return this.serder.ked["i"]
    }
}


export class Habery {
    private readonly _name: string;
    private readonly _mgr: Manager;
    private readonly _habs: Map<string, Hab> = new Map<string, Hab>()

    constructor({name, passcode, seed, aeid, pidx, salt}: HaberyArgs) {
        this._name = name
        if (passcode != undefined && seed == undefined) {
            if (passcode.length < 21) {
                throw new Error("Bran (passcode seed material) too short.")
            }

            let bran = MtrDex.Salt_128 + 'A' + passcode.substring(0, 21)  // qb64 salt for seed
            let signer = new Salter({qb64: bran}).signer(MtrDex.Ed25519_Seed, false)
            seed = signer.qb64
            if (aeid == undefined) {
                aeid = signer.verfer.qb64  // lest it remove encryption
            }
        }
        let algo;

        if (salt != undefined) {
            algo = Algos.salty
            salt = new Salter({qb64: salt}).qb64
        } else {
            algo = Algos.randy
        }

        this._mgr = new Manager({seed: seed, aeid: aeid, pidx: pidx, algo: algo, salt: salt})
    }

    get mgr(): Manager {
        return this._mgr
    }

    get habs(): Array<Hab> {
        return Array.from(this._habs.values())
    }

    habByName(name: string): Hab|undefined {
        return this._habs.get(name)
    }

    makeHab(name:string, {code = MtrDex.Blake3_256, transferable = true, isith = undefined, icount = 1,
                          nsith = undefined, ncount = undefined, toad = undefined, wits = undefined, delpre = undefined,
                          estOnly = false, DnD = false, data = undefined}: MakeHabArgs): Hab {

        if (nsith == undefined) {
            nsith = isith
        }
        if (ncount == undefined) {
            ncount = icount
        }
        if (!transferable) {
            ncount = 0
            nsith = "0"
            code = MtrDex.Ed25519N
        }

        let [verfers, digers] = this._mgr.incept({
            icount: icount, ncount: ncount, stem: this.name,
            transferable: transferable, temp: false
        })

        icount = verfers.length
        ncount = digers != undefined ? digers.length : 0
        if (isith == undefined) {
            isith = `${Math.max(1, Math.ceil(icount/2)).toString(16)}`
        }
        if (nsith == undefined) {
            nsith = `${Math.max(1, Math.ceil(ncount/2)).toString(16)}`
        }

        let cnfg = new Array<string>()
        if (estOnly) {
            cnfg.push(TraitDex.EstOnly)
        }
        if(DnD) {
            cnfg.push(TraitDex.DoNotDelegate)
        }

        let keys = Array.from(verfers, (verfer: Verfer) => verfer.qb64)
        let ndigs = Array.from(digers, (diger: Diger) => diger.qb64)


        const icp = incept({keys, isith, ndigs, nsith, toad, wits, cnfg, data, code, delpre})
        const hab = new Hab(name, icp)
        this._habs.set(name, hab)
        return hab
    }

    get name(): string {
        return this._name
    }
}