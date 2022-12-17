import libsodium from "libsodium-wrappers-sumo";

import {Matter, MatterArgs, MtrDex} from './matter';
import {Verfer} from "./verfer";
import {Signer} from "./signer";
import {Cipher} from "./cipher";
import {arrayEquals} from "./utils";


export class Encrypter extends Matter {
    private _encrypt: any;
    constructor({raw, code = MtrDex.X25519, qb64, qb64b, qb2, strip}:MatterArgs, verkey: Uint8Array | null = null) {
        if (raw == undefined && verkey != null) {
            let verfer = new Verfer({qb64b: verkey})
            if (!Array.from([MtrDex.Ed25519N, MtrDex.Ed25519]).includes(verfer.code)) {
                throw new Error(`Unsupported verkey derivation code = ${verfer.code}.`)
            }
            raw = libsodium.crypto_sign_ed25519_pk_to_curve25519(verfer.raw)
        }

        super({raw, code, qb64, qb64b, qb2, strip});

        if (this.code == MtrDex.X25519) {
            this._encrypt = this._x25519;
        } else {
            throw new Error(`Unsupported encrypter code = ${this.code}.`)
        }
    }

    verifySeed(seed: Uint8Array) {
        let signer = new Signer({qb64b: seed})
        let keypair = libsodium.crypto_sign_seed_keypair(signer.raw);
        let pubkey = libsodium.crypto_sign_ed25519_pk_to_curve25519(keypair.publicKey)
        return arrayEquals(pubkey, this.raw)
    }

    encrypt(ser: Uint8Array | null = null, matter: Matter | null = null) {
        if (ser == null && matter == null) {
            throw new Error("Neither ser nor matter are provided.")
        }

        if (ser != null) {
            matter = new Matter({qb64b: ser})
        }

        let code
        if (matter!.code == MtrDex.Salt_128) {
            code = MtrDex.X25519_Cipher_Salt
        } else {
            code = MtrDex.X25519_Cipher_Seed
        }

        return this._encrypt(matter!.qb64, this.raw, code)
    }

    _x25519(ser: Uint8Array, pubkey: Uint8Array, code: string) {
        let raw = libsodium.crypto_box_seal(ser, pubkey)
        return new Cipher({raw: raw, code: code})
    }
}