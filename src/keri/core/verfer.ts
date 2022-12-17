export {};
const libsodium = require('libsodium-wrappers-sumo');
const {Matter} = require('./matter');
import {MatterArgs, MtrDex} from './matter';

/**
 * @description  Verfer :sublclass of Matter,helps to verify signature of serialization
 *  using .raw as verifier key and .code as signature cypher suite
 */
export class Verfer extends Matter {
    constructor({raw, code, qb64, qb64b, qb2, strip}: MatterArgs) {
        super({raw, code, qb64, qb64b, qb2, strip});

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

        } catch (error: any) {
            throw new Error(error);
        }
    }
}
