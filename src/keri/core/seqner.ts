

import {Matter, MatterArgs, MtrDex} from './matter';
import { intToBytes, bytesToInt  } from './utils';
/**
 * @description  Seqner: subclass of Matter, cryptographic material, for ordinal numbers
 * such as sequence numbers or first seen ordering numbers.
 * Seqner provides fully qualified format for ordinals (sequence numbers etc)
 * when provided as attached cryptographic material elements.
 */
export class Seqner extends Matter {
    constructor({raw, code=MtrDex.Salt_128, qb64, qb64b, qb2, sn, snh, ...kwa}: MatterArgs & {sn?: number, snh?: string}) {
        if (!raw && !qb64b && !qb64 && !qb2) {
            if (sn === undefined) {
                if (snh === undefined) {
                    sn = 0;
                } else {
                    sn = parseInt(snh, 16);
                }
            }

            raw = intToBytes(sn,Matter._rawSize(MtrDex.Salt_128))
        }

        super({raw, code, qb64, qb64b, qb2, ...kwa});

        if (this.code !== MtrDex.Salt_128) {
            throw new Error(`Invalid code = ${this.code} for Seqner.`);
        }
    }

    get sn(): number {
        return bytesToInt(Buffer.from(this.raw))//To check if other readUInt64 is needed
    }

    get snh(): string {
        return this.sn.toString(16);
    }
}
