export enum Serials {
    JSON = 'JSON',
}

export enum Ident {
    KERI = 'KERI',
    ACDC = 'ACDC',
}

export class Version {
    public major: number;
    public minor: number;

    constructor(major: number = 1, minor: number = 0) {
        this.major = major;
        this.minor = minor;
    }
}

export const Versionage = new Version();

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
};

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
export const IxnLabels = ['v', 'i', 's', 't', 'p', 'a'];

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

export const RpyLabels = ['v', 't', 'd', 'dt', 'r', 'a'];

const encoder = new TextEncoder();
const decoder = new TextDecoder();

export const VERFULLSIZE = 17;
export const MINSNIFFSIZE = 12 + VERFULLSIZE;
export const MINSIGSIZE = 4;

// const version_pattern = 'KERI(?P<major>[0-9a-f])(?P<minor>[0-9a-f])
// (?P<kind>[A-Z]{4})(?P<size>[0-9a-f]{6})'
// const version_pattern1 = `KERI\(\?P<major>\[0\-9a\-f\]\)\(\?P<minor>\[0\-9a\-f\]\)\
// (\?P<kind>\[A\-Z\]\{4\}\)\(\?P<size>\[0\-9a\-f\]\{6\}\)_`

export const VEREX = '(KERI|ACDC)([0-9a-f])([0-9a-f])([A-Z]{4})([0-9a-f]{6})_';

export interface Dict<TValue> {
    [id: string]: TValue;
}

// Regex pattern matching

/**
 * @description This function is use to deversify the version
 * Here we will use regex to  to validate and extract serialization kind,size and version
 * @param {string} versionString   version string
 * @return {Object}  contaning prototol (KERI or ACDC), kind of serialization like cbor,json,mgpk
 *                    version = version of object ,size = raw size integer
 */
export function deversify(
    versionString: string
): [Ident, Serials, Version, string] {
    let kind;
    let size;
    let proto;
    const version = Versionage;

    // we need to identify how to match the buffers pattern ,like we do regex matching for strings
    const re = new RegExp(VEREX);

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
        if (!Object.values(Ident).includes(proto as Ident)) {
            throw new Error(`Invalid serialization kind = ${kind}`);
        }

        let ta = kind as keyof typeof Serials;
        kind = Serials[ta];
        let pa = proto as keyof typeof Ident;
        proto = Ident[pa];

        return [proto, kind, version, size];
    }
    throw new Error(`Invalid version string = ${versionString}`);
}

export function versify(
    ident: Ident = Ident.KERI,
    version?: Version,
    kind: Serials = Serials.JSON,
    size: number = 0
) {
    version = version == undefined ? Versionage : version;

    return `${ident}${version.major.toString(
        16
    )}${version.minor.toString()}${kind}${size.toString(16).padStart(6, '0')}_`;
}

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

export const B64IdxByChr = new Map<string, number>(
    Array.from(B64ChrByIdx, (entry) => [entry[1], entry[0]])
);

export function intToB64(i: number, l = 1): string {
    let out = '';
    while (l != 0) {
        out = B64ChrByIdx.get(i % 64) + out;
        i = Math.floor(i / 64);
        if (i == 0) {
            break;
        }
    }

    let x = l - out.length;
    for (let i = 0; i < x; i++) {
        out = 'A' + out;
    }

    return out;
}

export function intToB64b(n: number, l: number = 1): Uint8Array {
    let s = intToB64(n, l);
    return b(s);
}

export function b64ToInt(s: string): number {
    if (s.length == 0) {
        throw new Error('Empty string, conversion undefined.');
    }

    let i = 0;
    let rev = s.split('').reverse();
    rev.forEach((c: string, e: number) => {
        i |= B64IdxByChr.get(c)! << (e * 6);
    });

    return i;
}

export function b(s?: string): Uint8Array {
    return encoder.encode(s);
}

export function d(u?: Uint8Array): string {
    return decoder.decode(u);
}

export function concat(one: Uint8Array, two: Uint8Array): Uint8Array {
    let out = new Uint8Array(one.length + two.length);
    out.set(one);
    out.set(two, one.length);
    return out;
}

export function readInt(array: Uint8Array) {
    let value = 0;
    for (let i = 0; i < array.length; i++) {
        value = value * 256 + array[i];
    }
    return value;
}
