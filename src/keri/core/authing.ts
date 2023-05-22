import {Signer} from "./signer";
import {Verfer} from "./verfer";
import {desiginput, normalize, siginput} from "./httping";
import {Signage, signature, designature} from "../end/ending";
import {Cigar} from "./cigar";
import {Siger} from "./siger";
import {b} from "./core";
export class Authenticater {

    static DefaultFields = [
        "@method",
        "@path",
        "signify-resource",
        "signify-timestamp",
    ]
    private _verfer: Verfer;
    private readonly _csig: Signer;

    constructor(csig: Signer, verfer: Verfer) {
        this._csig = csig
        this._verfer = verfer
    }

    verify(headers: Headers, method: string, path: string): boolean {
        let siginput = headers.get("Signature-Input")
        if (siginput == null) {
            return false
        }
        let signature = headers.get("Signature")
        if (signature == null) {
            return false
        }
        let inputs = desiginput(siginput)
        inputs = inputs.filter((input) => input.name == "signify")
        if (inputs.length == 0) {
            return false
        }
        inputs.forEach((input) => {
            let items = new Array<string>()
            input.fields!.forEach((field: string) => {
                if (field.startsWith("@")) {
                    if (field == "@method") {
                        items.push(`"${field}": ${method}`)
                    } else if (field == "@path") {
                        items.push(`"${field}": ${path}`)
                    }
                } else {
                    if (headers.has(field)) {
                        let value = normalize(headers.get(field) as string)
                        items.push(`"${field}": ${value}`)
                    }
                }
            })
            items.push(`signify-resource: ${input.keyid}`)
            let created = new Date(input.created * 1000).toISOString()
            items.push(`signify-timestamp: ${created}`)
            let values = new Array<string>()
            values.push(`(${input.fields!.join(" ")})`)
            values.push(`created=${input.created}`)
            if (input.expires != undefined) {
                values.push(`expires=${input.expires}`)
            }
            if (input.nonce != undefined) {
                values.push(`nonce=${input.nonce}`)
            }
            if (input.keyid != undefined) {
                values.push(`keyid=${input.keyid}`)
            }
            if (input.context != undefined) {
                values.push(`context=${input.context}`)
            }
            if (input.alg != undefined) {
                values.push(`alg=${input.alg}`)
            }
            let params = values.join(";")
            items.push(`"@signature-params: ${params}"`)
            let ser = b(items.join("\n"))
            let signage = designature(signature!)
            let cig = signage[0].markers.get(input.name)
            if (!this._verfer.verify(cig.raw, ser)) {
                throw new Error(`Signature for ${input.keyid} invalid.`)
            }
        })

        return true
    }

    sign(headers: Headers, method: string, path: string, fields?: Array<string>): Headers {
        if (fields == undefined) {
            fields = Authenticater.DefaultFields
        }

        let [header, sig] = siginput(this._csig, {
            name: "signify", method, path, headers, fields, alg: "ed25519",
            keyid: this._csig.verfer.qb64
        })

        header.forEach((value, key) => {
            headers.append(key, value)
        })

        let markers = new Map<string, Siger|Cigar>()
        markers.set("signify", sig)
        let signage = new Signage(markers, false)
        let signed = signature([signage])
        signed.forEach((value, key) => {
            headers.append(key, value)
        })

        return headers
    }


}