import {Encrypter} from "./encrypter"
import {Decrypter} from "./decrypter"
import {Salter, Tier} from "./salter"
import {Signer} from "./signer"
import {Verfer} from "./verfer";
import {MtrDex} from "./matter";
import {Diger} from "./diger";
import {Cigar} from "./cigar";
import {Siger} from "./siger";
import {b} from "./core";


export enum Algos {
    randy = "randy",
    salty = "salty"
}

class PubLot {
    public pubs: Array<string> = new Array<string>()  // list qb64 public keys.
    public ridx: number = 0  //  index of rotation (est event) that uses public key set
    public kidx: number = 0  //  index of key in sequence of public keys
    public dt:string = ""    // datetime ISO8601 when key set created
}

class PreSit {
    public old: PubLot = new PubLot()  //previous publot
    public new: PubLot = new PubLot()  //newly current publot
    public nxt: PubLot = new PubLot()  //next public publot
}

class PrePrm {
    public pidx: number = 0  // prefix index for this keypair sequence
    public algo: Algos = Algos.salty  // salty default uses indices and salt to create new key pairs
    public salt: string = ''  // empty salt  used for salty algo.
    public stem: string = ''  // default unique path stem for salty algo
    public tier: string = ''  // security tier for stretch index salty algo

}

class PubSet {
    pubs: Array<string> = new Array<string>() // list qb64 public keys.
}

class PubPath {
    path: string = ""
    code: string = ""
    tier: string = Tier.high
    temp: boolean = false
}

class Keys {
    private readonly _signers: Array<Signer>
    private readonly _paths?: Array<string>

    constructor(signers: Array<Signer>, paths?: Array<string>) {
        this._signers = signers
        if (paths != undefined) {
            if (signers.length != paths.length) {
                throw new Error("If paths are provided, they must be the same length as signers")
            }
        }
        this._paths = paths
    }

    get paths(): Array<string> | undefined {
        return this._paths;
    }

    get signers(): Array<Signer> {
        return this._signers;
    }
}

export interface Creator {
    create(codes: Array<string> | undefined, count: number, code: string, transferable: boolean, pidx: number,
           ridx: number, kidx: number, temp: boolean): Keys
    salt: string
    stem: string
    tier: Tier
}

export class RandyCreator implements Creator {

    create(codes: Array<string> | undefined = undefined, count: number = 1, code: string = MtrDex.Ed25519_Seed,
           transferable: boolean = true): Keys {
        let signers = new Array<Signer>()
        if (codes == undefined) {
            codes = new Array(count).fill(code)
        }

        codes.forEach(function(code) {
            signers.push(new Signer({code: code, transferable: transferable}))
        })

        return new Keys(signers)
    }

    get salt(): string {
        return "";
    }

    get stem(): string {
        return "";
    }

    get tier(): Tier {
        return "" as Tier;
    }
}

export class SaltyCreator implements Creator {

    public salter: Salter
    private readonly _stem: string
    constructor(salt: string | undefined = undefined, tier: Tier | undefined = undefined,
                stem: string | undefined = undefined) {

        this.salter = new Salter({qb64: salt, tier: tier})
        this._stem = stem == undefined ? "" : stem

    }

    get salt(): string {
        return this.salter.qb64;
    }

    get stem(): string {
        return this._stem;
    }

    get tier(): Tier {
        return this.salter.tier!;
    }

    create(codes: Array<string> | undefined = undefined, count: number = 1, code: string = MtrDex.Ed25519_Seed,
           transferable: boolean = true,  pidx: number = 0, ridx: number = 0, kidx: number = 0,
           temp: boolean = false): Keys {

        let signers =  new Array<Signer>()
        let paths = new Array<string>()

        if (codes == undefined) {
            codes = new Array<string>(count).fill(code)
        }

        codes.forEach((code, idx) => {
            let path = this.stem + pidx.toString(16) + ridx.toString(16) + (kidx+idx).toString(16)
            signers.push(this.salter.signer(code, transferable, path, this.tier, temp))
            paths.push(path)
        })

        return new Keys(signers, paths)
    }
}

