import bip39 from 'bip39-light'
import { Diger, Signer, Verfer } from 'signify-ts';




export class BIP39Shim {

    private icount:number
    private ncount:number
    private dcode:string | undefined
    private pidx: number
    private kidx: number
    private transferable:boolean
    private stem: string
    private mnemonics: string[]
    private signer: Signer

    constructor(pidx, kargs ) {
        this.icount = kargs.icount
        this.ncount = kargs.ncount
        this.pidx = pidx
        this.kidx = kargs.kidx
        this.transferable = kargs.transferable
        this.stem = kargs.stem
        this.mnemonics = kargs.mnemonics

        const seed = bip39.mnemonicToEntropy(this.mnemonics);
        this.signer = new Signer({raw: seed, code: this.dcode, transferable: this.transferable})

    }

    params(){
        return {
            pidx: this.pidx,
            kidx: this.kidx,
            mnemonics: this.mnemonics
        }
    }

    keys(count, kidx, transferable){
        let keys = []
        for (let idx in range(count)){
            let keyId = `${this.stem}-${this.pidx}-${kidx + idx}`
            verkey = bip39 aldo
            verfer = new Verfer(verkey,
                coring.MtrDex.Ed25519 if transferable
                else coring.MtrDex.Ed25519N)
            keys.push(verfer.qb64)
        }
        return keys
    }


    incept(transferable:boolean){
        this.transferable = transferable

        let signers = this.creator.create(this.icodes, this.count, this.code, this.transferable) 

        let verfers = signers.signers.map(signer => signer.verfer.qb64);
        
        let nsigners = this.creator.create(this.ncodes, this.ncount, this.ncode, this.transferable)  
        

        let digers = nsigners.signers.map(nsigner => new Diger({code: this.dcode},nsigner.verfer.qb64b ).qb64);

        return [verfers, digers]
    }

    rotate(){
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
        // let signers = this.prxs!.map(prx => this.decrypter.decrypt(new Cipher({qb64:prx}).qb64b, undefined, this.transferable))
        let signers = []

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

    generateMnemonic(strength){
        return bip39.generateMnemonic(strength)
    }

}