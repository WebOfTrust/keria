import { Algos } from './manager';
import { Tier } from './salter';

export interface State {
    vn: [number, number];
    i: string;
    s: string;
    p?: string;
    d: string;
    f: string;
    dt: string;
    et: string;
    kt: string | string[];
    k: string[];
    nt: string | string[];
    n: string[];
    bt: string;
    b: string[];
    c: string[];
    ee: EstablishmentState;
    di?: string;
}

export interface EstablishmentState {
    d: string;
    s: string;
}

export interface SaltyState {
    sxlt: string;
    pidx: number;
    kidx: number;
    stem: string;
    tier: Tier;
    dcode: string;
    icodes: string[];
    ncodes: string[];
    transferable: boolean;
}

export interface RandyState {
    prxs: string[];
    nxts: string[];
}

export interface GroupState {
    mhab: HabState;
    keys: string[];
    ndigs: string[];
}

export interface ExternState {
    extern_type: string;
    pidx: number;
    [key: string]: unknown;
}

export interface HabState {
    name: string;
    prefix: string;
    transferable: boolean;
    state: State;
    windexes: unknown[];
    [Algos.salty]?: SaltyState;
    [Algos.randy]?: RandyState;
    [Algos.group]?: GroupState;
    [Algos.extern]?: ExternState;
}
