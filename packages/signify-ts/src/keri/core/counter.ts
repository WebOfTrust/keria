import { Codex, Sizage } from './matter.ts';
import { b, b64ToInt, d, intToB64 } from './core.ts';

export interface CounterArgs {
    code?: string;
    count?: number;
    countB64?: string;
    qb64b?: Uint8Array;
    qb64?: string;
    qb2?: Uint8Array;
    strip?: boolean;
}

export class CounterCodex extends Codex {
    public ControllerIdxSigs: string = '-A'; // Qualified Base64 Indexed Signature.
    public WitnessIdxSigs: string = '-B'; // Qualified Base64 Indexed Signature.
    public NonTransReceiptCouples: string = '-C'; // Composed Base64 Couple, pre+cig.
    public TransReceiptQuadruples: string = '-D'; // Composed Base64 Quadruple, pre+snu+dig+sig.
    public FirstSeenReplayCouples: string = '-E'; // Composed Base64 Couple, fnu+dts.
    public TransIdxSigGroups: string = '-F'; // Composed Base64 Group, pre+snu+dig+ControllerIdxSigs group.
    public SealSourceCouples: string = '-G'; // Composed Base64 couple, snu+dig of given delegators or issuers event
    public TransLastIdxSigGroups: string = '-H'; // Composed Base64 Group, pre+ControllerIdxSigs group.
    public SealSourceTriples: string = '-I'; // Composed Base64 triple, pre+snu+dig of anchoring source event
    public SadPathSig: string = '-J'; // Composed Base64 Group path+TransIdxSigGroup of SAID of content
    public SadPathSigGroup: string = '-K'; // Composed Base64 Group, root(path)+SaidPathCouples
    public PathedMaterialQuadlets: string = '-L'; // Composed Grouped Pathed Material Quadlet (4 char each)
    public AttachedMaterialQuadlets: string = '-V'; // Composed Grouped Attached Material Quadlet (4 char each)
    public BigAttachedMaterialQuadlets: string = '-0V'; // Composed Grouped Attached Material Quadlet (4 char each)
    public KERIProtocolStack: string = '--AAA'; // KERI ACDC Protocol Stack CESR Version
}

export const CtrDex = new CounterCodex();

export class Counter {
    static Sizes = new Map(
        Object.entries({
            '-A': new Sizage(2, 2, 4, 0),
            '-B': new Sizage(2, 2, 4, 0),
            '-C': new Sizage(2, 2, 4, 0),
            '-D': new Sizage(2, 2, 4, 0),
            '-E': new Sizage(2, 2, 4, 0),
            '-F': new Sizage(2, 2, 4, 0),
            '-G': new Sizage(2, 2, 4, 0),
            '-H': new Sizage(2, 2, 4, 0),
            '-I': new Sizage(2, 2, 4, 0),
            '-J': new Sizage(2, 2, 4, 0),
            '-K': new Sizage(2, 2, 4, 0),
            '-L': new Sizage(2, 2, 4, 0),
            '-V': new Sizage(2, 2, 4, 0),
            '-0V': new Sizage(3, 5, 8, 0),
            '--AAA': new Sizage(5, 3, 8, 0),
        })
    );

    static Hards = new Map<string, number>([
        ['-A', 2],
        ['-B', 2],
        ['-C', 2],
        ['-D', 2],
        ['-E', 2],
        ['-F', 2],
        ['-G', 2],
        ['-H', 2],
        ['-I', 2],
        ['-J', 2],
        ['-K', 2],
        ['-L', 2],
        ['-M', 2],
        ['-N', 2],
        ['-O', 2],
        ['-P', 2],
        ['-Q', 2],
        ['-R', 2],
        ['-S', 2],
        ['-T', 2],
        ['-U', 2],
        ['-V', 2],
        ['-W', 2],
        ['-X', 2],
        ['-Y', 2],
        ['-Z', 2],
        ['-a', 2],
        ['-b', 2],
        ['-c', 2],
        ['-d', 2],
        ['-e', 2],
        ['-f', 2],
        ['-g', 2],
        ['-h', 2],
        ['-i', 2],
        ['-j', 2],
        ['-k', 2],
        ['-l', 2],
        ['-m', 2],
        ['-n', 2],
        ['-o', 2],
        ['-p', 2],
        ['-q', 2],
        ['-r', 2],
        ['-s', 2],
        ['-t', 2],
        ['-u', 2],
        ['-v', 2],
        ['-w', 2],
        ['-x', 2],
        ['-y', 2],
        ['-z', 2],
        ['-0', 3],
        ['--', 5],
    ]);

