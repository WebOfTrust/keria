import {Matter, MatterArgs, MtrDex} from "./matter";
import {Decrypter} from "./decrypter";


export class Cipher extends Matter {
    constructor({raw, code, qb64, qb64b, qb2, strip}:MatterArgs) {
        if (raw != undefined && code == undefined) {
            if (raw.length == Matter._rawSize(MtrDex.X25519_Cipher_Salt)) {
                code = MtrDex.X25519_Cipher_Salt
            } else if (raw.length  == Matter._rawSize(MtrDex.X25519_Cipher_Seed)) {
                code = MtrDex.X25519_Cipher_Salt
            }
        }
        super({raw, code, qb64, qb64b, qb2, strip});

        if (!(Array.from([MtrDex.X25519_Cipher_Salt, MtrDex.X25519_Cipher_Seed]).includes(this.code))) {
            throw new Error(`Unsupported Cipher code == ${this.code}`)
        }
    }

    decrypt(prikey: Uint8Array | undefined = undefined, seed: Uint8Array | undefined = undefined) {
        let decrypter = new Decrypter({qb64b: prikey}, seed)
        return decrypter.decrypt(this.qb64b)
    }
}