export class Creatory {
    private readonly _make: any
    constructor(algo: Algos = Algos.salty) {
        switch(algo) {
            case Algos.randy:
                this._make = this._makeRandy
                break;
            case Algos.salty:
                this._make = this._makeSalty
                break;
            default:
                throw new Error(`unsupported algo=${algo}`)
        }
    }

    make(...args: any[]): Creator {
        return this._make(...args)
    }

    _makeRandy(): Creator {
        return new RandyCreator()
    }

    _makeSalty(...args: any[]): Creator {
        return new SaltyCreator(...args)
    }
}

export function openManager(passcode: string, salt?: string) {
    if (passcode.length < 21) {
        throw new Error("Bran (passcode seed material) too short.")
    }

    let bran = MtrDex.Salt_128 + 'A' + passcode.substring(0, 21)  // qb64 salt for seed
    let signer = new Salter({qb64: bran}).signer(MtrDex.Ed25519_Seed, false)
    let seed = signer.qb64
    let aeid = signer.verfer.qb64  // lest it remove encryption

    let algo;

    if (salt != undefined) {
        algo = Algos.salty
        salt = new Salter({qb64: salt}).qb64
    } else {
        algo = Algos.randy
    }

    return new Manager({seed: seed, aeid: aeid, algo: algo, salt: salt})
}

export interface ManagerArgs {
    ks?: KeyStore | undefined
    seed?: string | undefined
    aeid?: string | undefined
    pidx?: number | undefined
    algo?: Algos | undefined
    salt?: string | undefined
    tier?: string | undefined
}

export interface InceptArgs {
    icodes?: any | undefined
    icount?: number
    icode?: string
    ncodes?: any | undefined
    ncount?: number
    ncode?: string
    dcode?: string
    algo?: Algos | undefined
    salt?: string | undefined
    stem?: string | undefined
    tier?: string | undefined
    rooted?: boolean
    transferable?: boolean
    temp?: boolean
}

interface RotateArgs {
    pre: string
    ncodes?: any | undefined
    ncount?: number
    ncode?: string
    dcode?: string
    transferable?: boolean
    temp?: boolean
    erase?: boolean
}

interface SignArgs {
    ser: Uint8Array
    pubs?: Array<string> | undefined
    verfers?: Array<Verfer> | undefined
    indexed?: boolean
    indices?: Array<number> | undefined
    ondices?: Array<number> | undefined
}

export class Manager {
    private _seed?: string
    private _salt?: string
    private _encrypter: Encrypter | undefined
    private _decrypter: Decrypter | undefined
    private readonly _ks: KeyStore

    constructor({ks, seed, aeid, pidx, algo, salt, tier}: ManagerArgs) {

        this._ks = ks == undefined ? new Keeper() : ks
        this._seed = seed
        this._encrypter = undefined
        this._decrypter = undefined

        aeid = aeid == undefined ? undefined : aeid
        pidx = pidx == undefined ? 0 : pidx
        algo = algo == undefined ? Algos.salty : algo

        if (salt == undefined) {
            salt = new Salter({}).qb64
        } else {
            if (new Salter({qb64: salt}).qb64 != salt) {
                throw new Error(`Invalid qb64 for salt=${salt}.`)
            }
        }

        tier = tier == undefined ? Tier.low : tier

        if (this.pidx == undefined) {
            this.pidx = pidx
        }

        if (this.algo == undefined) {
            this.algo = algo
        }

        if (this.salt == undefined) {
            this.salt = salt
        }

        if (this.tier == undefined) {
            this.tier = tier
        }

        if (this.aeid == undefined) {
            this.updateAeid(aeid, this._seed)
        }
    }

    get ks(): KeyStore {
        return this._ks
    }

