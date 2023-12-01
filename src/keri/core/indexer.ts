import { EmptyMaterialError } from './kering';
import { b, b64ToInt, d, intToB64, readInt } from './core';
import Base64 from 'urlsafe-base64';
import { Buffer } from 'buffer';

export class IndexerCodex {
    Ed25519_Sig: string = 'A'; // Ed25519 sig appears same in both lists if any.
    Ed25519_Crt_Sig: string = 'B'; // Ed25519 sig appears in current list only.
    ECDSA_256k1_Sig: string = 'C'; // ECDSA secp256k1 sig appears same in both lists if any.
    ECDSA_256k1_Crt_Sig: string = 'D'; // ECDSA secp256k1 sig appears in current list.
    ECDSA_256r1_Sig: string = 'E'; // ECDSA secp256r1 sig appears same in both lists if any.
    ECDSA_256r1_Crt_Sig: string = 'F'; // ECDSA secp256r1 sig appears in current list.
    Ed448_Sig: string = '0A'; // Ed448 signature appears in both lists.
    Ed448_Crt_Sig: string = '0B'; // Ed448 signature appears in current list only.
    Ed25519_Big_Sig: string = '2A'; // Ed25519 sig appears in both lists.
    Ed25519_Big_Crt_Sig: string = '2B'; // Ed25519 sig appears in current list only.
    ECDSA_256k1_Big_Sig: string = '2C'; // ECDSA secp256k1 sig appears in both lists.
    ECDSA_256k1_Big_Crt_Sig: string = '2D'; // ECDSA secp256k1 sig appears in current list only.
    ECDSA_256r1_Big_Sig: string = '2E'; // ECDSA secp256r1 sig appears in both lists.
    ECDSA_256r1_Big_Crt_Sig: string = '2F'; // ECDSA secp256r1 sig appears in current list only.
    Ed448_Big_Sig: string = '3A'; // Ed448 signature appears in both lists.
    Ed448_Big_Crt_Sig: string = '3B'; // Ed448 signature appears in current list only.
}

export const IdrDex = new IndexerCodex();

export class IndexedSigCodex {
    Ed25519_Sig: string = 'A'; // Ed25519 sig appears same in both lists if any.
    Ed25519_Crt_Sig: string = 'B'; // Ed25519 sig appears in current list only.
    ECDSA_256k1_Sig: string = 'C'; // ECDSA secp256k1 sig appears same in both lists if any.
    ECDSA_256k1_Crt_Sig: string = 'D'; // ECDSA secp256k1 sig appears in current list.
    ECDSA_256r1_Sig: string = 'E'; // ECDSA secp256r1 sig appears same in both lists if any.
    ECDSA_256r1_Crt_Sig: string = 'F'; // ECDSA secp256r1 sig appears in current list.
    Ed448_Sig: string = '0A'; // Ed448 signature appears in both lists.
    Ed448_Crt_Sig: string = '0B'; // Ed448 signature appears in current list only.
    Ed25519_Big_Sig: string = '2A'; // Ed25519 sig appears in both lists.
    Ed25519_Big_Crt_Sig: string = '2B'; // Ed25519 sig appears in current list only.
    ECDSA_256k1_Big_Sig: string = '2C'; // ECDSA secp256k1 sig appears in both lists.
    ECDSA_256k1_Big_Crt_Sig: string = '2D'; // ECDSA secp256k1 sig appears in current list only.
    ECDSA_256r1_Big_Sig: string = '2E'; // ECDSA secp256r1 sig appears in both lists.
    ECDSA_256r1_Big_Crt_Sig: string = '2F'; // ECDSA secp256r1 sig appears in current list only.
    Ed448_Big_Sig: string = '3A'; // Ed448 signature appears in both lists.
    Ed448_Big_Crt_Sig: string = '3B'; // Ed448 signature appears in current list only.

    has(prop: string): boolean {
        const m = new Map(
            Array.from(Object.entries(this), (v) => [v[1], v[0]])
        );
        return m.has(prop);
    }
}

export const IdxSigDex = new IndexedSigCodex();

export class IndexedCurrentSigCodex {
    Ed25519_Crt_Sig: string = 'B'; // Ed25519 sig appears in current list only.
    ECDSA_256k1_Crt_Sig: string = 'D'; // ECDSA secp256k1 sig appears in current list only.
    ECDSA_256r1_Crt_Sig: string = 'F'; // ECDSA secp256r1 sig appears in current list.
    Ed448_Crt_Sig: string = '0B'; // Ed448 signature appears in current list only.
    Ed25519_Big_Crt_Sig: string = '2B'; // Ed25519 sig appears in current list only.
    ECDSA_256k1_Big_Crt_Sig: string = '2D'; // ECDSA secp256k1 sig appears in current list only.
    ECDSA_256r1_Big_Crt_Sig: string = '2F'; // ECDSA secp256r1 sig appears in current list only.
    Ed448_Big_Crt_Sig: string = '3B'; // Ed448 signature appears in current list only.

