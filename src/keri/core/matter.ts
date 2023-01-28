import {EmptyMaterialError} from "./kering";

const {intToB64, readInt} = require('./core');
const Base64 = require('urlsafe-base64');
import {b, d} from "./core";

export class Codex {
    has(prop: string): boolean {
        let m = new Map(Array.from(Object.entries(this), (v) => [v[1], v[0]]))
        return m.has(prop)
    }
}

export class MatterCodex extends Codex {
    Ed25519_Seed:         string = 'A'    // Ed25519 256 bit random seed for private key
    Ed25519N:             string = 'B'    // Ed25519 verification key non-transferable, basic derivation.
    X25519:               string = 'C'    // X25519 public encryption key, converted from Ed25519 or Ed25519N.
    Ed25519:              string = 'D'    // Ed25519 verification key basic derivation
    Blake3_256:           string = 'E'    // Blake3 256 bit digest self-addressing derivation.
    X25519_Private:       string = 'O'    // X25519 private decryption key converted from Ed25519
    X25519_Cipher_Seed:   string = 'P'    // X25519 124 char b64 Cipher of 44 char qb64 Seed
    X25519_Cipher_Salt:   string = '1AAH' // X25519 100 char b64 Cipher of 24 char qb64 Salt
    Salt_128:             string = '0A'   // 128 bit random salt or 128 bit number (see Huge)
    Ed25519_Sig:          string = '0B'   // Ed25519 signature.
}

export const MtrDex = new MatterCodex()


export class NonTransCodex extends Codex {
    Ed25519N: string = 'B'  // Ed25519 verification key non-transferable, basic derivation.
    ECDSA_256k1N: string = '1AAA'  // ECDSA secp256k1 verification key non-transferable, basic derivation.
    Ed448N: string = '1AAC'  // Ed448 non-transferable prefix public signing verification key. Basic derivation.
}

export const NonTransDex = new NonTransCodex()


export class DigiCodex extends Codex {
    Blake3_256: string = 'E'  // Blake3 256 bit digest self-addressing derivation.
    Blake2b_256: string = 'F'  // Blake2b 256 bit digest self-addressing derivation.
    Blake2s_256: string = 'G'  // Blake2s 256 bit digest self-addressing derivation.
    SHA3_256: string = 'H'  // SHA3 256 bit digest self-addressing derivation.
    SHA2_256: string = 'I'  // SHA2 256 bit digest self-addressing derivation.
    Blake3_512: string = '0D'  // Blake3 512 bit digest self-addressing derivation.
    Blake2b_512: string = '0E'  // Blake2b 512 bit digest self-addressing derivation.
    SHA3_512: string = '0F'  // SHA3 512 bit digest self-addressing derivation.
    SHA2_512: string = '0G'  // SHA2 512 bit digest self-addressing derivation.
}

export const DigiDex = new DigiCodex()

export class Sizage {
    public hs: number;
    public ss: number;
    public ls: number;
    public fs: number;

    constructor(hs: number, ss: number, fs: number, ls: number) {
        this.hs = hs;
        this.ss = ss;
        this.fs = fs;
        this.ls = ls;
    }
}

export interface MatterArgs {
    raw?: Uint8Array | undefined
    code?: string
    qb64b?: Uint8Array | undefined
    qb64?: string
    qb2?: Uint8Array | undefined
}

export class Matter {

    static Sizes = new Map(Object.entries({
        'A': new Sizage(1, 0, 44, 0),
        'B': new Sizage(1, 0, 44, 0),
        'C': new Sizage(1, 0, 44, 0),
        'D': new Sizage(1, 0, 44, 0),
        'E': new Sizage(1, 0, 44, 0),
        'O': new Sizage(1, 0, 44, 0),
        'P': new Sizage(1, 0, 124, 0),
        "0A": new Sizage(2, 0, 24, 0),
        '0B': new Sizage(2, 0, 88, 0),
        '1AAH': new Sizage(4, 0, 100, 0),
    }));

    static Hards = new Map<string, number>([['A', 1], ['B', 1], ['C', 1], ['D', 1], ['E', 1], ['F', 1], ['G', 1],
        ['H', 1], ['I', 1], ['J', 1], ['K', 1], ['L', 1], ['M', 1], ['N', 1], ['O', 1], ['P', 1], ['Q', 1], ['R', 1],
        ['S', 1], ['T', 1], ['U', 1], ['V', 1], ['W', 1], ['X', 1], ['Y', 1], ['Z', 1], ['a', 1], ['b', 1], ['c', 1],
        ['d', 1], ['e', 1], ['f', 1], ['g', 1], ['h', 1], ['i', 1], ['j', 1], ['k', 1], ['l', 1], ['m', 1], ['n', 1],
        ['o', 1], ['p', 1], ['q', 1], ['r', 1], ['s', 1], ['t', 1], ['u', 1], ['v', 1], ['w', 1], ['x', 1], ['y', 1],
        ['z', 1], ['0', 2], ['1', 4], ['2', 4], ['3', 4], ['4', 2], ['5', 2], ['6', 2], ['7', 4], ['8', 4], ['9', 4]])


    private _code: string = "";
    private _size: number = -1;
    private _raw: Uint8Array = new Uint8Array(0);

