
import {Bexter, Reb64} from "./bexter";
import {MatterArgs, MtrDex} from "./matter";
import {EmptyMaterialError} from "./kering";

/*
    Pather is a subclass of Bexter that provides SAD Path language specific functionality
    for variable length strings that only contain Base64 URL safe characters.  Pather allows
    the specification of SAD Paths as a list of field components which will be converted to the
    Base64 URL safe character representation.

    Additionally, Pather provides .rawify for extracting and serializing the content targeted by
    .path for a SAD, represented as an instance of Serder.  Pather enforces Base64 URL character
    safety by leveraging the fact that SADs must have static field ordering.  Any field label can
    be replaced by its field ordinal to allow for path specification and traversal for any field
    labels that contain non-Base64 URL safe characters.


    Examples: strings:
        path = []
        text = "-"
        qb64 = '6AABAAA-'

        path = ["A"]
        text = "-A"
        qb64 = '5AABAA-A'

        path = ["A", "B"]
        text = "-A-B"
        qb64 = '4AAB-A-B'

        path = ["A", 1, "B", 3]
        text = "-A-1-B-3"
        qb64 = '4AAC-A-1-B-3'

 */

export class Pather extends Bexter {
    constructor({raw, code = MtrDex.StrB64_L0, qb64b, qb64, qb2}: MatterArgs, bext?: string, path?: string[]) {
        if (raw === undefined && bext === undefined && qb64b === undefined && qb64 === undefined && qb2 === undefined) {
            if (path === undefined)
                throw new EmptyMaterialError("Missing bext string.")

            bext = Pather._bextify(path)
        }

        super({raw, code, qb64b, qb64, qb2}, bext);

    }

    // TODO: implement SAD access methods like resolve, root, strip, startswith and tail

    get path(): string[] {
        if (!this.bext.startsWith("-")) {
            throw new Error("invalid SAD ptr")
        }

        let path = this.bext
        while(path.charAt(0) === '-')
        {
            path = path.substring(1);
        }

        let apath = path.split("-")
        if (apath[0] !== '') {
            return apath
        } else {
            return []
        }
    }

    static _bextify(path: any[]): string {
        let vath = []
        for (const p of path) {
            let sp = ""
            if (typeof(p) === "number") {
                sp = p.toString()
            } else {
                sp = p
            }

            let match = Reb64.exec(sp)
            if (!match) {
                throw new Error(`"Non Base64 path component = ${p}.`)
            }

            vath.push(sp)
        }
        return "-" + vath.join("-")
    }
}