    has(prop: string): boolean {
        const m = new Map(
            Array.from(Object.entries(this), (v) => [v[1], v[0]])
        );
        return m.has(prop);
    }
}

export const IdxCrtSigDex = new IndexedCurrentSigCodex();

export class IndexedBothSigCodex {
    Ed25519_Sig: string = 'A'; // Ed25519 sig appears same in both lists if any.
    ECDSA_256k1_Sig: string = 'C'; // ECDSA secp256k1 sig appears same in both lists if any.
    Ed448_Sig: string = '0A'; // Ed448 signature appears in both lists.
    Ed25519_Big_Sig: string = '2A'; // Ed25519 sig appears in both listsy.
    ECDSA_256k1_Big_Sig: string = '2C'; // ECDSA secp256k1 sig appears in both lists.
    Ed448_Big_Sig: string = '3A'; // Ed448 signature appears in both lists.

    has(prop: string): boolean {
        const m = new Map(
            Array.from(Object.entries(this), (v) => [v[1], v[0]])
        );
        return m.has(prop);
    }
}

export const IdxBthSigDex = new IndexedBothSigCodex();

export class Xizage {
    public hs: number;
    public ss: number;
    public os: number;
    public fs?: number;
    public ls: number;

    constructor(hs: number, ss: number, os: number, fs?: number, ls?: number) {
        this.hs = hs;
        this.ss = ss;
        this.os = os;
        this.fs = fs;
        this.ls = ls!;
    }
}

export interface IndexerArgs {
    raw?: Uint8Array | undefined;
    code?: string | undefined;
    index?: number;
    ondex?: number;
    qb64b?: Uint8Array | undefined;
    qb64?: string | undefined;
    qb2?: Uint8Array | undefined;
}

export class Indexer {
    public Codex = IdrDex;

    static Hards = new Map<string, number>([
        ['A', 1],
        ['B', 1],
        ['C', 1],
        ['D', 1],
        ['E', 1],
        ['F', 1],
        ['G', 1],
        ['H', 1],
        ['I', 1],
        ['J', 1],
        ['K', 1],
        ['L', 1],
        ['M', 1],
        ['N', 1],
        ['O', 1],
        ['P', 1],
        ['Q', 1],
        ['R', 1],
        ['S', 1],
        ['T', 1],
        ['U', 1],
        ['V', 1],
        ['W', 1],
        ['X', 1],
        ['Y', 1],
        ['Z', 1],
        ['a', 1],
        ['b', 1],
        ['c', 1],
        ['d', 1],
        ['e', 1],
        ['f', 1],
        ['g', 1],
        ['h', 1],
        ['i', 1],
        ['j', 1],
        ['k', 1],
        ['l', 1],
        ['m', 1],
        ['n', 1],
        ['o', 1],
        ['p', 1],
        ['q', 1],
        ['r', 1],
        ['s', 1],
        ['t', 1],
        ['u', 1],
        ['v', 1],
        ['w', 1],
        ['x', 1],
        ['y', 1],
        ['z', 1],
        ['0', 2],
        ['1', 2],
        ['2', 2],
        ['3', 2],
        ['4', 2],
    ]);

    static Sizes = new Map(
        Object.entries({
            A: new Xizage(1, 1, 0, 88, 0),
            B: new Xizage(1, 1, 0, 88, 0),
            C: new Xizage(1, 1, 0, 88, 0),
            D: new Xizage(1, 1, 0, 88, 0),
            E: new Xizage(1, 1, 0, 88, 0),
            F: new Xizage(1, 1, 0, 88, 0),
            '0A': new Xizage(2, 2, 1, 156, 0),
            '0B': new Xizage(2, 2, 1, 156, 0),

            '2A': new Xizage(2, 4, 2, 92, 0),
            '2B': new Xizage(2, 4, 2, 92, 0),
            '2C': new Xizage(2, 4, 2, 92, 0),
            '2D': new Xizage(2, 4, 2, 92, 0),
            '2E': new Xizage(2, 4, 2, 92, 0),
            '2F': new Xizage(2, 4, 2, 92, 0),

            '3A': new Xizage(2, 6, 3, 160, 0),
            '3B': new Xizage(2, 6, 3, 160, 0),

            '0z': new Xizage(2, 2, 0, undefined, 0),
            '1z': new Xizage(2, 2, 1, 76, 1),
            '4z': new Xizage(2, 6, 3, 80, 1),
        })
    );

    private _code: string = '';
    private _index: number = -1;
    private _ondex: number | undefined;
    private _raw: Uint8Array = new Uint8Array(0);