    constructor({raw, code = MtrDex.Ed25519N, qb64b, qb64, qb2}: MatterArgs) {

        let size = -1
        if (raw != undefined) {
            if (code.length == 0) {
                throw new Error("Improper initialization need either (raw and code) or qb64b or qb64 or qb2.")
            }

            // Add support for variable size codes here if needed, this code only works for stable size codes
            let sizage = Matter.Sizes.get(code)
            if (sizage!.fs == -1) {  // invalid
                throw new Error(`Unsupported variable size code=${code}`)
            }

            let rize = Matter._rawSize(code)
            raw = raw.slice(0, rize)  // copy only exact size from raw stream
            if (raw.length != rize) { // forbids shorter
                throw new Error(`Not enougth raw bytes for code=${code} expected ${rize} got ${raw.length}.`)
            }

            this._code = code  // hard value part of code
            this._size = size  // soft value part of code in int
            this._raw = raw    // crypto ops require bytes not bytearray

        } else if (qb64 !== undefined) {
            this._exfil(qb64)
        } else if (qb64b !== undefined) {
            let qb64 = d(qb64b)
            this._exfil(qb64)
        } else if (qb2 !== undefined) {
            this._bexfil(qb2)
        } else {
            throw new EmptyMaterialError("EmptyMaterialError");
        }
    }

    get code(): string {
        return this._code;
    }

    get size() {
        return this._size;
    }

    get raw(): Uint8Array {
        return this._raw
    }

    get qb64() {
        return this._infil();
    }

    get qb64b() {
        return b(this.qb64)
    }

    get transferable(): boolean {
        return !NonTransDex.has(this.code)
    }

    get digestive(): boolean {
        return DigiDex.has(this.code)
    }

    static _rawSize(code: string) {
        let sizage = this.Sizes.get(code)  // get sizes
        let cs = sizage!.hs + sizage!.ss  // both hard + soft code size
        if (sizage!.fs === -1) {
            throw Error(`Non-fixed raw size code ${code}.`)
        }

        return (Math.floor((sizage!.fs - cs) * 3 / 4)) - sizage!.ls

    }

    static _leadSize(code: string) {
        let sizage = this.Sizes.get(code);
        return sizage!.ls
    }

    get both() {
        let sizage = Matter.Sizes.get(this.code);
        return `${this.code}${intToB64(this.size, sizage!.ls)}`
    }


    private _infil() {
        let code = this.code;
        let raw = this.raw;

        let ps = ((3 - (raw.length % 3)) % 3);  // pad size chars or lead size bytes
        let sizage = Matter.Sizes.get(code);

        if (sizage!.fs === -1) {  // Variable size code, NOT SUPPORTED
            throw new Error("Variable sized codes not supported... yet");
        } else {
            let both = code
            let cs = both.length
            if ((cs % 4) != ps - sizage!.ls) {  // adjusted pad given lead bytes
                throw new Error(`Invalid code=${both} for converted raw pad size=${ps}, ${raw.length}.`);
            }
            // prepad, convert, and replace upfront
            // when fixed and ls != 0 then cs % 4 is zero and ps==ls
            // otherwise  fixed and ls == 0 then cs % 4 == ps
            let bytes = new Uint8Array(ps + raw.length);
            for (let i = 0; i < ps; i++) {
                bytes[i] = 0;
            }
            for (let i = 0; i < raw.length; i++) {
                let odx = i + ps
                bytes[odx] = raw[i];
            }

            return both + Base64.encode(Buffer.from(bytes)).slice(cs % 4)
        }
    }

    private _exfil(qb64: string) {
        if (qb64.length == 0) {
            throw new Error("Empty Material")
        }

        let first = qb64[0];
        if (!Array.from(Matter.Hards.keys()).includes(first)) {
            throw new Error(`Unexpected code ${first}`)
        }

        let hs = Matter.Hards.get(first);
        if (qb64.length < hs!) {
            throw new Error(`Shortage Error`)
        }

        let hard = qb64.slice(0, hs);
        if (!Array.from(Matter.Sizes.keys()).includes(hard)) {
            throw new Error(`Unsupported code ${hard}`)
        }

        let sizage = Matter.Sizes.get(hard);
        let cs = sizage!.hs + sizage!.ss;
        let size = -1;
        if (sizage!.fs == -1) { // Variable size code, Not supported
            throw new Error("Variable size codes not supported yet")
        } else {
            size = sizage!.fs
        }

        if (qb64.length < sizage!.fs) {
            throw new Error(`Need ${sizage!.fs - qb64.length} more chars.`)
        }

        qb64 = qb64.slice(0, sizage!.fs)
        let ps = cs % 4
        let pbs = 2 * (ps == 0 ? sizage!.ls : ps)
        let raw
        if (ps != 0) {
            let base = new Array(ps + 1).join('A') + qb64.slice(cs);
            let paw = Base64.decode(base)  // decode base to leave prepadded raw
            let pi = (readInt(paw.subarray(0, ps)))  // prepad as int
            if (pi & (2 ** pbs - 1)) {  // masked pad bits non-zero
                throw new Error(`Non zeroed prepad bits = {pi & (2 ** pbs - 1 ):<06b} in {qb64b[cs:cs+1]}.`)
            }
            raw = paw.subarray(ps)  // strip off ps prepad paw bytes
        } else {
            let base = qb64.slice(cs);
            let paw = Base64.decode(base);
            let li = readInt(paw.subarray(0, sizage!.ls))
            if (li != 0) {
                if (li == 1) {
                    throw new Error(`Non zeroed lead byte = 0x{li:02x}.`)
                } else {
                    throw new Error(`Non zeroed lead bytes = 0x{li:04x}`)
                }
            }
            raw = paw.subarray(sizage!.ls)
        }

        this._code = hard  // hard only
        this._size = size
        this._raw = Uint8Array.from(raw)  // ensure bytes so immutable and for crypto ops
    }

    private _bexfil(qb2: Uint8Array) {
        throw new Error(`qb2 not yet supported: ${qb2}`)
    }
}
