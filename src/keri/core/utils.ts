import { Counter, CtrDex } from './counter';
import { Seqner } from './seqner';
import { Prefixer } from './prefixer';
import { Saider } from './saider';
import { Serder } from './serder';
import { b } from './core';

export function pad(n: any, width = 3, z = 0) {
    return (String(z).repeat(width) + String(n)).slice(String(n).length);
}

/**
 * @description  Returns list of depth first recursively extracted values from elements of
    key event dict ked whose flabels are in lables list

 * @param {*} ked  ked is key event dict
 * @param {*} labels    labels is list of element labels in ked from which to extract values
 */
export function extractValues(ked: any, labels: any) {
    let values = [];
    for (let label of labels) {
        values = extractElementValues(ked[label], values);
    }

    return values;
}

export function arrayEquals(ar1: Uint8Array, ar2: Uint8Array) {
    return (
        ar1.length === ar2.length &&
        ar1.every((val, index) => val === ar2[index])
    );
}

/**
 * @description   Recusive depth first search that recursively extracts value(s) from element
    and appends to values list
    Assumes that extracted values are str

 * @param {*} element
 * @param {*} values
 */

function extractElementValues(element: any, values: any) {
    let data = [];

    try {
        if (element instanceof Array && !(typeof element == 'string')) {
            for (let k in element) extractElementValues(element[k], values);
        } else if (typeof element == 'string') {
            values.push(element);
        }
        data = values;
    } catch (error) {
        throw new Error(error as string);
    }

    return data;
}

/**
 * @description Returns True if obj is non-string iterable, False otherwise

 * @param {*} obj
 */

// function nonStringIterable(obj) {
//     obj instanceof (String)
//     return  instanceof(obj, (str, bytes)) && instanceof(obj, Iterable))
// }

export function nowUTC(): Date {
    return new Date();
}

export function range(start: number, stop: number, step: number) {
    if (typeof stop == 'undefined') {
        // one param defined
        stop = start;
        start = 0;
    }

    if (typeof step == 'undefined') {
        step = 1;
    }

    if ((step > 0 && start >= stop) || (step < 0 && start <= stop)) {
        return [];
    }

    let result = new Array<number>();
    for (let i: number = start; step > 0 ? i < stop : i > stop; i += step) {
        result.push(i);
    }

    return result;
}

export function intToBytes(value: number, length: number): Uint8Array {
    const byteArray = new Uint8Array(length); // Assuming a 4-byte integer (32 bits)

    for (let index = byteArray.length-1; index >= 0; index--) {
        let byte = value & 0xff;
        byteArray[index] = byte;
        value = (value - byte) / 256;
    }
    return byteArray;
}

export function bytesToInt(ar: Uint8Array): number {
    let value = 0;
    for (let i = 0; i <ar.length; i++) {
        value = value * 256 + ar[i];
    }
    return value;
}

export function serializeACDCAttachment(
    acdc: Serder,
    saider: Saider
): Uint8Array {
    let prefixer = new Prefixer({ raw: b(acdc.raw) });
    let seqner = new Seqner({ sn: acdc.sn });
    let craw = new Uint8Array();
    let ctr = new Counter({ code: CtrDex.SealSourceTriples, count: 1 }).qb64b;
    let prefix = prefixer.qb64b;
    let seq = seqner.qb64b;
    let said = saider.qb64b;
    let newCraw = new Uint8Array(
        craw.length + ctr.length + prefix.length + seq.length + said.length
    );
    newCraw.set(craw);
    newCraw.set(ctr, craw.length);
    newCraw.set(prefix, craw.length + ctr.length);
    newCraw.set(seq, craw.length + ctr.length + prefix.length);
    newCraw.set(said, craw.length + ctr.length + prefix.length + seq.length);
    return newCraw;
}

export function serializeIssExnAttachment(
    anc: Serder,
    ancSaider: Saider
): Uint8Array {
    let seqner = new Seqner({ sn: anc.sn });
    let coupleArray = new Uint8Array(
        seqner.qb64b.length + ancSaider.qb64b.length
    );
    coupleArray.set(seqner.qb64b);
    coupleArray.set(ancSaider.qb64b, seqner.qb64b.length);
    let counter = new Counter({
        code: CtrDex.SealSourceCouples,
        count: 1,
    });
    let counterQb64b = counter.qb64b;
    let atc = new Uint8Array(counter.qb64b.length + coupleArray.length);
    atc.set(counterQb64b);
    atc.set(coupleArray, counterQb64b.length);

    if (atc.length % 4 !== 0) {
        throw new Error(
            `Invalid attachments size: ${atc.length}, non-integral quadlets detected.`
        );
    }
    let pcnt = new Counter({
        code: CtrDex.AttachedMaterialQuadlets,
        count: Math.floor(atc.length / 4),
    });
    let msg = new Uint8Array(pcnt.qb64b.length + atc.length);
    msg.set(pcnt.qb64b);
    msg.set(atc, pcnt.qb64b.length);

    return msg;
}
