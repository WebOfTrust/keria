import libsodium from "libsodium-wrappers-sumo";

import {Matter, MatterArgs, MtrDex} from './matter';
import {Signer} from "./signer";
import {Cipher} from "./cipher";
import {EmptyMaterialError} from "./kering";
import {Salter} from "./salter";


export class Decrypter extends Matter {
    private readonly _decrypt: any;
    constructor({raw, code = MtrDex.X25519_Private, qb64, qb64b, qb2, strip}:MatterArgs, seed: Uint8Array | undefined = undefined) {
        try {
            super({raw, code, qb64, qb64b, qb2, strip})
        } catch(e) {
            if(e instanceof EmptyMaterialError) {
                if (seed != undefined) {
                    let signer = new Signer({qb64b: seed})
                    if (signer.code != MtrDex.Ed25519_Seed) {
                        throw new Error(`Unsupported signing seed derivation code ${signer.code}`)
                    }
                    let sigkey = new Uint8Array(signer.raw.length + signer.verfer.raw.length)
                    sigkey.set(signer.raw)
                    sigkey.set(signer.verfer.raw, signer.raw.length)
                    raw = libsodium.crypto_sign_ed25519_sk_to_curve25519(sigkey)
                    super({raw, code, qb64, qb64b, qb2, strip})
                }
                else {
                    throw e
                }
            } else {
                throw e
            }
        }

        if (this.code == MtrDex.X25519_Private) {
            this._decrypt = this._x25519
        } else {
            throw new Error(`Unsupported decrypter code = ${this.code}.`)
        }
    }

    decrypt(ser: Uint8Array | null = null, cipher: Cipher | null = null, transferable: boolean = false) {
        if (ser == null && cipher == null) {
            throw new EmptyMaterialError("Neither ser or cipher were provided")
        }

        if (ser != null) {
            cipher = new Cipher({qb64b: ser})
        }

        return this._decrypt(cipher, this.raw, transferable)
    }

    _x25519(cipher: Cipher, prikey: Uint8Array, transferable: boolean = false) {
        let pubkey = libsodium.crypto_scalarmult_base(prikey)
        let plain = libsodium.crypto_box_seal_open(cipher.raw, pubkey, prikey)
        if (cipher.code == MtrDex.X25519_Cipher_Salt) {
            return new Salter({qb64b: plain})
        } else if (cipher.code == MtrDex.X25519_Cipher_Seed) {
            return new Signer({qb64b: plain, transferable: transferable})
        } else {
            throw new Error(`Unsupported cipher text code == ${cipher.code}`)
        }
    }
}