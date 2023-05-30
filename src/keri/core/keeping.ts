import { Salter } from './salter'
import { Algos, SaltyCreator, RandyCreator } from './manager';
import { MtrDex } from './matter';
import { Tier } from './salter';
import { Encrypter } from "../core/encrypter";
import { Decrypter } from './decrypter';
import { b } from "./core";
import { Cipher } from './cipher';
import { Diger } from './diger';
import { Prefixer } from './prefixer';

export {};

export class KeyManager {
    private salter?: Salter
    // private externalModulees?: any

    constructor(salter: Salter, _externalModules: any = undefined ) {

        this.salter = salter
        // this.externalModulees = _externalModules
    }

    new(algo: Algos, pidx: number, kargs: any){
        switch (algo) {
            case Algos.salty:
                return new SaltyKeeper(this.salter!, pidx, kargs["kidx"], kargs["tier"], kargs["transferable"], kargs["stem"], kargs["code"], kargs["count"], kargs["icodes"], kargs["ncode"], kargs["ncount"], kargs["ncodes"], kargs["dcode"], kargs["bran"], kargs["sxlt"])
            case Algos.randy:
                return new RandyKeeper(this.salter!, kargs["code"], kargs["count"], kargs["icodes"], kargs["transferable"], kargs["ncode"], kargs["ncount"], kargs["ncodes"], kargs["dcode"], kargs["prxs"], kargs["nxts"])
            case Algos.group:
                return new GroupKeeper(this, kargs["mhab"], kargs["states"], kargs["rstates"],kargs["keys"],kargs["ndigs"])
            default:
                throw new Error('Unknown algo')
        }
    }

    get(aid:any) {
        let pre = new Prefixer({qb64: aid["prefix"]})
        if (Algos.salty in aid){
            let kargs = aid[Algos.salty]
            return new SaltyKeeper(this.salter!, kargs["pidx"], kargs["kidx"], kargs["tier"], kargs["transferable"], kargs["stem"], kargs["code"], kargs["count"], kargs["icodes"], kargs["ncode"], kargs["ncount"], kargs["ncodes"], kargs["dcode"], kargs["bran"], kargs["sxlt"])
        } else if (Algos.randy in aid) {
            let kargs = aid[Algos.randy]
            return new RandyKeeper(this.salter!, kargs["code"], kargs["count"], kargs["icodes"], pre.transferable, kargs["ncode"], kargs["ncount"], kargs["ncodes"], kargs["dcode"], kargs["prxs"],  kargs["nxts"])
        } else if (Algos.group in aid) {
            throw new Error(`Group Keeper not allowed yet`)
        } else{
            throw new Error(`Algo not allowed yet`)
        }
    }

}

export class SaltyKeeper {
    private aeid:string
    private encrypter:Encrypter
    private decrypter:Decrypter
    private salter: Salter
    private pidx:number
    private kidx:number
    private tier:Tier
    private transferable:boolean
    private stem:string | undefined
    private code:string
    private count:number
    private icodes:string[] | undefined
    private ncode:string
    private ncount:number
    private ncodes:string[] | undefined
    private dcode:string | undefined
    private sxlt:string | undefined
    private bran:string | undefined
    private creator: SaltyCreator
    public algo:Algos = Algos.salty

    constructor(salter:Salter, pidx:number, kidx:number=0, tier=Tier.low, transferable=false, stem=undefined,
        code=MtrDex.Ed25519_Seed, count=1, icodes:string[]|undefined=undefined, ncode=MtrDex.Ed25519_Seed,
        ncount=1, ncodes:string[]|undefined=undefined, dcode=MtrDex.Blake3_256, bran:string|undefined = undefined, sxlt=undefined){

        // # Salter is the entered passcode and used for enc/dec of salts for each AID
        this.salter = salter
        let signer = this.salter.signer(undefined, transferable=false)

        this.aeid = signer.verfer.qb64

        this.encrypter = new Encrypter({}, b(this.aeid))
        this.decrypter = new Decrypter({}, signer.qb64b)

        this.code = code
        this.ncode = ncode
        this.tier = tier
        this.icodes = icodes==undefined? new Array<string>(count).fill(code) : icodes
        this.ncodes = ncodes==undefined? new Array<string>(ncount).fill(ncode) : ncodes
        this.dcode = dcode
        this.pidx = pidx
        this.kidx = kidx
        this.transferable = transferable
        this.count = count
        this.ncount = ncount
        this.stem = stem==undefined? "signify:aid" : stem
        
        if (bran != undefined) {
            this.bran = MtrDex.Salt_128 + 'A' + bran!.slice(0, 21)
            this.creator = new SaltyCreator(this.bran, this.tier, this.stem)
            this.sxlt = this.encrypter.encrypt(b(this.creator.salt)).qb64
        } else if (sxlt == undefined) {
            this.creator = new SaltyCreator(undefined, this.tier, this.stem)
            this.sxlt = this.encrypter.encrypt(b(this.creator.salt)).qb64
        } else {      
            this.sxlt = sxlt
            let ciph = new Cipher({qb64:this.sxlt})
            this.creator = new SaltyCreator(this.decrypter.decrypt(null, ciph).qb64, tier=tier, this.stem)
        }

    }

