import { randomNonce } from '../app/coring.ts';
import { TraitDex } from '../app/habery.ts';
import {
    Serials,
    Vrsn_1_0,
    Version,
    Protocols,
    versify,
    Ilks,
} from '../core/core.ts';
import { ample } from './eventing.ts';
import { MtrDex } from './matter.ts';
import { Prefixer } from './prefixer.ts';
import { Serder } from './serder.ts';

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
        version = Vrsn_1_0,
        kind = Serials.JSON,
        code = MtrDex.Blake3_256,
    }: VDRInceptArgs): Serder {
        const vs = versify(Protocols.KERI, version, kind, 0);
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

        const sad = {
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

        const prefixer = new Prefixer({ code }, sad);
        sad.i = prefixer.qb64;
        sad.d = prefixer.qb64;

        return new Serder(sad);
    }
}

export { vdr };
