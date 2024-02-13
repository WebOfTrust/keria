import { Siger } from '../core/siger';
import { Cigar } from '../core/cigar';

export const FALSY = [false, 0, '?0', 'no', 'false', 'False', 'off'];
export const TRUTHY = [true, 1, '?1', 'yes', 'true', 'True', 'on'];

export class Signage {
    constructor(
        markers: any,
        indexed?: boolean,
        signer?: string,
        ordinal?: string,
        digest?: string,
        kind?: string
    ) {
        this.markers = markers;
        this.indexed = indexed;
        this.signer = signer;
        this.ordinal = ordinal;
        this.digest = digest;
        this.kind = kind;
    }
    public markers: any;
    public indexed: boolean | undefined = false;
    public signer: string | undefined;
    public ordinal: string | undefined;
    public digest: string | undefined;
    public kind: string | undefined;
}

export function signature(signages: Array<Signage>): Headers {
    const values = new Array<string>();

    for (const signage of signages) {
        let markers: Array<Siger | Cigar>;
        let indexed = signage.indexed;
        const signer = signage.signer;
        const ordinal = signage.ordinal;
        const digest = signage.digest;
        const kind = signage.kind;
        let tags: Array<string>;

        if (signage.markers instanceof Map) {
            tags = Array.from(signage.markers.keys());
            markers = Array.from(signage.markers.values());
        } else {
            markers = signage.markers as Array<Siger | Cigar>;
            tags = new Array<string>();
        }

        if (indexed == undefined) {
            indexed = markers[0] instanceof Siger;
        }

        const items = new Array<string>();
        const tag = 'indexed';

        let val = indexed ? '?1' : '?0';
        items.push(`${tag}="${val}"`);

        if (signer != undefined) {
            items.push(`signer="${signer}"`);
        }
        if (ordinal != undefined) {
            items.push(`ordinal="${ordinal}"`);
        }
        if (digest != undefined) {
            items.push(`digest="${digest}"`);
        }
        if (kind != undefined) {
            items.push(`kind="${kind}"`);
        }

        markers.forEach((marker, idx) => {
            let tag: string;
            if (tags != undefined && tags.length > idx) {
                tag = tags[idx];
            } else if (marker instanceof Siger) {
                if (!indexed)
                    throw new Error(
                        `Indexed signature marker ${marker} when indexed False.`
                    );

                tag = marker.index.toString();
            } else {
                // Must be a Cigar
                if (indexed)
                    throw new Error(
                        `Unindexed signature marker ${marker} when indexed True.`
                    );
                tag = marker.verfer!.qb64;
            }

            val = marker.qb64;
            items.push(`${tag}="${val}"`);
        });

        values.push(items.join(';'));
    }

    return new Headers([['Signature', values.join(',')]]);
}

export function designature(value: string) {
    const values = value.replace(' ', '').split(',');

    const signages = new Array<Signage>();
    values.forEach((val) => {
        const dict = new Map<string, string>();
        val.split(';').forEach((v) => {
            const splits = v.split('=', 2);
            dict.set(splits[0], splits[1].replaceAll('"', ''));
        });

        if (!dict.has('indexed')) {
            throw new Error(
                'Missing indexed field in Signature header signage.'
            );
        }
        const item = dict.get('indexed')!;
        const indexed = !FALSY.includes(item);
        dict.delete('indexed');

        let signer;
        if (dict.has('signer')) {
            signer = dict.get('signer') as string;
            dict.delete('signer');
        }

        let ordinal;
        if (dict.has('ordinal')) {
            ordinal = dict.get('ordinal') as string;
            dict.delete('ordinal');
        }

        let digest;
        if (dict.has('digest')) {
            digest = dict.get('digest') as string;
            dict.delete('digest');
        }

        let kind;
        if (dict.has('kind')) {
            kind = dict.get('kind') as string;
            dict.delete('kind');
        } else {
            kind = 'CESR';
        }

        let markers: Map<string, string | Siger | Cigar>;
        if (kind == 'CESR') {
            markers = new Map<string, Siger | Cigar>();
            dict.forEach((val, key) => {
                if (indexed) {
                    markers.set(key, new Siger({ qb64: val as string }));
                } else {
                    markers.set(key, new Cigar({ qb64: val as string }));
                }
            });
        } else {
            markers = dict;
        }

        signages.push(
            new Signage(markers, indexed, signer, ordinal, digest, kind)
        );
    });

    return signages;
}