    get encrypter(): Encrypter | undefined {
        return this._encrypter
    }

    get decrypter(): Decrypter | undefined {
        return this._decrypter
    }

    get seed(): string | undefined {
        return this._seed
    }

    get aeid(): string | undefined {
        return this.ks.getGbls('aeid')
    }

    get pidx(): number | undefined {
        let pidx = this.ks.getGbls('pidx')
        if (pidx != undefined) {
            return parseInt(pidx, 16)
        }
        return undefined
    }

    set pidx(pidx: number | undefined) {
        this.ks.pinGbls('pidx', pidx!.toString(16))
    }

    get salt(): string  | undefined {
        if (this._decrypter == undefined) {
            return this._salt
        } else {
            let salt = this.ks.getGbls('salt')
            return this._decrypter.decrypt(b(salt)).qb64
        }
    }

    set salt(salt: string | undefined) {
        if(this._encrypter == undefined) {
            this._salt = salt
        } else {
            salt = this._encrypter.encrypt(b(salt)).qb64
            this.ks.pinGbls('salt', salt!)
        }
    }

    get tier(): string | undefined {
        return this.ks.getGbls('tier')
    }

    set tier(tier: string | undefined) {
        this.ks.pinGbls('tier', tier!)
    }

    get algo(): Algos | undefined {
        let a = this.ks.getGbls('algo')
        let ta = a as keyof typeof Algos
        return Algos[ta]
    }

    set algo(algo: Algos | undefined) {
        this.ks.pinGbls('algo', algo! as string)
    }

    private updateAeid(aeid: string | undefined, seed?: string) {
        if (this.aeid != undefined) {
            let seed = b(this._seed)
            if (this._seed == undefined || !this._encrypter?.verifySeed(seed)) {
                throw new Error(`Last seed missing or provided last seed "
                                       "not associated with last aeid=${this.aeid}.`)
            }
        }

        if (aeid != "" && aeid != undefined) {
            if (aeid != this.aeid) {
                this._encrypter = new Encrypter({}, b(aeid))
                if (seed == undefined || !this._encrypter.verifySeed(b(seed))) {
                    throw new Error(`Seed missing or provided seed not associated"
                                           "  with provided aeid=${aeid}.`)
                }
            }
        } else if (this.algo == Algos.randy) {
            // Unlike KERIpy, we don't support unencrypted secrets
            throw new Error("Invalid Manager configuration, encryption must be used with Randy key creation.")
        } else {
            this._encrypter = undefined
        }

        let salt = this.salt
        if(salt != undefined) {
            this.salt = salt
        }

        if (this._decrypter != undefined) {
            for (const [keys, data] of this.ks.prmsElements()) {
                if (data.salt != undefined) {
                    let salter = this._decrypter.decrypt(b(data.salt))
                    data.salt = this._encrypter == undefined ? salter.qb64 : this._encrypter.encrypt(null, salter)
                    this.ks.pinPrms(keys, data)
                }
            }

            for (const [pubKey, signer] of this.ks.prisElements(this._decrypter)) {
                this.ks.pinPris(pubKey, signer, this._encrypter!)
            }

        }

        this.ks.pinGbls("aeid", aeid!)  // set aeid in db
        this._seed = seed  // set .seed in memory

        // update .decrypter
        this._decrypter = seed != undefined ? new Decrypter({}, b(seed)) : undefined
    }

