/**
 * Serialization types supported by the KERI and ACDC protocols and this Signify implementation.
 */
export enum Serials {
    JSON = 'JSON',
}

/**
 * Protocol types supported by the KERI and ACDC protocols and this Signify implementation.
 */
export enum Protocols {
    KERI = 'KERI',
    ACDC = 'ACDC',
}

/**
 * Represents a protocol version of the KERI, ACDC, or other protocol specified in a CESR version string.
 */
export class Version {
    public major: number;
    public minor: number;

    constructor(major: number = 1, minor: number = 0) {
        this.major = major;
        this.minor = minor;
    }
}

/**
 * Denotes version 1.0 of a protocol.
 */
export const Vrsn_1_0 = new Version();

/**
 * Types of KERI and ACDC events.
 */
export const Ilks = {
    icp: 'icp',
    rot: 'rot',
    ixn: 'ixn',
    dip: 'dip',
    drt: 'drt',
    rct: 'rct',
    vrc: 'vrc',
    rpy: 'rpy',
    exn: 'exn',
    vcp: 'vcp',
    iss: 'iss',
    rev: 'rev',
    bis: 'bis',
    brv: 'brv',
};

/**
 * Field labels for an inception event in V1 of the KERI protocol.
 */
export const IcpLabels = [
    'v',
    'i',
    's',
    't',
    'kt',
    'k',
    'n',
    'bt',
    'b',
    'c',
    'a',
];

/**
 * Field labels for an delegated inception event in V1 of the KERI protocol.
 */
export const DipLabels = [
    'v',
    'i',
    's',
    't',
    'kt',
    'k',
    'n',
    'bt',
    'b',
    'c',
    'a',
    'di',
];

/**
 * Field labels for a rotation event in V1 of the KERI protocol.
 */
export const RotLabels = [
    'v',
    'i',
    's',
    't',
    'p',
    'kt',
    'k',
    'n',
    'bt',
    'br',
    'ba',
    'a',
];

/**
 * Field labels for an delegated rotation event in V1 of the KERI protocol.
 */
export const DrtLabels = [
    'v',
    'i',
    's',
    't',
    'p',
    'kt',
    'k',
    'n',
    'bt',
    'br',
    'ba',
    'a',
];

/**
 * Field labels for an interaction event in V1 of the KERI protocol.
 */
export const IxnLabels = ['v', 'i', 's', 't', 'p', 'a'];

/**
 * Field labels for a key state notice event in V1 of the KERI protocol.
 */
export const KsnLabels = [
    'v',
    'i',
    's',
    't',
    'p',
    'd',
    'f',
    'dt',
    'et',
    'kt',
    'k',
    'n',
    'bt',
    'b',
    'c',
    'ee',
    'di',
    'r',
];

/**
 * Field labels for a reply event in V1 of the KERI protocol.
 */
export const RpyLabels = ['v', 't', 'd', 'dt', 'r', 'a'];

/**
 * Full size of a CESR version string in bytes.
 */
export const VERFULLSIZE = 17;
/**
 * Minimum number of bytes a CESR parser must sniff to receive the entire version string.
 */
export const MINSNIFFSIZE = 12 + VERFULLSIZE;
export const MINSIGSIZE = 4;

// const version_pattern = 'KERI(?P<major>[0-9a-f])(?P<minor>[0-9a-f])
// (?P<kind>[A-Z]{4})(?P<size>[0-9a-f]{6})'
// const version_pattern1 = `KERI\(\?P<major>\[0\-9a\-f\]\)\(\?P<minor>\[0\-9a\-f\]\)\
// (\?P<kind>\[A\-Z\]\{4\}\)\(\?P<size>\[0\-9a\-f\]\{6\}\)_`

/**
 * Regular expression for a version 1 CESR object version string.
 */
export const VEREX = '(KERI|ACDC)([0-9a-f])([0-9a-f])([A-Z]{4})([0-9a-f]{6})_';

/**
 * An interface for a basic dictionary type keyed by string with any value type.
 * Mimics the Python dictionary type.
 */
export interface Dict<TValue> {
    [id: string]: TValue;
}

/**
 * Parses a serialization version string into the protocol, protocol version, serialization type, and raw size.
 * Uses regex matchers to validate and extract version string parts.
 * @param {string} versionString version string
 * @return {Object} tuple of prototol (KERI or ACDC), kind of serialization like cbor,json, or mgpk,
 *                  protocol version, and raw size of serialization
 */
export function deversify(
    versionString: string
): [Protocols, Serials, Version, string] {
    let kind;
    let size;
    let proto;
    const version = Vrsn_1_0;

    // we need to identify how to match the buffers pattern ,like we do regex matching for strings
    const re = new RegExp(VEREX);

    // Regex pattern matching
    const match = re.exec(versionString);

    if (match) {
        [proto, version.major, version.minor, kind, size] = [
            match[1],
            +match[2],
            +match[3],
            match[4],
            match[5],
        ];
        if (!Object.values(Serials).includes(kind as Serials)) {
            throw new Error(`Invalid serialization kind = ${kind}`);
        }
        if (!Object.values(Protocols).includes(proto as Protocols)) {
            throw new Error(`Invalid serialization kind = ${kind}`);
        }

        const ta = kind as keyof typeof Serials;
        kind = Serials[ta];
        const pa = proto as keyof typeof Protocols;
        proto = Protocols[pa];

        return [proto, kind, version, size];
    }
    throw new Error(`Invalid version string = ${versionString}`);
}

