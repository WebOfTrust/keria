import { MtrDex } from './matter';
import {
    deversify,
    Dict,
    Protocols,
    Serials,
    versify,
    Version,
    Vrsn_1_0,
} from './core';
import { Verfer } from './verfer';
import { Diger } from './diger';
import { CesrNumber } from './number';

export class Serder {
    private _kind: Serials;
    private _raw: string = '';
    private _sad: Dict<any> = {};
    private _proto: Protocols = Protocols.KERI;
    private _size: number = 0;
    private _version: Version = Vrsn_1_0;
    private readonly _code: string;

    /**
     * Creates a new Serder object from a self-addressing data dictionary.
     * @param sad self-addressing data dictionary.
     * @param kind serialization type to produce
     * @param code derivation code for the prefix
     */
    constructor(
        sad: Dict<any>,
        kind: Serials = Serials.JSON,
        code: string = MtrDex.Blake3_256
    ) {
        let [raw, proto, eKind, eSad, version] = this._exhale(sad, kind);
        this._raw = raw;
        this._sad = eSad;
        this._proto = proto;
        this._version = version;
        this._code = code;
        this._kind = eKind;
        this._size = raw.length;
    }

    get sad(): Dict<any> {
        return this._sad;
    }

    get pre(): string {
        return this._sad['i'];
    }

    get code(): string {
        return this._code;
    }

    get raw(): string {
        return this._raw;
    }

    get said(): string {
        return this._sad['d'];
    }

    get sner(): CesrNumber {
        return new CesrNumber({}, this.sad['s']);
    }

    get sn(): number {
        return this.sner.num;
    }

    get kind(): Serials {
        return this._kind;
    }

    /**
     * Serializes a self-addressing data dictionary from the dictionary passed in
     * using the specified serialization type.
     * @param sad self-addressing data dictionary.
     * @param kind serialization type to produce
     * @private
     */
    private _exhale(
        sad: Dict<any>,
        kind: Serials
    ): [string, Protocols, Serials, Dict<any>, Version] {
        return sizeify(sad, kind);
    }

    get proto(): Protocols {
        return this._proto;
    }

    get size(): number {
        return this._size;
    }

    get version(): Version {
        return this._version;
    }
    get verfers(): Verfer[] {
        let keys: any = [];
        if ('k' in this._sad) {
            // establishment event
            keys = this._sad['k'];
        } else {
            // non-establishment event
            keys = [];
        }
        // create a new Verfer for each key
        const verfers = [];
        for (const key of keys) {
            verfers.push(new Verfer({ qb64: key }));
        }
        return verfers;
    }

    get digers(): Diger[] {
        let keys: any = [];
        if ('n' in this._sad) {
            // establishment event
            keys = this._sad['n'];
        } else {
            // non-establishment event
            keys = [];
        }
        // create a new Verfer for each key
        const digers = [];
        for (const key of keys) {
            digers.push(new Diger({ qb64: key }));
        }
        return digers;
    }

    pretty() {
        return JSON.stringify(this._sad, undefined, 2);
    }
}

export function dumps(sad: Object, kind: Serials.JSON): string {
    if (kind == Serials.JSON) {
        return JSON.stringify(sad);
    } else {
        throw new Error('unsupported event encoding');
    }
}

export function sizeify(
    ked: Dict<any>,
    kind?: Serials
): [string, Protocols, Serials, Dict<any>, Version] {
    if (!('v' in ked)) {
        throw new Error('Missing or empty version string');
    }

    const [proto, knd, version] = deversify(ked['v'] as string);
    if (version != Vrsn_1_0) {
        throw new Error(`unsupported version ${version.toString()}`);
    }

    if (kind == undefined) {
        kind = knd;
    }

    let raw = dumps(ked, kind);
    const size = new TextEncoder().encode(raw).length;

    ked['v'] = versify(proto, version, kind, size);

    raw = dumps(ked, kind);

    return [raw, proto, kind, ked, version];
}
