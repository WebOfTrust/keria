import {createHash} from "blake3"

import {Matter, MatterArgs, MtrDex} from './matter';

/**
 * @description : Diger is subset of Matter and is used to verify the digest of serialization
 * It uses  .raw : as digest
 * .code as digest algorithm
 *
 */

export class Diger extends Matter {
    private readonly _verify: any

    // This constructor will assign digest verification function to ._verify
    constructor({raw, code = MtrDex.Blake3_256, qb64, qb64b, qb2}: MatterArgs, ser: Uint8Array | null = null) {
        try {
            super({raw, code, qb64, qb64b, qb2});
        } catch (error) {
            if (ser == null) {
                throw error;
            }

            if (code === MtrDex.Blake3_256) {
                const hasher = createHash();
                const dig = hasher.update(ser).digest('');
                super({raw: dig, code: code});
            } else {
                throw new Error(`Unsupported code = ${code} for digester.`);
            }
        }

        if (code === MtrDex.Blake3_256) {
            this._verify = this.blake3_256;
        } else {
            throw new Error(`Unsupported code = ${code} for digester.`);
        }
    }


    /**
     *
     * @param {Uint8Array} ser  serialization bytes
     * @description  This method will return true if digest of bytes serialization ser matches .raw
     * using .raw as reference digest for ._verify digest algorithm determined
     by .code
     */
    verify(ser: Uint8Array): boolean {
        return this._verify(ser, this.raw);
    }

    compare(ser: Uint8Array, dig: any = null, diger: Diger | null = null ) {
        if (dig != null) {
            if (dig.toString() == this.qb64) {
                return true
            }

            diger = new Diger({qb64b: dig})
        } else if (diger != null) {
            if (diger.qb64b == this.qb64b) {
                return true;
            }
        }

        else {
            throw new Error("Both dig and diger may not be None.")
        }

        if (diger.code == this.code) {
            return false
        }

        return diger.verify(ser) && this.verify(ser)
    }


    blake3_256(ser: Uint8Array, dig: any) {
        const hasher = createHash();
        let digest = hasher.update(ser).digest('');
        return (digest.toString() === dig.toString());
    }
}