/**
 * Returns a valid KERI serialization version string specifying the protocol,
 * protocol version, serialization type, and raw byte size of the serialization.
 *
 * Defaults to version 1.0.
 * @param ident
 * @param version
 * @param kind
 * @param size
 */
export function versify(
    ident: Protocols = Protocols.KERI,
    version?: Version,
    kind: Serials = Serials.JSON,
    size: number = 0
) {
    version = version == undefined ? Vrsn_1_0 : version; // defaults to Version 1
    const major = version.major.toString(16); // hex digits
    const minor = version.minor.toString(16); // hex digits
    // raw size in hex digits zero padded to 6 characters
    const rawSize = size.toString(16).padStart(6, '0');
    const terminationChar = '_'; // v1 termination character
    return `${ident}${major}${minor}${kind}${rawSize}${terminationChar}`;
}

/**
 * Map allowing lookup of Base64URLSafe characters by index.
 */
export const B64ChrByIdx = new Map<number, string>([
    [0, 'A'],
    [1, 'B'],
    [2, 'C'],
    [3, 'D'],
    [4, 'E'],
    [5, 'F'],
    [6, 'G'],
    [7, 'H'],
    [8, 'I'],
    [9, 'J'],
    [10, 'K'],
    [11, 'L'],
    [12, 'M'],
    [13, 'N'],
    [14, 'O'],
    [15, 'P'],
    [16, 'Q'],
    [17, 'R'],
    [18, 'S'],
    [19, 'T'],
    [20, 'U'],
    [21, 'V'],
    [22, 'W'],
    [23, 'X'],
    [24, 'Y'],
    [25, 'Z'],
    [26, 'a'],
    [27, 'b'],
    [28, 'c'],
    [29, 'd'],
    [30, 'e'],
    [31, 'f'],
    [32, 'g'],
    [33, 'h'],
    [34, 'i'],
    [35, 'j'],
    [36, 'k'],
    [37, 'l'],
    [38, 'm'],
    [39, 'n'],
    [40, 'o'],
    [41, 'p'],
    [42, 'q'],
    [43, 'r'],
    [44, 's'],
    [45, 't'],
    [46, 'u'],
    [47, 'v'],
    [48, 'w'],
    [49, 'x'],
    [50, 'y'],
    [51, 'z'],
    [52, '0'],
    [53, '1'],
    [54, '2'],
    [55, '3'],
    [56, '4'],
    [57, '5'],
    [58, '6'],
    [59, '7'],
    [60, '8'],
    [61, '9'],
    [62, '-'],
    [63, '_'],
]);

/**
 * Map allowing lookup of Base64URLSafe index by character.
 */
export const B64IdxByChr = new Map<string, number>(
    Array.from(B64ChrByIdx, (entry) => [entry[1], entry[0]])
);

/**
 * Converts an integer to a Base64URLSafe encoded string, left padded as specified.
 * @param i integer to convert
 * @param l minimum length of Base64 digits left padded with Base64 0 == 'A' character.
 */
export function intToB64(i: number, l = 1): string {
    let out = '';
    while (l != 0) {
        out = B64ChrByIdx.get(i % 64) + out;
        i = Math.floor(i / 64);
        if (i == 0) {
            break;
        }
    }

    const x = l - out.length;
    for (let i = 0; i < x; i++) {
        out = 'A' + out;
    }

    return out;
}

/**
 * Converts an integer to a Base64URLSafe encoded string to a byte array, left padded as specified.
 * @param i integer to convert
 * @param l minimum length of Base64 digits left padded with Base64 0 == 'A' character.
 */
export function intToB64b(n: number, l: number = 1): Uint8Array {
    const s = intToB64(n, l);
    return b(s);
}

/**
 * Converts a Base64URLSafe encoded string to an integer.
 * @param s string to convert
 */
export function b64ToInt(s: string): number {
    if (s.length == 0) {
        throw new Error('Empty string, conversion undefined.');
    }

    let i = 0;
    const rev = s.split('').reverse();
    rev.forEach((c: string, e: number) => {
        i |= B64IdxByChr.get(c)! << (e * 6);
    });

    return i;
}

// Built in encoder and decoder for converting to and from UTF-8 strings and Uint8Array byte arrays.
const encoder = new TextEncoder();
const decoder = new TextDecoder();

/**
 * Converts a UTF-8 string to bytes.
 * Output is an encoded array of bytes. Assumes UTF-8 encoding.
 * @param s string to be encoded as an array of bytes
 */
export function b(s?: string): Uint8Array {
    return encoder.encode(s);
}

/**
 * Convert bytes to UTF-8 string.
 * @param u array of bytes to be converted to UTF-8 string.
 */
export function d(u?: Uint8Array): string {
    return decoder.decode(u);
}

/**
 * Concatenates two byte arrays together in a new byte array.
 * @param one first byte array to be concatenated
 * @param two second byte array to be concatenated
 */
export function concat(one: Uint8Array, two: Uint8Array): Uint8Array {
    const out = new Uint8Array(one.length + two.length);
    out.set(one);
    out.set(two, one.length);
    return out;
}

/**
 * Converts a big-endian byte array into an integer.
 *
 * @param array - A `Uint8Array` of bytes representing a big-endian integer.
 * @returns The integer represented by the byte array.
 *
 * Example:
 *   readInt(Uint8Array([0x01, 0x02, 0x03])) // returns 66051
 *
 * How it works:
 * - The function interprets the array as a big-endian number.
 * - Each byte is added to the integer after shifting the previous value left by 8 bits (multiplying by 256).
 */
export function readInt(array: Uint8Array) {
    let value = 0;
    for (let i = 0; i < array.length; i++) {
        value = value * 256 + array[i];
    }
    return value;
}
