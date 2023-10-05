import { BexDex, Matter, NumDex } from './matter';
import { CesrNumber } from './number';
import { Fraction } from 'mathjs';
import { math } from '../../index';

export class Tholder {
    private _weighted: boolean = false;
    private _thold: any = undefined;
    private _size: number = 0;
    private _number: CesrNumber | undefined = undefined;
    private _satisfy: any = undefined;

    // private _bexter: any

    constructor(kargs: { thold?: any; limen?: any; sith?: any }) {
        if (kargs.thold !== undefined) {
            this._processThold(kargs.thold);
        } else if (kargs.limen != undefined) {
            this._processLimen(kargs.limen);
        } else if (kargs.sith !== undefined) {
            this._processSith(kargs.sith);
        } else {
            throw new Error('Missing threshold expression');
        }
    }

    get weighted(): boolean {
        return this._weighted;
    }

    get thold(): any {
        return this._thold;
    }

    get size(): number {
        return this._size;
    }

    get limen(): any {
        return this._number?.qb64b;
    }

    get sith(): string {
        if (this.weighted) {
            let sith = this.thold.map((clause: Fraction[]) => {
                return clause.map((c) => {
                    if (0 < Number(c) && Number(c) < 1) {
                        return math.format(c, { fraction: 'ratio' });
                    } else {
                        return math.format(c, { fraction: 'decimal' });
                    }
                });
            });
            if (sith.length == 1) {
                sith = sith[0];
            }

            return sith;
        } else {
            return this.thold.toString(16);
        }
    }

    get json(): string {
        return JSON.stringify(this.sith);
    }

    get num(): number | undefined {
        return this._weighted ? undefined : this._thold;
    }

    private _processThold(thold: number | Array<Array<Fraction>>) {
        if (typeof thold === 'number') {
            this._processUnweighted(thold);
        } else {
            this._processWeighted(thold);
        }
    }

    private _processLimen(limen: string) {
        let matter = new Matter({ qb64: limen });
        if (NumDex.has(matter.code)) {
            let number = new CesrNumber({ raw: matter.raw, code: matter.code });
            this._processUnweighted(number.num);
        } else if (BexDex.has(matter.code)) {
            // TODO: Implement Bexter
        } else {
            throw new Error('Invalid code for limen=' + matter.code);
        }
    }

    private _processSith(sith: string | number | Array<string>) {
        if (typeof sith == 'number') {
            this._processUnweighted(sith);
        } else if (typeof sith == 'string' && sith.indexOf('[') == -1) {
            this._processUnweighted(parseInt(sith, 16));
        } else {
            let _sith: any = sith;
            if (typeof sith == 'string') {
                _sith = JSON.parse(sith);
            }

            if (_sith.length == 0) {
                throw new Error('Empty weight list');
            }

            let mask = _sith.map((x: any) => {
                return typeof x !== 'string';
            });

            if (mask.length > 0 && !mask.every((x: boolean) => x)) {
                _sith = [_sith];
            }

            for (let c of _sith) {
                let mask = c.map((x: any) => {
                    return typeof x === 'string';
                });
                if (mask.length > 0 && !mask.every((x: boolean) => x)) {
                    throw new Error(
                        'Invalid sith, some weights in clause ' +
                            mask +
                            ' are non string'
                    );
                }
            }

            let thold = this._processClauses(_sith);
            this._processWeighted(thold);
        }
    }

    private _processClauses(sith: Array<Array<string>>): Fraction[][] {
        let thold = new Array<Array<Fraction>>();
        sith.forEach((clause) => {
            thold.push(
                clause.map((w) => {
                    return this.weight(w);
                })
            );
        });
        return thold;
    }

    private _processUnweighted(thold: number) {
        if (thold < 0) {
            throw new Error('Non-positive int threshold = {thold}.');
        }
        this._thold = thold;
        this._weighted = false;
        this._size = this._thold; // used to verify that keys list size is at least size
        this._satisfy = this._satisfy_numeric;
        this._number = new CesrNumber({}, thold);
        // this._bexter = undefined
    }

    private _processWeighted(thold: Array<Array<Fraction>>) {
        for (let clause of thold) {
            if (Number(math.sum(clause)) < 1) {
                throw new Error(
                    'Invalid sith clause: ' +
                        thold +
                        'all clause weight sums must be >= 1'
                );
            }
        }

        this._thold = thold;
        this._weighted = true;
        this._size = thold.reduce((acc, currentValue) => {
            return acc + currentValue.length;
        }, 0);
        this._satisfy = this._satisfy_weighted;
        //TODO: created Bexter if needed
    }

    private weight(w: string): Fraction {
        return math.fraction(w);
    }

    private _satisfy_numeric(indices: any[]) {
        return this.thold > 0 && indices.length >= this.thold; // at least one
    }

    private _satisfy_weighted(indices: any) {
        if (indices.length === 0) {
            return false;
        }

        let indexes: Set<number> = new Set(indices.sort());
        let sats = new Array(indices.length).fill(false);
        for (let idx of indexes) {
            sats[idx] = true;
        }
        let wio = 0;
        for (let clause of this.thold) {
            let cw = 0;
            for (let w of clause) {
                if (sats[wio]) {
                    cw += Number(w);
                }
                wio += 1;
            }
            if (cw < 1) {
                return false;
            }
        }

        return true;
    }

    public satisfy(indices: any): boolean {
        return this._satisfy(indices);
    }
}