    incept({icodes=undefined, icount=1, icode=MtrDex.Ed25519_Seed,
            ncodes=undefined, ncount=1, ncode=MtrDex.Ed25519_Seed,
            dcode=MtrDex.Blake3_256, algo=undefined, salt=undefined, stem=undefined, tier=undefined,
            rooted=true, transferable=true, temp=false }: InceptArgs): [Array<Verfer>, Array<Diger>] {

        if (rooted && algo == undefined) {
            algo = this.algo
        }
        if (rooted && salt == undefined) {
            salt = this.salt
        }
        if (rooted && tier == undefined) {
            tier = this.tier
        }

        let pidx = this.pidx!
        let ridx = 0
        let kidx = 0

        let creator = new Creatory(algo).make(salt, tier, stem)

        if (icodes == undefined) {
            if (icount < 0) {
                throw new Error(`Invalid icount=${icount} must be >= 0.`)
            }

            icodes = new Array<string>(icount).fill(icode)
        }

        let ikeys = creator.create(icodes, 0, MtrDex.Ed25519_Seed, transferable, pidx, ridx, kidx, temp)
        let verfers = Array.from(ikeys.signers, (signer: Signer) => signer.verfer)

        if (ncodes == undefined) {
            if (ncount < 0) {
                throw new Error(`Invalid ncount=${ncount} must be >= 0.`)
            }

            ncodes = new Array<string>(ncount).fill(ncode)
        }

        let nkeys = creator.create(ncodes, 0, MtrDex.Ed25519_Seed, transferable, pidx, ridx+1, kidx+icodes.length,
            temp)

        let digers = Array.from(nkeys.signers, (signer: Signer) => new Diger({code: dcode}, signer.verfer.qb64b))

        let pp = new PrePrm()
        pp.pidx = pidx!
        pp.algo = algo!
        pp.salt = creator.salt.length == 0 || this.encrypter == undefined ? "" : this.encrypter.encrypt(b(creator.salt)).qb64
        pp.stem = creator.stem
        pp.tier = creator.tier

        let dt = new Date().toString()
        let nw = new PubLot()
        nw.pubs = Array.from(verfers, (verfer: Verfer) => verfer.qb64)
        nw.ridx = ridx
        nw.kidx = kidx
        nw.dt = dt

        let nt = new PubLot()
        nt.pubs = Array.from(nkeys.signers, (signer: Signer) => signer.verfer.qb64)
        nt.ridx = ridx + 1
        nt.kidx = kidx + icodes.length
        nt.dt = dt

        let ps = new PreSit()
        ps.new = nw
        ps.nxt = nt

        let pre = verfers[0].qb64
        if (!this.ks.putPres(pre, verfers[0].qb64b)) {
            throw new Error(`Already incepted pre=${pre}.`)
        }

        if (!this.ks.putPrms(pre, pp)) {
            throw new Error(`Already incepted prm for pre=${pre}.`)
        }

        this.pidx = pidx! + 1

        if (!this.ks.putSits(pre, ps)) {
            throw new Error(`Already incepted sit for pre=${pre}.`)
        }

        if (this.encrypter != undefined) { // Only store encrypted keys if we have an encrypter, otherwise regenerate
            ikeys.signers.forEach((signer: Signer) => {
                this.ks.putPris(signer.verfer.qb64, signer, this.encrypter!)
            })

            nkeys.signers.forEach((signer: Signer) => {
                this.ks.putPris(signer.verfer.qb64, signer, this.encrypter!)
            })
        } else if (this._encrypter == undefined && ikeys.paths != undefined && nkeys.paths != undefined) {
            ikeys.paths.forEach((path: string, idx: number) => {
                let signer = ikeys.signers[idx]
                let ppt = new PubPath()
                ppt.path = path
                ppt.code = icodes[idx]
                ppt.tier = pp.tier
                ppt.temp = temp
                this.ks.putPths(signer.verfer.qb64, ppt)
            })
            nkeys.paths.forEach((path: string, idx: number) => {
                let signer = nkeys.signers[idx]
                let ppt = new PubPath()
                ppt.path = path
                ppt.code = ncodes[idx]
                ppt.tier = pp.tier
                ppt.temp = temp
                this.ks.putPths(signer.verfer.qb64, ppt)
            })
        } else {
            throw new Error("invalid configuration, randy keys without encryption")
        }

        let pubSet = new PubSet()
        pubSet.pubs = ps.new.pubs
        this.ks.putPubs(riKey(pre, ridx), pubSet)

        let nxtPubSet = new PubSet()
        nxtPubSet.pubs = ps.nxt.pubs
        this.ks.putPubs(riKey(pre, ridx+1), nxtPubSet)

        return [verfers, digers]
    }

