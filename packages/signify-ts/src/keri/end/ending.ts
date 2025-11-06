import { Siger } from '../core/siger.ts';
import { Cigar } from '../core/cigar.ts';

export const FALSY = [false, 0, '?0', 'no', 'false', 'False', 'off'];
export const TRUTHY = [true, 1, '?1', 'yes', 'true', 'True', 'on'];

export class Signage {
    constructor(
        public readonly markers:
            | (Siger | Cigar)[]
            | Map<string, string | Siger | Cigar>,
        public readonly indexed?: boolean,
        public readonly signer?: string,
        public readonly ordinal?: string,
        public readonly digest?: string,
        public readonly kind?: string
    ) {}
}

export function signature(signages: Signage[]): Headers {
    const values: string[] = [];

    for (const signage of signages) {
        let markers: Array<string | Siger | Cigar>;
        let tags: string[];

        if (signage.markers instanceof Map) {
            markers = Array.from(signage.markers.values());
            tags = Array.from(signage.markers.keys());
        } else {
            markers = signage.markers as Array<Siger | Cigar>;
            tags = [];
        }

        const items = new Array<string>();
        const indexed = signage.indexed ?? markers[0] instanceof Siger;

        if (indexed) {
            items.push('indexed="?1"');
        } else {
            items.push('indexed="?0"');
        }

        if (signage.signer != undefined) {
            items.push(`signer="${signage.signer}"`);
        }
        if (signage.ordinal != undefined) {
            items.push(`ordinal="${signage.ordinal}"`);
        }
        if (signage.digest != undefined) {
            items.push(`digest="${signage.digest}"`);
        }
        if (signage.kind != undefined) {
            items.push(`kind="${signage.kind}"`);
        }

        items.push(
            ...markers.map((marker, idx) => {
                let tag: string | undefined = undefined;
                let val: string;

                if (tags != undefined && tags.length > idx) {
                    tag = tags[idx];
                }

                if (marker instanceof Siger) {
                    if (!indexed) {
                        throw new Error(
                            `Indexed signature marker ${marker} when indexed False.`
                        );
                    }

                    tag = tag ?? marker.index.toString();
                    val = marker.qb64;
                } else if (marker instanceof Cigar) {
                    if (indexed) {
                        throw new Error(
                            `Unindexed signature marker ${marker} when indexed True.`
                        );
                    }
                    if (!marker.verfer) {
                        throw new Error(
                            `Indexed signature marker is missing verfer`
                        );
                    }

                    tag = tag ?? marker.verfer.qb64;
                    val = marker.qb64;
                } else {
                    tag = tag ?? idx.toString();
                    val = marker;
                }

                return `${tag}="${val}"`;
            })
        );

        values.push(items.join(';'));
    }

    return new Headers([['Signature', values.join(',')]]);
}

export function designature(value: string) {
    const values = value.replace(' ', '').split(',');

    const signages = values.map((val) => {
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

        if (kind == 'CESR') {
            const markers = new Map<string, Siger | Cigar>();

            for (const [key, val] of dict.entries()) {
                if (indexed) {
                    markers.set(key, new Siger({ qb64: val }));
                } else {
                    markers.set(key, new Cigar({ qb64: val }));
                }
            }

            return new Signage(markers, indexed, signer, ordinal, digest, kind);
        } else {
            return new Signage(dict, indexed, signer, ordinal, digest, kind);
        }
    });

    return signages;
}
