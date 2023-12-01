import { Signer } from './signer';
import { Verfer } from './verfer';
import { desiginput, normalize, siginput } from './httping';
import { Signage, signature, designature } from '../end/ending';
import { Cigar } from './cigar';
import { Siger } from './siger';
export class Authenticater {
    static DefaultFields = [
        '@method',
        '@path',
        'signify-resource',
        'signify-timestamp',
    ];
    private _verfer: Verfer;
    private readonly _csig: Signer;

    constructor(csig: Signer, verfer: Verfer) {
        this._csig = csig;
        this._verfer = verfer;
    }

    verify(headers: Headers, method: string, path: string): boolean {
        const siginput = headers.get('Signature-Input');
        if (siginput == null) {
            return false;
        }
        const signature = headers.get('Signature');
        if (signature == null) {
            return false;
        }
        let inputs = desiginput(siginput);
        inputs = inputs.filter((input) => input.name == 'signify');
        if (inputs.length == 0) {
            return false;
        }
        inputs.forEach((input) => {
            const items = new Array<string>();
            input.fields!.forEach((field: string) => {
                if (field.startsWith('@')) {
                    if (field == '@method') {
                        items.push(`"${field}": ${method}`);
                    } else if (field == '@path') {
                        items.push(`"${field}": ${path}`);
                    }
                } else {
                    if (headers.has(field)) {
                        const value = normalize(headers.get(field) as string);
                        items.push(`"${field}": ${value}`);
                    }
                }
            });
            const values = new Array<string>();
            values.push(`(${input.fields!.join(' ')})`);
            values.push(`created=${input.created}`);
            if (input.expires != undefined) {
                values.push(`expires=${input.expires}`);
            }
            if (input.nonce != undefined) {
                values.push(`nonce=${input.nonce}`);
            }
            if (input.keyid != undefined) {
                values.push(`keyid=${input.keyid}`);
            }
            if (input.context != undefined) {
                values.push(`context=${input.context}`);
            }
            if (input.alg != undefined) {
                values.push(`alg=${input.alg}`);
            }
            const params = values.join(';');
            items.push(`"@signature-params: ${params}"`);
            const ser = items.join('\n');
            const signage = designature(signature!);
            const cig = signage[0].markers.get(input.name);
            if (!this._verfer.verify(cig.raw, ser)) {
                throw new Error(`Signature for ${input.keyid} invalid.`);
            }
        });

        return true;
    }

    sign(
        headers: Headers,
        method: string,
        path: string,
        fields?: Array<string>
    ): Headers {
        if (fields == undefined) {
            fields = Authenticater.DefaultFields;
        }

        const [header, sig] = siginput(this._csig, {
            name: 'signify',
            method,
            path,
            headers,
            fields,
            alg: 'ed25519',
            keyid: this._csig.verfer.qb64,
        });

        header.forEach((value, key) => {
            headers.append(key, value);
        });

        const markers = new Map<string, Siger | Cigar>();
        markers.set('signify', sig);
        const signage = new Signage(markers, false);
        const signed = signature([signage]);
        signed.forEach((value, key) => {
            headers.append(key, value);
        });

        return headers;
    }
}