    move(old: string, gnu: string) {
        if (old == gnu) {
            return
        }

        if (this.ks.getPres(old) == undefined) {
            throw new Error(`Nonexistent old pre=${old}, nothing to assign.`)
        }

        if (this.ks.getPres(gnu) != undefined) {
            throw new Error(`Preexistent new pre=${gnu} may not clobber.`)
        }

        let oldprm = this.ks.getPrms(old)
        if (oldprm == undefined) {
            throw new Error(`Nonexistent old prm for pre=${old}, nothing to move.`)
        }

        if (this.ks.getPrms(gnu) != undefined) {
            throw new Error(`Preexistent new prm for pre=${gnu} may not clobber.`)
        }

        let oldsit = this.ks.getSits(old)
        if (oldsit == undefined) {
            throw new Error(`Nonexistent old sit for pre=${old}, nothing to move.`)
        }

        if (this.ks.getSits(gnu) != undefined) {
            throw new Error(`Preexistent new sit for pre=${gnu} may not clobber.`)
        }

        if (!this.ks.putPrms(gnu, oldprm)) {
            throw new Error(`Failed moving prm from old pre=${old} to new pre=${gnu}.`)
        } else {
            this.ks.remPrms(old)
        }

        if (!this.ks.putSits(gnu, oldsit)) {
            throw new Error(`Failed moving sit from old pre=${old} to new pre=${gnu}.`)
        } else {
            this.ks.remSits(old)
        }

        let i = 0
        while (true) {
            let pl = this.ks.getPubs(riKey(old, i))
            if (pl == undefined) {
                break
            }

            if (!this.ks.putPubs(riKey(gnu, i), pl)) {
                throw new Error(`Failed moving pubs at pre=${old} ri=${i} to new pre=${gnu}`)
            }
            i = i + 1
        }

        if (!this.ks.pinPres(old, b(gnu))) {
            throw new Error(`Failed assiging new pre=${gnu} to old pre=${old}.`)
        }

        if (!this.ks.putPres(gnu, b(gnu))) {
            throw new Error(`Failed assiging new pre=${gnu}.`)
        }
    }

