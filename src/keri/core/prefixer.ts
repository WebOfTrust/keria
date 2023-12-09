import { Matter, MatterArgs, MtrDex } from './matter';
import { EmptyMaterialError } from './kering';
import { Dict, Ilks } from './core';
import { sizeify } from './serder';
import { Verfer } from './verfer';

import { blake3 } from '@noble/hashes/blake3';

const Dummy: string = '#';

export class Prefixer extends Matter {
    private readonly _derive: Function | undefined;
    private readonly _verify: Function | undefined;

    constructor({ raw, code, qb64b, qb64, qb2 }: MatterArgs, ked?: Dict<any>) {
        try {
            super({ raw, code, qb64b, qb64, qb2 });
        } catch (e) {
            if (e instanceof EmptyMaterialError) {
                if (ked == undefined || (code == undefined && !('i' in ked))) {
                    throw e;
                }

                if (code == undefined) {
                    super({ qb64: ked['i'], code: code });
                    code = this.code;
                }

                let _derive;
                if (code == MtrDex.Ed25519N) {
                    _derive = Prefixer._derive_ed25519N;
                } else if (code == MtrDex.Ed25519) {
                    _derive = Prefixer._derive_ed25519;
                } else if (code == MtrDex.Blake3_256) {
                    _derive = Prefixer._derive_blake3_256;
                } else {
                    throw new Error(`Unsupported code = ${code} for prefixer.`);
                }

                [raw, code] = _derive(ked);
                super({ raw: raw, code: code });
                this._derive = _derive;
            } else {
                throw e;
            }
        }

        if (this.code == MtrDex.Ed25519N) {
            this._verify = this._verify_ed25519N;
        } else if (this.code == MtrDex.Ed25519) {
            this._verify = this._verify_ed25519;
        } else if (this.code == MtrDex.Blake3_256) {
            this._verify = this._verify_blake3_256;
        } else {
            throw new Error(`Unsupported code = ${code} for prefixer.`);
        }
    }

    derive(ked: Dict<any>): [Uint8Array, string] {
        if (ked['i'] != Ilks.icp) {
            throw new Error(
                `Non-incepting ilk ${ked['i']} for prefix derivation`
            );
        }
        return this._derive!(ked);
    }

    verify(ked: Dict<any>, prefixed: boolean = false): boolean {
        if (ked['i'] != Ilks.icp) {
            throw new Error(
                `Non-incepting ilk ${ked['i']} for prefix derivation`
            );
        }
        return this._verify!(ked, this.qb64, prefixed);
    }

    static _derive_ed25519N(ked: Dict<any>): [Uint8Array, string] {
        let verfer;
        const keys = ked['k'];
        if (keys.length != 1) {
            throw new Error(
                `Basic derivation needs at most 1 key got ${keys.length} keys instead`
            );
        }
        try {
            verfer = new Verfer({ qb64: keys[0] });
        } catch (e) {
            throw new Error(`Error extracting public key = ${e}`);
        }

        if (!(verfer.code in [MtrDex.Ed25519N])) {
            throw new Error(`Mismatch derivation code = ${verfer.code}`);
        }

        const next = 'n' in ked ? ked['n'] : [];
        if (verfer.code == MtrDex.Ed25519N && next.length > 0) {
            throw new Error(
                `Non-empty nxt = ${next} for non-transferable code = ${verfer.code}`
            );
        }

        const backers = 'b' in ked ? ked['b'] : [];
        if (verfer.code == MtrDex.Ed25519N && backers.length > 0) {
            throw new Error(
                `Non-empty b =${backers} for non-transferable code = ${verfer.code}`
            );
        }

        const anchor = 'a' in ked ? ked['a'] : [];
        if (verfer.code == MtrDex.Ed25519N && anchor.length > 0) {
            throw new Error(
                `Non-empty a = ${verfer.code} for non-transferable code = ${verfer.code}`
            );
        }

        return [verfer.raw, verfer.code];
    }

    static _derive_ed25519(ked: Dict<any>): [Uint8Array, string] {
        let verfer;
        const keys = ked['k'];
        if (keys.length != 1) {
            throw new Error(
                `Basic derivation needs at most 1 key got ${keys.length} keys instead`
            );
        }

        try {
            verfer = new Verfer({ qb64: keys[0] });
        } catch (e) {
            throw new Error(`Error extracting public key = ${e}`);
        }

        if (verfer.code in [MtrDex.Ed25519]) {
            throw new Error(`Mismatch derivation code = ${verfer.code}`);
        }

        return [verfer.raw, verfer.code];
    }

    static _derive_blake3_256(ked: Dict<any>): [Uint8Array, string] {
        const kd = ked;
        const ilk = ked['t'];
        if (![Ilks.icp, Ilks.dip, Ilks.vcp, Ilks.dip].includes(ilk)) {
            throw new Error(`Invalid ilk = ${ilk} to derive pre.`);
        }

        kd['i'] = ''.padStart(Matter.Sizes.get(MtrDex.Blake3_256)!.fs!, Dummy);
        kd['d'] = ked['i'];
        const [raw] = sizeify(ked);
        const dig = Buffer.from(
            blake3.create({ dkLen: 32 }).update(raw).digest()
        );
        return [dig, MtrDex.Blake3_256];
    }

    _verify_ed25519N(
        ked: Dict<any>,
        pre: string,
        prefixed: boolean = false
    ): boolean {
        try {
            const keys = ked['k'];
            if (keys.length != 1) {
                return false;
            }

            if (keys[0] != pre) {
                return false;
            }

            if (prefixed && ked['i'] != pre) {
                return false;
            }

            const next = 'n' in ked ? ked['n'] : [];
            if (next.length > 0) {
                // must be empty
                return false;
            }
        } catch (e) {
            return false;
        }

        return true;
    }

    _verify_ed25519(
        ked: Dict<any>,
        pre: string,
        prefixed: boolean = false
    ): boolean {
        try {
            const keys = ked['k'];
            if (keys.length != 1) {
                return false;
            }

            if (keys[0] != pre) {
                return false;
            }

            if (prefixed && ked['i'] != pre) {
                return false;
            }
        } catch (e) {
            return false;
        }

        return true;
    }

    _verify_blake3_256(
        ked: Dict<any>,
        pre: string,
        prefixed: boolean = false
    ): boolean {
        try {
            const [raw] = Prefixer._derive_blake3_256(ked);
            const crymat = new Matter({ raw: raw, code: MtrDex.Blake3_256 });
            if (crymat.qb64 != pre) {
                return false;
            }

            if (prefixed && ked['i'] != pre) {
                return false;
            }
        } catch (e) {
            return false;
        }
        return true;
    }
}
