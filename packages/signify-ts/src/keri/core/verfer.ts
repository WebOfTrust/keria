import libsodium from 'libsodium-wrappers-sumo';
import { Matter, MatterArgs, MtrDex } from './matter.ts';
import { p256 } from '@noble/curves/p256';
import { b } from './core.ts';

const VERFER_CODES = new Set([
    MtrDex.Ed25519N,
    MtrDex.Ed25519,
    MtrDex.ECDSA_256r1N,
    MtrDex.ECDSA_256r1,
]);

/**
 * @description  Verfer :sublclass of Matter,helps to verify signature of serialization
 *  using .raw as verifier key and .code as signature cypher suite
 */
export class Verfer extends Matter {
    constructor({ raw, code, qb64, qb64b, qb2 }: MatterArgs) {
        super({ raw, code, qb64, qb64b, qb2 });

        if (!VERFER_CODES.has(this.code)) {
            throw new Error(`Unsupported code = ${this.code} for verifier.`);
        }
    }

    verify(sig: Uint8Array, ser: Uint8Array | string): boolean {
        switch (this.code) {
            case MtrDex.Ed25519:
            case MtrDex.Ed25519N: {
                return libsodium.crypto_sign_verify_detached(
                    sig,
                    ser,
                    this.raw
                );
            }
            case MtrDex.ECDSA_256r1:
            case MtrDex.ECDSA_256r1N: {
                const message = typeof ser === 'string' ? b(ser) : ser;
                return p256.verify(sig, message, this.raw);
            }
            default:
                throw new Error(
                    `Unsupported code = ${this.code} for verifier.`
                );
        }
    }
}