    params() {
        // Get AID parameters to store externally

        return {
            sxlt: this.sxlt,
            pidx: this.pidx,
            kidx: this.kidx,
            stem: this.stem,
            tier: this.tier,
            icodes: this.icodes,
            ncodes: this.ncodes,
            dcode: this.dcode,
            transferable: this.transferable
        }
    }

    incept(transferable:boolean) {
        // Create verfers and digers for inception event for AID represented by this Keeper

        // Args:
        //     transferable (bool): True if the AID for this keeper can establish new keys

        // Returns:
        //     verfers(list): qualified base64 of signing public keys
        //     digers(list): qualified base64 of hash of rotation public keys
        
        this.transferable = transferable
        this.kidx = 0

        let signers = this.creator.create(this.icodes, this.count, this.code, this.transferable, this.pidx, 0, this.kidx,false)                          
        let verfers = signers.signers.map(signer => signer.verfer.qb64);

        let nsigners = this.creator.create(this.ncodes, this.ncount, this.ncode, this.transferable, this.pidx, 0, this.icodes?.length,false)    
        let digers = nsigners.signers.map(nsigner => new Diger({code: this.dcode},nsigner.verfer.qb64b ).qb64);

        return [verfers, digers]

    }

    rotate(ncodes:string[], transferable:boolean, ..._:any[]){
    // Rotate and return verfers and digers for next rotation event for AID represented by this Keeper

    // Args:
    //     ncodes (list):
    //     transferable (bool): derivation codes for rotation key creation

    // Returns:
    //     verfers(list): qualified base64 of signing public keys
    //     digers(list): qualified base64 of hash of rotation public keys


        this.ncodes = ncodes
        this.transferable = transferable
        let signers = this.creator.create(this.ncodes, this.ncount, this.ncode, this.transferable, this.pidx, 0, this.kidx+this.icodes!.length,false)                          
        let verfers = signers.signers.map(signer => signer.verfer.qb64);

        this.kidx = this.kidx! + this.icodes!.length
        let nsigners = this.creator.create(this.ncodes, this.ncount, this.ncode, this.transferable, this.pidx, 0, this.kidx+this.icodes!.length,false)    
        let digers = nsigners.signers.map(nsigner => new Diger({code: this.dcode},nsigner.verfer.qb64b ).qb64);

        return [verfers, digers]
    }

    sign(ser: Uint8Array, indexed=true, indices:number[]|undefined=undefined, ondices:number[]|undefined=undefined){
        let signers = this.creator.create(this.icodes, this.ncount, this.ncode, this.transferable, this.pidx, 0, this.kidx,false)

        if (indexed){
            let sigers = []
            let i = 0
            for (const [j, signer] of signers.signers.entries()) {
                if (indices!= undefined){
                    i = indices![j]
                    if (typeof i != "number" || i < 0){
                        throw new Error(`Invalid signing index = ${i}, not whole number.`)
                    }
                } else {
                    i = j
                }
                let o = 0
                if (ondices!=undefined){
                    o = ondices![j]
                    if ((o == undefined || typeof o == "number" && typeof o != "number" && o>=0)!) {
                        throw new Error(`Invalid ondex = ${o}, not whole number.`)
                    }
                } else {
                    o = i
                }
                sigers.push(signer.sign(ser, i, o==undefined?true:false, o))
            } 
            return sigers.map(siger => siger.qb64);
        } else {
            let cigars = []
            for (const [_, signer] of signers.signers.entries()) {
                cigars.push(signer.sign(ser))
            }
            return cigars.map(cigar => cigar.qb64);
        }
    }
}


export class RandyKeeper {
    private salter: Salter
    private code:string
    private count:number
    private icodes:string[] | undefined
    private transferable:boolean
    private ncount:number
    private ncodes:string[] | undefined
    private ncode:string
    private dcode:string | undefined
    private prxs:string[] | undefined
    private nxts:string[] | undefined
    private aeid:string
    private encrypter:Encrypter
    private decrypter:Decrypter
    private creator: RandyCreator
    public algo:Algos = Algos.randy



    constructor(salter:Salter, code=MtrDex.Ed25519_Seed, count=1, icodes:string[]|undefined=undefined, transferable=false, 
        ncode=MtrDex.Ed25519_Seed, ncount=1, ncodes:string[], dcode=MtrDex.Blake3_256, prxs:string[]|undefined=undefined, nxts:string[]|undefined=undefined){

        this.salter = salter
        this.icodes = icodes==undefined? new Array<string>(count).fill(code) : icodes
        this.ncodes = ncodes==undefined? new Array<string>(ncount).fill(ncode) : ncodes

        this.code = code
        this.ncode = ncode
        this.count = count
        this.ncount = ncount    

        let signer = this.salter.signer(undefined, transferable=false)
        this.aeid = signer.verfer.qb64

        this.encrypter = new Encrypter({}, b(this.aeid))
        this.decrypter = new Decrypter({}, signer.qb64b)

        this.nxts = nxts
        this.prxs = prxs
        this.transferable = transferable

        this.icodes = icodes
        this.ncodes = ncodes
        this.dcode = dcode
        
        this.creator = new RandyCreator()
        

    }