    rotate({pre, ncodes=undefined, ncount=1, ncode=MtrDex.Ed25519_Seed, dcode=MtrDex.Blake3_256,
           transferable=true, temp=false, erase=true}:RotateArgs):  [Array<Verfer>, Array<Diger>] {
        let pp = this.ks.getPrms(pre)
        if (pp == undefined) {
            throw new Error(`Attempt to rotate nonexistent pre=${pre}.`)
        }

        let ps = this.ks.getSits(pre)
        if (ps == undefined) {
            throw new Error(`Attempt to rotate nonexistent pre=${pre}.`)
        }

        if (ps.nxt.pubs == undefined || ps.nxt.pubs.length == 0) {
            throw new Error(`Attempt to rotate nontransferable pre=${pre}.`)
        }

        let old = ps.old
        ps.old = ps.new
        ps.new = ps.nxt

        if (this.aeid != undefined && this.decrypter == undefined) {
            throw new Error("Unauthorized decryption attempt.  Aeid but no decrypter.")
        }

        let verfers = new Array<Verfer>()
        ps.new.pubs.forEach((pub) => {
            if (this.decrypter != undefined) {
                let signer = this.ks.getPris(pub, this.decrypter)
                if (signer == undefined) {
                    throw new Error(`Missing prikey in db for pubkey=${pub}`)
                }
                verfers.push(signer.verfer)
            } else {
                // Should we regenerate from salt here since this.decryptor is undefined
                verfers.push(new Verfer({qb64: pub}))
            }

        })

        let salt = pp.salt
        if (salt != undefined && salt != "") { // If you provded a Salt for an AID but don't have encryption, pitch a fit
            if (this.decrypter == undefined) {
                throw new Error("Invalid configuration: AID salt with no encryption")
            }
            salt = this.decrypter.decrypt(b(salt)).qb64
        } else {
            salt = this.salt!
        }

        let creator = new Creatory(pp.algo).make(salt, pp.tier, pp.stem)

        if (ncodes == undefined) {
            if (ncount < 0) {
                throw new Error(`Invalid count=${ncount} must be >= 0`)
            }
            ncodes = new Array<string>(ncount).fill(ncode)
        }

        let pidx = pp.pidx
        let ridx = ps.new.ridx + 1
        let kidx = ps.nxt.kidx + ps.new.pubs.length

        let keys = creator.create(ncodes, 0, "", transferable, pidx, ridx, kidx, temp)
        let digers = Array.from(keys.signers, (signer: Signer) => new Diger({code: dcode}, signer.verfer.qb64b))

        let dt = new Date().toString()
        ps.nxt = new PubLot()
        ps.nxt.pubs = Array.from(keys.signers, (signer: Signer) => signer.verfer.qb64)
        ps.nxt.ridx = ridx
        ps.nxt.kidx = kidx
        ps.nxt.dt = dt

        if (!this.ks.pinSits(pre, ps)) {
            throw new Error(`Problem updating pubsit db for pre=${pre}.`)
        }

        if (this.encrypter != undefined) { // Only store encrypted keys if we have an encrypter, otherwise regenerate
            keys.signers.forEach((signer: Signer) => {
                this.ks.putPris(signer.verfer.qb64, signer, this.encrypter!)
            })
        } else if (this._encrypter == undefined && keys.paths != undefined) {
            keys.paths.forEach((path: string, idx: number) => {
                let signer = keys.signers[idx]
                let ppt = new PubPath()
                ppt.path = path
                ppt.tier = pp!.tier
                ppt.temp = temp
                this.ks.putPths(signer.verfer.qb64, ppt)
            })
        } else {
            throw new Error("invalid configuration, randy keys without encryption")
        }

        let newPs = new PubSet()
        newPs.pubs = ps.nxt.pubs
        this.ks.putPubs(riKey(pre, ps.nxt.ridx), newPs)

        if (erase) {
            old.pubs.forEach((pub) => {
                this.ks.remPris(pub)
            })
        }

        return [verfers, digers]
    }