    constructor({
        raw = undefined,
        code = IdrDex.Ed25519_Sig,
        index = 0,
        ondex = undefined,
        qb64b = undefined,
        qb64 = undefined,
        qb2 = undefined,
    }: IndexerArgs) {
        if (raw != undefined) {
            if (code == undefined) {
                throw new EmptyMaterialError(
                    `Improper initialization need either (raw and code) or qb64b or qb64 or qb2.`
                );
            }

            if (!Indexer.Sizes.has(code)) {
                throw new Error(`Unsupported code=${code}.`);
            }

            const xizage = Indexer.Sizes.get(code)!;
            const os = xizage.os;
            const fs = xizage.fs;
            const cs = xizage.hs + xizage.ss;
            const ms = xizage.ss - xizage.os;

            if (!Number.isInteger(index) || index < 0 || index > 64 ** ms - 1) {
                throw new Error(`Invalid index=${index} for code=${code}.`);
            }

            if (
                ondex != undefined &&
                xizage.os != 0 &&
                !(ondex >= 0 && ondex <= 64 ** os - 1)
            ) {
                throw new Error(`Invalid ondex=${ondex} for code=${code}.`);
            }

            if (IdxCrtSigDex.has(code) && ondex != undefined) {
                throw new Error(`Non None ondex=${ondex} for code=${code}.`);
            }

            if (IdxBthSigDex.has(code)) {
                if (ondex == undefined) {
                    ondex = index;
                } else {
                    if (ondex != index && os == 0) {
                        throw new Error(
                            `Non matching ondex=${ondex} and index=${index} for code=${code}.`
                        );
                    }
                }
            }

            if (fs == undefined) {
                throw new Error('variable length unsupported');
            }
            // TODO: Don't support this code
            //  if not fs:  # compute fs from index
            //       if cs % 4:
            //           raise InvalidCodeSizeError(f"Whole code size not multiple of 4 for "
            //                                      f"variable length material. cs={cs}.")
            //       if os != 0:
            //           raise InvalidCodeSizeError(f"Non-zero other index size for "
            //                                      f"variable length material. os={os}.")
            //       fs = (index * 4) + cs
            const rawsize = Math.floor(((fs - cs) * 3) / 4);
            raw = raw.slice(0, rawsize);

            if (raw.length != rawsize) {
                throw new Error(
                    `Not enougth raw bytes for code=${code} and index=${index} ,expected ${rawsize} got ${raw.length}.`
                );
            }

            this._code = code;
            this._index = index;
            this._ondex = ondex;
            this._raw = raw;
        } else if (qb64b != undefined) {
            const qb64 = d(qb64b);
            this._exfil(qb64);
        } else if (qb64 != undefined) {
            this._exfil(qb64);
        } else if (qb2 != undefined) {
            this._bexfil(qb2);
        } else {
            throw new EmptyMaterialError(
                `Improper initialization need either (raw and code and index) or qb64b or qb64 or qb2.`
            );
        }
    }

    private _bexfil(qb2: Uint8Array) {
        throw new Error(`qb2 not yet supported: ${qb2}`);
    }

    public static _rawSize(code: string) {
        const xizage = Indexer.Sizes.get(code)!;
        return Math.floor(xizage.fs! - ((xizage.hs + xizage.ss) * 3) / 4);
    }

    get code(): string {
        return this._code;
    }

    get raw(): Uint8Array {
        return this._raw;
    }

    get index(): number {
        return this._index;
    }

    get ondex(): number | undefined {
        return this._ondex;
    }

    get qb64(): string {
        return this._infil();
    }

    get qb64b() {
        return b(this.qb64);
    }

    private _infil(): string {
        const code = this.code;
        const index = this.index;
        const ondex = this.ondex;
        const raw = this.raw;

        const ps = (3 - (raw.length % 3)) % 3;
        const xizage = Indexer.Sizes.get(code)!;
        const cs = xizage.hs + xizage.ss;
        const ms = xizage.ss - xizage.os;

        // TODO: don't support this code
        //  if not fs:  # compute fs from index
        //       if cs % 4:
        //           raise InvalidCodeSizeError(f"Whole code size not multiple of 4 for "
        //                                      f"variable length material. cs={cs}.")
        //       if os != 0:
        //           raise InvalidCodeSizeError(f"Non-zero other index size for "
        //                                      f"variable length material. os={os}.")
        //       fs = (index * 4) + cs

        if (index < 0 || index > 64 ** ms - 1) {
            throw new Error(`Invalid index=${index} for code=${code}.`);
        }

        if (
            ondex != undefined &&
            xizage.os != 0 &&
            !(ondex >= 0 && ondex <= 64 ** xizage.os - 1)
        ) {
            throw new Error(
                `Invalid ondex=${ondex} for os=${xizage.os} and code=${code}.`
            );
        }

        const both = `${code}${intToB64(index, ms)}${intToB64(
            ondex == undefined ? 0 : ondex,
            xizage.os
        )}`;

        if (both.length != cs) {
            throw new Error(
                `Mismatch code size = ${cs} with table = ${both.length}.`
            );
        }

        if (cs % 4 != ps - xizage.ls) {
            throw new Error(
                `Invalid code=${both} for converted raw pad size=${ps}.`
            );
        }

        const bytes = new Uint8Array(ps + raw.length);
        for (let i = 0; i < ps; i++) {
            bytes[i] = 0;
        }
        for (let i = 0; i < raw.length; i++) {
            const odx = i + ps;
            bytes[odx] = raw[i];
        }

        const full =
            both + Base64.encode(Buffer.from(bytes)).slice(ps - xizage.ls);
        if (full.length != xizage.fs) {
            throw new Error(`Invalid code=${both} for raw size=${raw.length}.`);
        }

        return full;
    }

