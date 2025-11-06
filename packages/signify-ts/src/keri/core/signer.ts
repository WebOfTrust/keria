import { EmptyMaterialError } from './kering.ts';

export {};
import libsodium from 'libsodium-wrappers-sumo';
import { Matter } from './matter.ts';
import { MtrDex } from './matter.ts';
import { Verfer } from './verfer.ts';
import { Cigar } from './cigar.ts';
import { Siger } from './siger.ts';
import { IdrDex } from './indexer.ts';
import { concat } from './core.ts';

/**
 * @description Signer is Matter subclass with method to create signature of serialization
 * It will use .raw as signing (private) key seed
 * .code as cipher suite for signing and new property .verfer whose property
 *  .raw is public key for signing.
 *  If not provided .verfer is generated from private key seed using .code
 as cipher suite for creating key-pair.
 */
interface SignerArgs {
    raw?: Uint8Array | undefined;
    code?: string;
    qb64b?: Uint8Array | undefined;
    qb64?: string;
    qb2?: Uint8Array | undefined;
    transferable?: boolean;
}

export class Signer extends Matter {
    // eslint-disable-next-line @typescript-eslint/no-unsafe-function-type
    private readonly _sign: Function;
    private readonly _verfer: Verfer;

    constructor({
        raw,
        code = MtrDex.Ed25519_Seed,
        qb64,
        qb64b,
        qb2,
        transferable = true,
    }: SignerArgs) {
        try {
            super({ raw, code, qb64, qb64b, qb2 });
        } catch (e) {
            if (e instanceof EmptyMaterialError) {
                if (code == MtrDex.Ed25519_Seed) {
                    const raw = libsodium.randombytes_buf(
                        libsodium.crypto_sign_SEEDBYTES
                    );
                    super({ raw, code, qb64, qb64b, qb2 });
                } else {
                    throw new Error(`Unsupported signer code = ${code}.`);
                }
            } else {
                throw e;
            }
        }
        let verfer;
        if (this.code == MtrDex.Ed25519_Seed) {
            this._sign = this._ed25519;
            const keypair = libsodium.crypto_sign_seed_keypair(this.raw);
            verfer = new Verfer({
                raw: keypair.publicKey,
                code: transferable ? MtrDex.Ed25519 : MtrDex.Ed25519N,
            });
        } else {
            throw new Error(`Unsupported signer code = ${this.code}.`);
        }

        this._verfer = verfer;
    }

    /**
     * @description Property verfer:
     Returns Verfer instance
     Assumes ._verfer is correctly assigned
     */
    get verfer(): Verfer {
        return this._verfer;
    }

    sign(
        ser: Uint8Array,
        index: number | null = null,
        only: boolean = false,
        ondex: number | undefined = undefined
    ): Siger | Cigar {
        return this._sign(ser, this.raw, this.verfer, index, only, ondex);
    }

    _ed25519(
        ser: Uint8Array,
        seed: Uint8Array,
        verfer: Verfer,
        index: number | null,
        only: boolean = false,
        ondex: number | undefined
    ) {
        const sig = libsodium.crypto_sign_detached(
            ser,
            concat(seed, verfer.raw)
        );

        if (index == null) {
            return new Cigar({ raw: sig, code: MtrDex.Ed25519_Sig }, verfer);
        } else {
            let code;
            if (only) {
                ondex = undefined;
                if (index <= 63) {
                    code = IdrDex.Ed25519_Crt_Sig;
                } else {
                    code = IdrDex.Ed25519_Big_Crt_Sig;
                }
            } else {
                if (ondex == undefined) {
                    ondex = index;
                }

                if (ondex == index && index <= 63)
                    // both same and small
                    code = IdrDex.Ed25519_Sig; //  use  small both same
                //  otherwise big or both not same so use big both
                else code = IdrDex.Ed25519_Big_Sig; // use use big both
            }

            return new Siger(
                { raw: sig, code: code, index: index, ondex: ondex },
                verfer
            );
        }
    }
}