    sign({ser, pubs=undefined, verfers=undefined, indexed=true, indices=undefined, ondices=undefined}: SignArgs) {
        let signers = new Array<Signer>()

        if (pubs == undefined && verfers == undefined) {
            throw new Error("pubs or verfers required")
        }

        if (pubs != undefined) {
            if (this.aeid != undefined && this.decrypter == undefined) {
                throw new Error("Unauthorized decryption attempt.  Aeid but no decrypter.")
            }

            pubs.forEach((pub) => {
                //If no decrypter then get SaltyState and regenerate prikey
                if (this.decrypter != undefined) {
                    let signer = this.ks.getPris(pub, this.decrypter)
                    if (signer == undefined) {
                        throw new Error(`Missing prikey in db for pubkey=${pub}`)
                    }
                    signers.push(signer)
                } else {
                    let verfer = new Verfer({qb64: pub})
                    let ppt = this.ks.getPths(pub)
                    if (ppt == undefined) {
                        throw new Error(`Missing prikey in db for pubkey=${pub}`)
                    }
                    let salter = new Salter({qb64: this.salt})
                    signers.push(salter.signer(ppt.code, verfer.transferable, ppt.path, ppt.tier as Tier, ppt.temp))
                }
            })
        } else {
            verfers!.forEach((verfer: Verfer) => {
                if (this.decrypter != undefined) {
                    let signer = this.ks.getPris(verfer.qb64, this.decrypter)
                    if (signer == undefined) {
                        throw new Error(`Missing prikey in db for pubkey=${verfer.qb64}`)
                    }
                    signers.push(signer)
                } else {
                    let ppt = this.ks.getPths(verfer.qb64)
                    if (ppt == undefined) {
                        throw new Error(`Missing prikey in db for pubkey=${verfer.qb64}`)
                    }
                    let salter = new Salter({qb64: this.salt})
                    signers.push(salter.signer(ppt.code, verfer.transferable, ppt.path, ppt.tier as Tier, ppt.temp))
                }
            })
        }

        if (indices != undefined && indices.length != signers.length) {
            throw new Error(`Mismatch indices length=${indices.length} and resultant signers length=${signers.length}`)
        }

        if (ondices != undefined && ondices.length != signers.length) {
            throw new Error(`Mismatch ondices length=${ondices.length} and resultant signers length=${signers.length}`)
        }

        if (indexed) {
            let sigers = new Array<Siger>()
            signers.forEach((signer, idx) => {
                let i
                if (indices != undefined) {
                    i = indices[idx]
                    if (i < 0) {
                        throw new Error(`Invalid signing index = ${i}, not whole number.`)
                    }
                } else {
                    i = idx
                }

                let o
                if (ondices != undefined) {
                    o = ondices[idx]
                    if (o <= 0) {
                        throw new Error(`Invalid other signing index = {o}, not None or not whole number.`)
                    }
                } else {
                    o = i
                }

                let only = o == undefined
                sigers.push(signer.sign(ser, i, only, o) as Siger)
            })
            return sigers
        } else {
            let cigars = new Array<Cigar>()
            signers.forEach((signer: Signer) => {
                cigars.push(signer.sign(ser) as Cigar)
            })

            return cigars
        }
    }
}

export function riKey(pre: string, ridx: number) {
    return pre + "." + ridx.toString(16).padStart(32, '0')

}


export interface KeyStore {
    getGbls(key: string): string | undefined
    pinGbls(key: string, val: string): void

    prmsElements(): Array<[string, PrePrm]>
    getPrms(keys: string) :PrePrm | undefined
    pinPrms(keys: string, data: PrePrm): void
    putPrms(keys: string, data: PrePrm): boolean
    remPrms(keys: string): boolean

    prisElements(decrypter: Decrypter): Array<[string, Signer]>
    getPris(keys: string, decrypter: Decrypter): Signer | undefined
    pinPris(keys: string, data: Signer, encrypter: Encrypter): void
    putPris(pubKey: string, signer: Signer, encrypter: Encrypter): boolean
    remPris(pubKey: string): void

    getPths(pubKey: string): PubPath | undefined
    putPths(pubKey: string, val: PubPath): boolean
    pinPths(pubKey: string, val: PubPath): boolean

    getPres(pre: string): Uint8Array | undefined
    putPres(pre: string, val: Uint8Array): boolean
    pinPres(pre: string, val: Uint8Array): boolean

    getSits(keys: string) :PreSit | undefined
    putSits(pre: string, val: PreSit): boolean
    pinSits(pre: string, val: PreSit): boolean
    remSits(keys: string): boolean

    getPubs(keys: string): PubSet | undefined
    putPubs(keys: string, data: PubSet): boolean
}

/*
     In memory test implementation of Keeper key store
*/

class Keeper implements KeyStore {
    private readonly _gbls: Map<string, string>
    private readonly _pris: Map<string, Uint8Array>
    private readonly _pths: Map<string, PubPath>
    private readonly _pres: Map<string, Uint8Array>
    private readonly _prms: Map<string, PrePrm>
    private readonly _sits: Map<string, PreSit>
    private readonly _pubs: Map<string, PubSet>

