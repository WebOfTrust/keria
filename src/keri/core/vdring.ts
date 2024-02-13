import { randomNonce } from '../app/coring';
import { TraitDex } from '../app/habery';
import {
    Serials,
    Versionage,
    Version,
    Ident,
    versify,
    Ilks,
} from '../core/core';
import { ample } from './eventing';
import { MtrDex } from './matter';
import { Prefixer } from './prefixer';
import { Serder } from './serder';

namespace vdr {
    export interface VDRInceptArgs {
        pre: string;
        toad?: number | string;
        nonce?: string;
        baks?: string[];
        cnfg?: string[];
        version?: Version;
        kind?: Serials;
        code?: string;
    }

    export function incept({
        pre,
        toad,
        nonce = randomNonce(),
        baks = [],
        cnfg = [],
        version = Versionage,
        kind = Serials.JSON,
        code = MtrDex.Blake3_256,
    }: VDRInceptArgs): Serder {
        const vs = versify(Ident.KERI, version, kind, 0);
        const isn = 0;
        const ilk = Ilks.vcp;

        if (cnfg.includes(TraitDex.NoBackers) && baks.length > 0) {
            throw new Error(
                `${baks.length} backers specified for NB vcp, 0 allowed`
            );
        }

        if (new Set(baks).size < baks.length) {
            throw new Error(`Invalid baks ${baks} has duplicates`);
        }

        let _toad: number;
        if (toad === undefined) {
            if (baks.length === 0) {
                _toad = 0;
            } else {
                _toad = ample(baks.length);
            }
        } else {
            _toad = +toad;
        }

        if (baks.length > 0) {
            if (_toad < 1 || _toad > baks.length) {
                throw new Error(`Invalid toad ${_toad} for baks in ${baks}`);
            }
        } else {
            if (_toad != 0) {
                throw new Error(`Invalid toad ${_toad} for no baks`);
            }
        }

        const ked = {
            v: vs,
            t: ilk,
            d: '',
            i: '',
            ii: pre,
            s: '' + isn,
            c: cnfg,
            bt: _toad.toString(16),
            b: baks,
            n: nonce,
        };

        const prefixer = new Prefixer({ code }, ked);
        ked.i = prefixer.qb64;
        ked.d = prefixer.qb64;

        return new Serder(ked);
    }
}

export { vdr };
