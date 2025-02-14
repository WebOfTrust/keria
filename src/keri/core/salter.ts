import { Signer } from './signer';

import { Matter, MtrDex } from './matter';
import { EmptyMaterialError } from './kering';
import libsodium from 'libsodium-wrappers-sumo';

/**
 * Secret derivation security tier.
 */
export enum Tier {
    low = 'low',
    med = 'med',
    high = 'high',
}

interface SalterArgs {
    raw?: Uint8Array | undefined;
    code?: string;
    tier?: Tier;
    qb64b?: Uint8Array | undefined;
    qb64?: string;
    qb2?: Uint8Array | undefined;
}

/**
 * Maintains a random salt for secrets (private keys).
 * Its .raw is random salt, .code as cipher suite for salt
 */
export class Salter extends Matter {
    private readonly _tier: Tier | null;

    /**
     * Creates a Salter from the provided raw salt bytes or generates a random salt if raw is not provided.
     * Defaults to low security tier. Only supports Salt_128 salt type.
     * @param salterArgs defines the kind of cryptographic seed to create with a variety of raw material initialization sources.
     */
    constructor(salterArgs: SalterArgs) {
        const {
            raw,
            code = MtrDex.Salt_128,
            tier = Tier.low,
            qb64,
            qb64b,
            qb2,
        } = salterArgs;
        try {
            super({ raw, code, qb64, qb64b, qb2 });
        } catch (e) {
            if (e instanceof EmptyMaterialError) {
                if (code == MtrDex.Salt_128) {
                    const salt = libsodium.randombytes_buf(
                        libsodium.crypto_pwhash_SALTBYTES
                    );
                    super({ raw: salt, code: code });
                } else {
                    throw new Error(
                        'invalid code for Salter, only Salt_128 accepted'
                    );
                }
            } else {
                throw e;
            }
        }

        if (this.code != MtrDex.Salt_128) {
            throw new Error('invalid code for Salter, only Salt_128 accepted');
        }

        this._tier = tier !== null ? tier : Tier.low;
    }

    /**
     * Stretches the salt to a secret key using the path, .raw, tier, and size determined by self.code.
     *
     * @param size number of bytes of the stretched seed
     * @param path string of bytes prepended (prefixed) to the salt before stretching
     * @param tier security tier for stretching
     * @param temp boolean, True means use temporary, insecure tier; for testing only
     * @returns stretched raw binary seed (secret) derived from path and .raw, and size using argon2d stretching algorithm.
     * @private
     */
    private stretch(
        size: number = 32,
        path: string = '',
        tier: Tier | null = null,
        temp: boolean = false
    ): Uint8Array {
        tier = tier == null ? this.tier : tier;

        let opslimit: number, memlimit: number;

        // Harcoded values based on keripy
        if (temp) {
            opslimit = 1; //libsodium.crypto_pwhash_OPSLIMIT_MIN
            memlimit = 8192; //libsodium.crypto_pwhash_MEMLIMIT_MIN
        } else {
            switch (tier) {
                case Tier.low:
                    opslimit = 2; //libsodium.crypto_pwhash_OPSLIMIT_INTERACTIVE
                    memlimit = 67108864; //libsodium.crypto_pwhash_MEMLIMIT_INTERACTIVE
                    break;
                case Tier.med:
                    opslimit = 3; //libsodium.crypto_pwhash_OPSLIMIT_MODERATE
                    memlimit = 268435456; //libsodium.crypto_pwhash_MEMLIMIT_MODERATE
                    break;
                case Tier.high:
                    opslimit = 4; //libsodium.crypto_pwhash_OPSLIMIT_SENSITIVE
                    memlimit = 1073741824; //libsodium.crypto_pwhash_MEMLIMIT_SENSITIVE
                    break;
                default:
                    throw new Error(`Unsupported security tier = ${tier}.`);
            }
        }

        return libsodium.crypto_pwhash(
            size,
            path,
            this.raw,
            opslimit,
            memlimit,
            libsodium.crypto_pwhash_ALG_ARGON2ID13
        );
    }

    /**
     * Returns Signer with the private key secret derived from code the path, the user entered passcode as a salt,
     * and the security tier sized by the CESR cryptographic seed size indicated by the code. See the example below.
     * The Signer's public key for its .verfer is derived from its private key, the Matter code, and the transferable boolean.
     *
     * The construction of the raw hash bytes used looks like this:
     *  (      size,               password, salt                                   )
     *  where
     *  ( code size,                   path, Base64Decode(passcode)                 )
     *  for example, for the initial inception signing key the following parameters are used:
     *  (        32, "signify:controller00", Base64Decode("Athisismysecretkeyseed") )
     *  and for the initial rotation key pair the following parameters are used:
     *  (        32, "signify:controller01", Base64Decode("Athisismysecretkeyseed") )
     *
     * @param code derivation code indicating seed type
     * @param transferable whether or not the key is for a transferable or non-transferable identifier.
     * @param path string of bytes prepended (prefixed) to the salt before stretching
     * @param tier security tier for stretching
     * @param temp boolean, True means use temporary, insecure tier; for testing only
     */
    signer(
        code: string = MtrDex.Ed25519_Seed,
        transferable: boolean = true,
        path: string = '',
        tier: Tier | null = null,
        temp: boolean = false
    ): Signer {
        const seed = this.stretch(Matter._rawSize(code), path, tier, temp);

        return new Signer({
            raw: seed, // private key
            code: code,
            transferable: transferable,
        });
    }

    get tier(): Tier | null {
        return this._tier;
    }
}