    constructor() {
        this._gbls = new Map<string, string>()
        this._pris = new Map<string, Uint8Array>()
        this._pths = new Map<string, PubPath>()
        this._pres = new Map<string, Uint8Array>()
        this._prms = new Map<string, PrePrm>()
        this._sits = new Map<string, PreSit>()
        this._pubs = new Map<string, PubSet>()

    }

    getGbls(key: string): string | undefined {
        return this._gbls.get(key)
    }

    pinGbls(key: string, val: string): void {
        this._gbls.set(key, val)
    }

    prmsElements(): Array<[string, PrePrm]> {
        let out = new Array<[string, PrePrm]>()
        this._prms.forEach((value, key) => {
            out.push([key, value])
        })

        return out
    }

    getPrms(keys: string): PrePrm | undefined {
        return this._prms.get(keys)
    }

    pinPrms(keys: string, data: PrePrm): void {
        this._prms.set(keys, data)
    }

    putPrms(keys: string, data: PrePrm): boolean {
        if (this._prms.has(keys)) {
            return false
        }
        this._prms.set(keys, data)
        return true
    }

    remPrms(keys: string): boolean {
        return this._prms.delete(keys)
    }

    prisElements(decrypter: Decrypter): Array<[string, Signer]> {
        let out = new Array<[string, Signer]>()
        this._pris.forEach(function (val, pubKey) {
            let verfer = new Verfer({qb64: pubKey})
            let signer = decrypter.decrypt(val, null, verfer.transferable)
            out.push([pubKey, signer])
        })
        return out
    }

    pinPris(pubKey: string, signer: Signer, encrypter: Encrypter): void {
        let cipher = encrypter.encrypt(null, signer)
        this._pris.set(pubKey, cipher.qb64b)
    }

    putPris(pubKey: string, signer: Signer, encrypter: Encrypter): boolean {
        if (this._pris.has(pubKey)) {
            return false
        }
        let cipher = encrypter.encrypt(null, signer)
        this._pris.set(pubKey, cipher.qb64b)
        return true
    }

    getPris(pubKey: string, decrypter: Decrypter): Signer | undefined {
        let val = this._pris.get(pubKey)
        if (val == undefined) {
            return undefined
        }
        let verfer = new Verfer({qb64: pubKey})


        return decrypter.decrypt(val, null, verfer.transferable)
    }

    pinPths(pubKey: string, val: PubPath): boolean {
        this._pths.set(pubKey, val)
        return true
    }

    putPths(pubKey: string, val: PubPath): boolean {
        if (this._pths.has(pubKey)) {
            return false
        }

        this._pths.set(pubKey, val)
        return true

    }

    getPths(pubKey: string): PubPath | undefined {
        return this._pths.get(pubKey)
    }

    remPris(pubKey: string): void {
        this._pris.delete(pubKey)
    }

    getPres(pre: string): Uint8Array | undefined {
        return this._pres.get(pre)
    }

    pinPres(pre: string, val: Uint8Array): boolean {
        this._pres.set(pre, val)
        return true
    }

    putPres(pre: string, val: Uint8Array): boolean {
        if (this._pres.has(pre)) {
            return false
        }

        this._pres.set(pre, val)
        return true
    }

    getSits(keys: string): PreSit | undefined {
        return this._sits.get(keys)
    }

    putSits(pre: string, val: PreSit): boolean {
        if (this._sits.has(pre)) {
            return false
        }

        this._sits.set(pre, val)
        return true
    }

    pinSits(pre: string, val: PreSit): boolean {
        this._sits.set(pre, val)
        return true
    }

    remSits(keys: string): boolean {
        return this._sits.delete(keys)
    }

    getPubs(keys: string): PubSet | undefined {
        return this._pubs.get(keys)
    }

    putPubs(keys: string, data: PubSet): boolean {
        if (this._pubs.has(keys)) {
            return false
        }
        this._pubs.set(keys, data)
        return true
    }
}