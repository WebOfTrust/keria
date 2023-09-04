import {BexDex, Matter, MatterArgs, MtrDex} from "./matter";
import {EmptyMaterialError} from "./kering";
import Base64 from "urlsafe-base64";

const B64REX = "^[A-Za-z0-9\\-_]*$"
export const Reb64 = new RegExp(B64REX)


/*

    Bexter is subclass of Matter, cryptographic material, for variable length
    strings that only contain Base64 URL safe characters, i.e. Base64 text (bext).
    When created using the 'bext' paramaeter, the encoded matter in qb64 format
    in the text domain is more compact than would be the case if the string were
    passed in as raw bytes. The text is used as is to form the value part of the
    qb64 version not including the leader.

    Due to ambiguity that arises from pre-padding bext whose length is a multiple of
    three with one or more 'A' chars. Any bext that starts with an 'A' and whose length
    is either a multiple of 3 or 4 may not round trip. Bext with a leading 'A'
    whose length is a multiple of four may have the leading 'A' stripped when
    round tripping.

        Bexter(bext='ABBB').bext == 'BBB'
        Bexter(bext='BBB').bext == 'BBB'
        Bexter(bext='ABBB').qb64 == '4AABABBB' == Bexter(bext='BBB').qb64

    To avoid this problem, only use for applications of base 64 strings that
    never start with 'A'

    Examples: base64 text strings:

    bext = ""
    qb64 = '4AAA'

    bext = "-"
    qb64 = '6AABAAA-'

    bext = "-A"
    qb64 = '5AABAA-A'

    bext = "-A-"
    qb64 = '4AABA-A-'

    bext = "-A-B"
    qb64 = '4AAB-A-B'


    Example uses:
        CESR encoded paths for nested SADs and SAIDs
        CESR encoded fractionally weighted threshold expressions


    Attributes:

    Inherited Properties:  (See Matter)
        .pad  is int number of pad chars given raw

        .code is  str derivation code to indicate cypher suite
        .raw is bytes crypto material only without code
        .index is int count of attached crypto material by context (receipts)
        .qb64 is str in Base64 fully qualified with derivation code + crypto mat
        .qb64b is bytes in Base64 fully qualified with derivation code + crypto mat
        .qb2  is bytes in binary with derivation code + crypto material
        .transferable is Boolean, True when transferable derivation code False otherwise

    Properties:
        .text is the Base64 text value, .qb64 with text code and leader removed.

    Hidden:
        ._pad is method to compute  .pad property
        ._code is str value for .code property
        ._raw is bytes value for .raw property
        ._index is int value for .index property
        ._infil is method to compute fully qualified Base64 from .raw and .code
        ._exfil is method to extract .code and .raw from fully qualified Base64

    Methods:




 */

export class Bexter extends Matter {
    constructor({raw, code = MtrDex.StrB64_L0, qb64b, qb64, qb2}: MatterArgs, bext?: string) {
        if (raw === undefined && qb64b === undefined && qb64 === undefined && qb2 === undefined) {
            if (bext === undefined)
                throw new EmptyMaterialError("Missing bext string.")

            let match = Reb64.exec(bext)
            if (!match)
                throw new Error("Invalid Base64.")

            raw = Bexter._rawify(bext)
        }

        super({raw, code, qb64b, qb64, qb2});

        if (!BexDex.has(this.code))
            throw new Error(`Invalid code = ${this.code} for Bexter.`)
    }

    static _rawify(bext: string): Uint8Array {
        let ts = bext.length % 4  // bext size mod 4
        let ws = (4 - ts) % 4  // pre conv wad size in chars
        let ls = (3 - ts) % 3  // post conv lead size in bytes
        let wad = new Array(ws)
        wad.fill('A')
        let base = wad.join('') + bext  // pre pad with wad of zeros in Base64 == 'A'
        let raw = Base64.decode(base) // [ls:]  // convert and remove leader

        return Uint8Array.from(raw).subarray(ls)  // raw binary equivalent of text

    }

    get bext(): string {
        let sizage = Matter.Sizes.get(this.code)
        let wad = Uint8Array.from(new Array(sizage?.ls).fill(0))
        let bext = Base64.encode(Buffer.from([...wad, ...this.raw]))

        let ws = 0
        if (sizage?.ls === 0 && bext !== undefined) {
            if (bext[0] === 'A') {
                ws = 1
            }
        } else {
            ws = (sizage?.ls! + 1) % 4
        }

        return bext.substring(ws)
    }
}