    _exfil(qb64: string) {
        if (qb64.length == 0) {
            throw new Error('Empty Material');
        }

        const first = qb64[0];
        if (!Array.from(Indexer.Hards.keys()).includes(first)) {
            throw new Error(`Unexpected code ${first}`);
        }

        const hs = Indexer.Hards.get(first)!;
        if (qb64.length < hs) {
            throw new Error(`Need ${hs - qb64.length} more characters.`);
        }

        const hard = qb64.slice(0, hs);
        if (!Array.from(Indexer.Sizes.keys()).includes(hard)) {
            throw new Error(`Unsupported code ${hard}`);
        }

        const xizage = Indexer.Sizes.get(hard)!;
        const cs = xizage.hs + xizage.ss; // both hard + soft code size
        const ms = xizage.ss - xizage.os;

        if (qb64.length < cs) {
            throw new Error(`Need ${cs - qb64.length} more characters.`);
        }

        const sindex = qb64.slice(hs, hs + ms);
        const index = b64ToInt(sindex);

        const sondex = qb64.slice(hs + ms, hs + ms + xizage.os);
        let ondex;
        if (IdxCrtSigDex.has(hard)) {
            ondex = xizage.os != 0 ? b64ToInt(sondex) : undefined;
            if (ondex != 0 && ondex != undefined) {
                throw new Error(`Invalid ondex=${ondex} for code=${hard}.`);
            } else {
                ondex = undefined;
            }
        } else {
            ondex = xizage.os != 0 ? b64ToInt(sondex) : index;
        }

        if (xizage.fs == undefined) {
            throw new Error('variable length not supported');
        }
        // TODO: support variable length
        // if not fs:  # compute fs from index which means variable length
        //     if cs % 4:
        //         raise ValidationError(f"Whole code size not multiple of 4 for "
        //                               f"variable length material. cs={cs}.")
        //     if os != 0:
        //         raise ValidationError(f"Non-zero other index size for "
        //                               f"variable length material. os={os}.")
        //     fs = (index * 4) + cs

        if (qb64.length < xizage.fs) {
            throw new Error(`Need ${xizage.fs - qb64.length} more chars.`);
        }

        qb64 = qb64.slice(0, xizage.fs);
        const ps = cs % 4;
        const pbs = 2 * ps != 0 ? ps : xizage.ls;
        let raw;
        if (ps != 0) {
            const base = new Array(ps + 1).join('A') + qb64.slice(cs);
            const paw = Base64.decode(base); // decode base to leave prepadded raw
            const pi = readInt(paw.slice(0, ps)); // prepad as int
            if (pi & (2 ** pbs - 1)) {
                // masked pad bits non-zero
                throw new Error(
                    `Non zeroed prepad bits = {pi & (2 ** pbs - 1 ):<06b} in {qb64b[cs:cs+1]}.`
                );
            }
            raw = paw.slice(ps); // strip off ps prepad paw bytes
        } else {
            const base = qb64.slice(cs);
            const paw = Base64.decode(base);
            const li = readInt(paw.slice(0, xizage!.ls));
            if (li != 0) {
                if (li == 1) {
                    throw new Error(`Non zeroed lead byte = 0x{li:02x}.`);
                } else {
                    throw new Error(`Non zeroed lead bytes = 0x{li:04x}`);
                }
            }
            raw = paw.slice(xizage!.ls);
        }

        if (raw.length != Math.floor(((qb64.length - cs) * 3) / 4)) {
            throw new Error(`Improperly qualified material = ${qb64}`);
        }

        this._code = hard;
        this._index = index;
        this._ondex = ondex;
        this._raw = new Uint8Array(raw); // must be bytes for crpto opts and immutable not bytearray
    }
}