    private _code: string = '';
    private _count: number = -1;

    constructor({ code, count, countB64, qb64b, qb64, qb2 }: CounterArgs) {
        if (code != undefined) {
            if (!Counter.Sizes.has(code)) {
                throw new Error(`"Unsupported code=${code}.`);
            }

            const sizage = Counter.Sizes.get(code)!;
            const cs = sizage.hs + sizage.ss;
            if (sizage.fs != cs || cs % 4 != 0) {
                throw new Error(
                    `Whole code size not full size or not multiple of 4. cs=${cs} fs=${sizage.fs}.`
                );
            }

            if (count == undefined) {
                count = countB64 == undefined ? 1 : b64ToInt(countB64);
            }

            if (count < 0 || count > 64 ** sizage.ss - 1) {
                throw new Error(`Invalid count=${count} for code=${code}.`);
            }

            this._code = code;
            this._count = count;
        } else if (qb64b != undefined) {
            const qb64 = d(qb64b);
            this._exfil(qb64);
        } else if (qb64 != undefined) {
            this._exfil(qb64);
        } else if (qb2 != undefined) {
        } else {
            throw new Error(
                `Improper initialization need either (code and count) or qb64b or qb64 or qb2.`
            );
        }
    }

    get code(): string {
        return this._code;
    }

    get count() {
        return this._count;
    }

    get qb64() {
        return this._infil();
    }

    get qb64b() {
        return b(this.qb64);
    }

    countToB64(l?: number): string {
        if (l == undefined) {
            const sizage = Counter.Sizes.get(this.code)!;
            l = sizage.ss;
        }
        return intToB64(this.count, l);
    }

    static semVerToB64(
        version: string = '',
        major: number = 0,
        minor: number = 0,
        patch: number = 0
    ): string {
        let parts = [major, minor, patch];
        if (version != '') {
            const ssplits = version.split('.');
            const splits = ssplits.map((x) => {
                if (x == '') return 0;
                return parseInt(x);
            });

            const off = splits.length;
            const x = 3 - off;
            for (let i = 0; i < x; i++) {
                splits.push(parts[i + off]);
            }
            parts = splits;
        }

        parts.forEach((p) => {
            if (p < 0 || p > 63) {
                throw new Error(
                    `Out of bounds semantic version. Part=${p} is < 0 or > 63.`
                );
            }
        });

        return parts
            .map((p) => {
                return intToB64(p, 1);
            })
            .join('');
    }

    private _infil(): string {
        const code = this.code;
        const count = this.count;

        const sizage = Counter.Sizes.get(code)!;
        const cs = sizage.hs + sizage.ss;
        if (sizage.fs != cs || cs % 4 != 0) {
            throw new Error(
                `Whole code size not full size or not multiple of 4. cs=${cs} fs=${sizage.fs}.`
            );
        }

        if (count < 0 || count > 64 ** sizage.ss - 1) {
            throw new Error(`Invalid count=${count} for code=${code}.`);
        }

        const both = `${code}${intToB64(count, sizage.ss)}`;

        if (both.length % 4) {
            throw new Error(
                `Invalid size = ${both.length} of ${both} not a multiple of 4.`
            );
        }

        return both;
    }

    private _exfil(qb64: string) {
        if (qb64.length == 0) {
            throw new Error('Empty Material');
        }

        const first = qb64.slice(0, 2);
        if (!Counter.Hards.has(first)) {
            throw new Error(`Unexpected code ${first}`);
        }

        const hs = Counter.Hards.get(first)!;
        if (qb64.length < hs) {
            throw new Error(`Need ${hs - qb64.length} more characters.`);
        }

        const hard = qb64.slice(0, hs);
        if (!Counter.Sizes.has(hard)) {
            throw new Error(`Unsupported code ${hard}`);
        }

        const sizage = Counter.Sizes.get(hard)!;
        const cs = sizage!.hs + sizage!.ss;

        if (qb64.length < cs) {
            throw new Error(`Need ${cs - qb64.length} more chars.`);
        }

        const scount = qb64.slice(sizage.hs, sizage.hs + sizage.ss);
        const count = b64ToInt(scount);

        this._code = hard;
        this._count = count;
    }
}
