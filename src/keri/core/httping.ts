import {serializeDictionary, Dictionary, parseDictionary, Item, Parameters} from "structured-headers";
import {Signer} from "./signer";
import {b} from "./core";
import {Cigar} from "./cigar";
import {nowUTC} from "./utils";
import {Siger} from "./siger";
const Base64 = require('urlsafe-base64');

export function normalize(header: string) {
    return header.trim()
}

export interface SiginputArgs {
    name: string,
    method:string,
    path:string,
    headers: Headers,
    fields: Array<string>,
    expires?:number,
    nonce?: string,
    alg?: string,
    keyid?: string,
    context?: string
}

export function siginput(signer: Signer,
                         {name, method, path, headers, fields,
                             expires, nonce, alg, keyid, context}: SiginputArgs): [Map<string, string>, Siger|Cigar] {

    let items = new Array<string>()
    let ifields = new Array<[string, Map<string, string>]>()

    fields.forEach((field) => {
        if  (field.startsWith("@")) {
            switch (field) {
                case "@method":
                    items.push(`"${field}": ${method}`)
                    ifields.push([field, new Map()])
                    break
                case "@path":
                    items.push(`"${field}": ${path}`)
                    ifields.push([field, new Map()])
                    break
            }
        } else {
            if (!headers.has(field))
                return

            ifields.push([field, new Map()])
            let value = normalize(headers.get(field)!)
            items.push(`"${field}": ${value}`)
        }
    })

    let nameParams = new Map<string, string|number>()
    let now = Math.floor(nowUTC().getTime() / 1000)
    nameParams.set("created", now)

    let values = [`(${ifields.join(" ")})`, `created=${now}`]
    if (expires != undefined) {
        values.push(`expires=${expires}`)
        nameParams.set('expires', expires)
    }
    if (nonce != undefined) {
        values.push(`nonce=${nonce}`)
        nameParams.set('nonce', nonce)
    }
    if (keyid != undefined) {
        values.push(`keyid=${keyid}`)
        nameParams.set('keyid', keyid)
    }
    if (context != undefined) {
        values.push(`context=${context}`)
        nameParams.set('context', context)
    }
    if (alg != undefined) {
        values.push(`alg=${alg}`)
        nameParams.set('alg', alg)
    }
    let sid = new Map([
        [name, [ifields, nameParams]]
    ])

    let params = values.join(";")
    items.push(`"@signature-params: ${params}"`)

    let ser = items.join("\n")
    let sig = signer.sign(b(ser))

    return [new Map<string, string>([['Signature-Input', `${serializeDictionary(sid as Dictionary)}`]]), sig]
}

export class Unqualified {
    private readonly _raw: Uint8Array

    constructor(raw: Uint8Array) {
        this._raw = raw
    }

    get qb64(): string {
        return Base64.encode(Buffer.from(this._raw))
    }

    get qb64b(): Uint8Array {
        return b(this.qb64)
    }
}

export class Inputage {
    public name: any
    public fields: any
    public created: any
    public expires: any
    public nonce: any
    public alg: any
    public keyid: any
    public context: any
}

export function desiginput(value: string): Array<Inputage> {
    let sid = parseDictionary(value)
    let siginputs = new Array<Inputage>()

    sid.forEach((value, key) => {
        let siginput = new Inputage()
        siginput.name = key
        let list: Item[]
        let params
        [list, params] = value as [Item[], Parameters]
        siginput.fields = list.map((item) => item[0])

        if (!params.has("created")) {
            throw new Error("missing required `created` field from signature input")
        }
        siginput.created = params.get("created")
        
        if (params.has("expires")) {
            siginput.expires = params.get("expires")
        }
        
        if (params.has("nonce")) {
            siginput.nonce = params.get("nonce")
        }
        
        if (params.has("alg")) {
            siginput.alg = params.get("alg")
        }
        
        if (params.has("keyid")) {
            siginput.keyid = params.get("keyid")
        }
        
        if (params.has("context")) {
            siginput.context = params.get("context")
        }
        
        siginputs.push(siginput)
    })

    return siginputs

}