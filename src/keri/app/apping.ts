import libsodium from "libsodium-wrappers-sumo";
import {Salter} from "../core/salter";


export function randomPasscode(): string {
    let raw = libsodium.randombytes_buf(16);
    let salter = new Salter({raw: raw})

    return salter.qb64.substring(2)
}


