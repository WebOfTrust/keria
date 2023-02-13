export {};
import libsodium from "libsodium-wrappers-sumo"

import {Matter, MatterArgs, MtrDex} from './matter';

/**
 * @description  Verfer :sublclass of Matter,helps to verify signature of serialization
 *  using .raw as verifier key and .code as signature cypher suite
 */
export class Verfer extends Matter {
    private readonly _verify: (sig: any, ser: any, key: any) => boolean;
    constructor({raw, code, qb64, qb64b, qb2}: MatterArgs) {
        super({raw, code, qb64, qb64b, qb2});

        if (Array.from([MtrDex.Ed25519N, MtrDex.Ed25519]).includes(this.code)) {
            this._verify = this._ed25519
        } else {
            throw new Error(`Unsupported code = ${this.code} for verifier.`)
        }
    }

    verify(sig: any, ser: any) {
        return this._verify(sig, ser, this.raw)
    }

    _ed25519(sig: any, ser: any, key: any) {
        try {
            return libsodium.crypto_sign_verify_detached(sig, ser, key);

        } catch (error) {
            throw new Error(error as string);
        }
    }
}