    params() {

        return {
            nxts: this.nxts,
            prxs: this.prxs,
            transferable: this.transferable
        }
    }

    incept(transferable:boolean) {
        this.transferable = transferable

        let signers = this.creator.create(this.icodes, this.count, this.code, this.transferable) 
        this.prxs = signers.signers.map(signer => this.encrypter.encrypt(undefined,signer).qb64);

        let verfers = signers.signers.map(signer => signer.verfer.qb64);
        
        let nsigners = this.creator.create(this.ncodes, this.ncount, this.ncode, this.transferable)  
        
        this.nxts = nsigners.signers.map(signer => this.encrypter.encrypt(undefined,signer).qb64);

        let digers = nsigners.signers.map(nsigner => new Diger({code: this.dcode},nsigner.verfer.qb64b ).qb64);

        return [verfers, digers]
    }

    rotate(ncodes:string[], transferable:boolean, ..._:any[]){
    
            this.ncodes = ncodes
            this.transferable = transferable
            this.prxs = this.nxts

            let signers = this.nxts!.map(nxt => this.decrypter.decrypt(undefined, new Cipher({qb64:nxt}), this.transferable))
            let verfers = signers.map(signer => signer.verfer.qb64)
            let nsigners = this.creator.create(this.ncodes, this.ncount, this.ncode, this.transferable)    

            this.nxts = nsigners.signers.map(signer => this.encrypter.encrypt(undefined, signer).qb64);
    
            let digers = nsigners.signers.map(nsigner => new Diger({code: this.dcode},nsigner.verfer.qb64b ).qb64);
    
            return [verfers, digers]
        }

    sign(ser: Uint8Array, indexed=true, indices:number[]|undefined=undefined, ondices:number[]|undefined=undefined){
        let signers = this.prxs!.map(prx => this.decrypter.decrypt(new Cipher({qb64:prx}).qb64b, undefined, this.transferable))

        if (indexed){
            let sigers = []
            let i = 0
            for (const [j, signer] of signers.entries()) {
                if (indices!= undefined){
                    i = indices![j]
                    if (typeof i != "number" || i < 0){
                        throw new Error(`Invalid signing index = ${i}, not whole number.`)
                    }
                } else {
                    i = j
                }
                let o = 0
                if (ondices!=undefined){
                    o = ondices![j]
                    if ((o == undefined || typeof o == "number" && typeof o != "number" && o>=0)!) {
                        throw new Error(`Invalid ondex = ${o}, not whole number.`)
                    }
                } else {
                    o = i
                }
                sigers.push(signer.sign(ser, i, o==undefined?true:false, o))
            } 
            return sigers.map(siger => siger.qb64);
        } else {
            let cigars = []
            for (const [_, signer] of signers.entries()) {
                cigars.push(signer.sign(ser))
            }
            return cigars.map(cigar => cigar.qb64);
        }
    }
}
    export class GroupKeeper {
        private manager: KeyManager
        private mhab:any
        private gkeys:string[] | undefined
        private gdigs:string[] | undefined
        public algo:Algos = Algos.group
    
        constructor(manager:KeyManager, mhab=undefined, states:any[]|undefined=undefined, rstates:any[]|undefined=undefined, keys:any[]|undefined=undefined, ndigs:any[]|undefined=undefined){
        
        this.manager = manager
        if (states !=undefined) {
            keys = states.map(state => state['k'][0])
        }

        if (rstates !=undefined) {
            ndigs = rstates.map(state => state['n'][0])
        }

        this.gkeys = keys
        this.gdigs = ndigs
        this.mhab = mhab
    }
    incept(..._:any){
        return [this.gkeys, this.gdigs]
    }

    rotate(states:any[], rstates:any[],..._:any){
        this.gkeys = states.map(state => state['k'][0])
        this.gdigs = rstates.map(state => state['n'][0])
        return [this.gkeys, this.gdigs]
    }
    sign(ser:Uint8Array, indexed:boolean=true, _rotate:boolean=false, ..._:any){
        let key = this.mhab['state']['k'][0]
        let ndig = this.mhab['state']['n'][0]

        let csi = this.gkeys!.indexOf(key)
        let pni = this.gdigs!.indexOf(ndig)
        let mkeeper = this.manager.get(this.mhab)

        return mkeeper.sign(ser, indexed, [csi], [pni])
    }

    params(){
        return {
            mhab: this.mhab,
            keys: this.gkeys,
            ndigs: this.gdigs
        }

    }
}