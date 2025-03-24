import { Algos } from './manager.ts';
import { Tier } from './salter.ts';

export interface KeyState {
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

/**
 * Marker interface for state configuring an IdentifierManager.
 */
// eslint-disable-next-line @typescript-eslint/no-empty-object-type
export interface IdentifierManagerState {}

/**
 * Interface defining configuration parameters for a specified, deterministic salt of an IdentifierManager.
 */
export interface SaltyKeyState extends IdentifierManagerState {
    /**
     * Encrypted
     */
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

/**
 * Interface defining configuration parameters for a random seed identifier manager.
 */
export interface RandyKeyState extends IdentifierManagerState {
    prxs: string[];
    nxts: string[];
}

/**
 * Interface defining properties a multi-signature group identifier manager.
 */
export interface GroupKeyState extends IdentifierManagerState {
    mhab: HabState;
    keys: string[];
    ndigs: string[];
}

/**
 * Interface defining properties for an external module identifier manager that uses externally managed keys such as in an HSM or a KMS system.
 */
export interface ExternState extends IdentifierManagerState {
    extern_type: string;
    pidx: number;
    [key: string]: unknown;
}

/**
 * Interface defining properties of an identifier habitat, know as a Hab in KERIpy.
 */
export interface HabState {
    name: string;
    prefix: string;
    transferable: boolean;
    state: KeyState;
    windexes: unknown[];
    icp_dt: string;
    [Algos.salty]?: SaltyKeyState;
    [Algos.randy]?: RandyKeyState;
    [Algos.group]?: GroupKeyState;
    [Algos.extern]?: ExternState;
}
