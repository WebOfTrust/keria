import libsodium from "libsodium-wrappers-sumo";
import { Salter } from "../core/salter";
import { Matter, MtrDex } from '../core/matter';


export function randomPasscode(): string {
    let raw = libsodium.randombytes_buf(16);
    let salter = new Salter({ raw: raw })

    return salter.qb64.substring(2)
}

export function randomNonce(): string {
    let seed = libsodium.randombytes_buf(libsodium.crypto_sign_SEEDBYTES);
    let seedqb64 = new Matter({ raw: seed, code: MtrDex.Ed25519_Seed });
    return seedqb64.qb64;
}
