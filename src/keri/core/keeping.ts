import { Salter } from './salter';
import { Algos, SaltyCreator, RandyCreator } from './manager';
import { MtrDex } from './matter';
import { Tier } from './salter';
import { Encrypter } from '../core/encrypter';
import { Decrypter } from './decrypter';
import { b } from './core';
import { Cipher } from './cipher';
import { Diger } from './diger';
import { Prefixer } from './prefixer';
import { Signer } from './signer';
import {
    ExternState,
    GroupKeyState,
    HabState,
    RandyKeyState,
    SaltyKeyState,
    KeyState,
} from './keyState';

/** External module definition */
export interface ExternalModuleType {
    new (pidx: number, args: IdentifierManagerParams): IdentifierManager;
}

export interface ExternalModule {
    type: string;
    name: string;
    module: ExternalModuleType;
}

export type IdentifierManagerResult = [string[], string[]];
export type SignResult = string[];

export interface IdentifierManagerParams {
    [key: string]: unknown;
}

export interface SaltyManagerParams extends IdentifierManagerParams {
    pidx: number;
    kidx: number;
    tier: Tier;
    transferable: boolean;
    stem: string | undefined;
    icodes: string[] | undefined;
    ncodes: string[] | undefined;
    dcode: string | undefined;
    sxlt: string | undefined;
}

export interface RandyManagerParams extends IdentifierManagerParams {
    nxts?: string[];
    prxs?: string[];
    transferable: boolean;
}

export interface GroupManagerParams extends IdentifierManagerParams {
    mhab: HabState;
}

/**
 * Interface for KERI identifier (prefix) creation, rotation, and signing.
 * @param T Type of the key keeper
 */
export interface IdentifierManager<
    T extends IdentifierManagerParams = IdentifierManagerParams,
> {
    algo: Algos;
    signers: Signer[];
    params(): T;
    incept(transferable: boolean): Promise<IdentifierManagerResult>;
    rotate(
        ncodes: string[],
        transferable: boolean,
        states?: KeyState[],
        rstates?: KeyState[]
    ): Promise<IdentifierManagerResult>;
    sign(
        ser: Uint8Array,
        indexed?: boolean,
        indices?: number[],
        ondices?: number[]
    ): Promise<SignResult>;
}

/**
 * Creates IdentifierManager instances based on the algorithm and key indexes.
 */
export class IdentifierManagerFactory {
    private modules: Record<string, ExternalModuleType> = {};

    /**
     * Creates a factory for generating IdentifierManagers. Requires a salt to be specified.
     * Allows external key management modules to be configured.
     * @param salter
     * @param externalModules
     */
    constructor(
        private salter: Salter,
        externalModules: ExternalModule[] = []
    ) {
        this.salter = salter;

        for (const mod of externalModules) {
            this.modules[mod.type] = mod.module;
        }
    }

    /**
     *
     * @param algo
     * @param pidx
     * @param kargs
     */
    new(algo: Algos, pidx: number, kargs: any) {
        switch (algo) {
            case Algos.salty:
                return new SaltyIdentifierManager(
                    this.salter!,
                    pidx,
                    kargs['kidx'],
                    kargs['tier'],
                    kargs['transferable'],
                    kargs['stem'],
                    kargs['code'],
                    kargs['count'],
                    kargs['icodes'],
                    kargs['ncode'],
                    kargs['ncount'],
                    kargs['ncodes'],
                    kargs['dcode'],
                    kargs['bran'],
                    kargs['sxlt']
                );
            case Algos.randy:
                return new RandyIdentifierManager(
                    this.salter!,
                    kargs['code'],
                    kargs['count'],
                    kargs['icodes'],
                    kargs['transferable'],
                    kargs['ncode'],
                    kargs['ncount'],
                    kargs['ncodes'],
                    kargs['dcode'],
                    kargs['prxs'],
                    kargs['nxts']
                );
            case Algos.group:
                return new GroupIdentifierManager(
                    this,
                    kargs['mhab'],
                    kargs['states'],
                    kargs['rstates'],
                    kargs['keys'],
                    kargs['ndigs']
                );
            case Algos.extern: {
                const ModuleConstructor = this.modules[kargs.extern_type];
                if (!ModuleConstructor) {
                    throw new Error(
                        `unsupported external module type ${kargs.extern_type}`
                    );
                }

                return new ModuleConstructor(pidx, kargs);
            }
            default:
                throw new Error('Unknown algo');
        }
    }

    /**
     * Generates an algorithm-specific IdentifierManager instance with correct keys based on
     * the indexes provided by the HabState.
     * @param aid HabState with the algorithm and key indexes
     * @returns IdentifierManager instance
     */
    get(aid: HabState): IdentifierManager {
        const algo = aid[Algos.salty]
            ? Algos.salty
            : aid[Algos.randy]
            ? Algos.randy
            : aid[Algos.group]
            ? Algos.group
            : aid[Algos.extern]
            ? Algos.extern
            : undefined;
        if (!algo) {
            throw new Error('No algo specified');
        }
        let kargs = aid[algo];
        if (!kargs) {
            throw new Error('No kargs found in HabState');
        }
        switch (algo) {
            case Algos.salty:
                kargs = kargs as SaltyKeyState;
                return new SaltyIdentifierManager(
                    this.salter,
                    kargs.pidx,
                    kargs.kidx,
                    kargs.tier,
                    kargs.transferable,
                    kargs.stem,
                    undefined,
                    undefined,
                    kargs.icodes,
                    undefined,
                    undefined,
                    kargs.ncodes,
                    kargs.dcode,
                    undefined,
                    kargs.sxlt
                );
            case Algos.randy:
                kargs = kargs as RandyKeyState;
                return new RandyIdentifierManager(
                    this.salter,
                    undefined,
                    undefined,
                    undefined,
                    new Prefixer({ qb64: aid['prefix'] }).transferable,
                    undefined,
                    undefined,
                    [],
                    undefined,
                    kargs.prxs,
                    kargs.nxts
                );
            case Algos.group:
                kargs = kargs as GroupKeyState;
                return new GroupIdentifierManager(
                    this,
                    kargs.mhab,
                    undefined,
                    undefined,
                    kargs.keys,
                    kargs.ndigs
                );
            case Algos.extern: {
                kargs = kargs as ExternState;
                const typ = kargs.extern_type;
                if (typ in this.modules) {
                    const mod = new this.modules[typ](kargs.pidx, kargs);
                    return mod;
                } else {
                    throw new Error(`unsupported external module type ${typ}`);
                }
            }
            default:
                throw new Error('Algo not allowed yet');
        }
    }
}

export class SaltyIdentifierManager implements IdentifierManager {
    private aeid: string;
    private encrypter: Encrypter;
    private decrypter: Decrypter;
    private salter: Salter;
    private pidx: number;
    private kidx: number;
    private tier: Tier;
    private transferable: boolean;
    private stem: string | undefined;
    private code: string;
    private count: number;
    private icodes: string[] | undefined;
    private ncode: string;
    private ncount: number;
    private ncodes: string[] | undefined;
    private dcode: string | undefined;
    private sxlt: string | undefined;
    private bran: string | undefined;
    private creator: SaltyCreator;
    public algo: Algos = Algos.salty;
    public signers: Signer[];

    constructor(
        salter: Salter,
        pidx: number,
        kidx: number = 0,
        tier = Tier.low,
        transferable = false,
        stem: string | undefined = undefined,
        code = MtrDex.Ed25519_Seed,
        count = 1,
        icodes: string[] | undefined = undefined,
        ncode = MtrDex.Ed25519_Seed,
        ncount = 1,
        ncodes: string[] | undefined = undefined,
        dcode = MtrDex.Blake3_256,
        bran: string | undefined = undefined,
        sxlt: string | undefined = undefined
    ) {
        // # Salter is the entered passcode and used for enc/dec of salts for each AID
        this.salter = salter;
        const signer = this.salter.signer(code, transferable, undefined, tier);

        this.aeid = signer.verfer.qb64;

        this.encrypter = new Encrypter({}, b(this.aeid));
        this.decrypter = new Decrypter({}, signer.qb64b);

        this.code = code;
        this.ncode = ncode;
        this.tier = tier;
        this.icodes =
            icodes == undefined ? new Array<string>(count).fill(code) : icodes;
        this.ncodes =
            ncodes == undefined
                ? new Array<string>(ncount).fill(ncode)
                : ncodes;
        this.dcode = dcode;
        this.pidx = pidx;
        this.kidx = kidx;
        this.transferable = transferable;
        this.count = count;
        this.ncount = ncount;
        this.stem = stem == undefined ? 'signify:aid' : stem;

        if (bran != undefined) {
            this.bran = MtrDex.Salt_128 + 'A' + bran!.slice(0, 21);
            this.creator = new SaltyCreator(this.bran, this.tier, this.stem);
            this.sxlt = this.encrypter.encrypt(b(this.creator.salt)).qb64;
        } else if (sxlt == undefined) {
            this.creator = new SaltyCreator(undefined, this.tier, this.stem);
            this.sxlt = this.encrypter.encrypt(b(this.creator.salt)).qb64;
        } else {
            this.sxlt = sxlt;
            const ciph = new Cipher({ qb64: this.sxlt });
            this.creator = new SaltyCreator(
                this.decrypter.decrypt(null, ciph).qb64,
                tier,
                this.stem
            );
        }

        this.signers = this.creator.create(
            this.icodes,
            this.ncount,
            this.ncode,
            this.transferable,
            this.pidx,
            0,
            this.kidx,
            false
        ).signers;
    }

    params(): SaltyManagerParams {
        return {
            sxlt: this.sxlt,
            pidx: this.pidx,
            kidx: this.kidx,
            stem: this.stem,
            tier: this.tier,
            icodes: this.icodes,
            ncodes: this.ncodes,
            dcode: this.dcode,
            transferable: this.transferable,
        };
    }

    async incept(transferable: boolean): Promise<IdentifierManagerResult> {
        this.transferable = transferable;
        this.kidx = 0;

        const signers = this.creator.create(
            this.icodes,
            this.count,
            this.code,
            this.transferable,
            this.pidx,
            0,
            this.kidx,
            false
        );
        const verfers = signers.signers.map((signer) => signer.verfer.qb64);

        const nsigners = this.creator.create(
            this.ncodes,
            this.ncount,
            this.ncode,
            this.transferable,
            this.pidx,
            0,
            this.icodes?.length,
            false
        );
        const digers = nsigners.signers.map(
            (nsigner) =>
                new Diger({ code: this.dcode }, nsigner.verfer.qb64b).qb64
        );

        return [verfers, digers];
    }

    async rotate(
        ncodes: string[],
        transferable: boolean
    ): Promise<[string[], string[]]> {
        this.ncodes = ncodes;
        this.transferable = transferable;
        const signers = this.creator.create(
            this.ncodes,
            this.ncount,
            this.ncode,
            this.transferable,
            this.pidx,
            0,
            this.kidx + this.icodes!.length,
            false
        );
        const verfers = signers.signers.map((signer) => signer.verfer.qb64);

        this.kidx = this.kidx! + this.icodes!.length;
        const nsigners = this.creator.create(
            this.ncodes,
            this.ncount,
            this.ncode,
            this.transferable,
            this.pidx,
            0,
            this.kidx + this.icodes!.length,
            false
        );
        const digers = nsigners.signers.map(
            (nsigner) =>
                new Diger({ code: this.dcode }, nsigner.verfer.qb64b).qb64
        );

        return [verfers, digers];
    }

    async sign(
        ser: Uint8Array,
        indexed = true,
        indices: number[] | undefined = undefined,
        ondices: number[] | undefined = undefined
    ): Promise<SignResult> {
        const signers = this.creator.create(
            this.icodes,
            this.ncount,
            this.ncode,
            this.transferable,
            this.pidx,
            0,
            this.kidx,
            false
        );

        if (indexed) {
            const sigers = [];
            let i = 0;
            for (const [j, signer] of signers.signers.entries()) {
                if (indices != undefined) {
                    i = indices![j];
                    if (typeof i != 'number' || i < 0) {
                        throw new Error(
                            `Invalid signing index = ${i}, not whole number.`
                        );
                    }
                } else {
                    i = j;
                }
                let o = 0;
                if (ondices != undefined) {
                    o = ondices![j];
                    if (
                        (o == undefined ||
                            (typeof o == 'number' &&
                                typeof o != 'number' &&
                                o >= 0))!
                    ) {
                        throw new Error(
                            `Invalid ondex = ${o}, not whole number.`
                        );
                    }
                } else {
                    o = i;
                }
                sigers.push(
                    signer.sign(ser, i, o == undefined ? true : false, o)
                );
            }
            return sigers.map((siger) => siger.qb64);
        } else {
            const cigars = [];
            for (const [, signer] of signers.signers.entries()) {
                cigars.push(signer.sign(ser));
            }
            return cigars.map((cigar) => cigar.qb64);
        }
    }
}

export class RandyIdentifierManager implements IdentifierManager {
    private salter: Salter;
    private code: string;
    private count: number;
    private icodes: string[] | undefined;
    private transferable: boolean;
    private ncount: number;
    private ncodes: string[] | undefined;
    private ncode: string;
    private dcode: string | undefined;
    private prxs: string[] | undefined;
    private nxts: string[] | undefined;
    private aeid: string;
    private encrypter: Encrypter;
    private decrypter: Decrypter;
    private creator: RandyCreator;
    public algo: Algos = Algos.randy;
    public signers: Signer[];

    constructor(
        salter: Salter,
        code = MtrDex.Ed25519_Seed,
        count = 1,
        icodes: string[] | undefined = undefined,
        transferable = false,
        ncode = MtrDex.Ed25519_Seed,
        ncount = 1,
        ncodes: string[],
        dcode = MtrDex.Blake3_256,
        prxs: string[] | undefined = undefined,
        nxts: string[] | undefined = undefined
    ) {
        this.salter = salter;
        this.icodes =
            icodes == undefined ? new Array<string>(count).fill(code) : icodes;
        this.ncodes =
            ncodes == undefined
                ? new Array<string>(ncount).fill(ncode)
                : ncodes;

        this.code = code;
        this.ncode = ncode;
        this.count = count;
        this.ncount = ncount;

        const signer = this.salter.signer(code, transferable);
        this.aeid = signer.verfer.qb64;

        this.encrypter = new Encrypter({}, b(this.aeid));
        this.decrypter = new Decrypter({}, signer.qb64b);

        this.nxts = nxts ?? [];
        this.prxs = prxs ?? [];
        this.transferable = transferable;

        this.icodes = icodes;
        this.ncodes = ncodes;
        this.dcode = dcode;

        this.creator = new RandyCreator();

        this.signers = this.prxs.map((prx) =>
            this.decrypter.decrypt(
                new Cipher({ qb64: prx }).qb64b,
                undefined,
                this.transferable
            )
        );
    }

    params(): RandyManagerParams {
        return {
            nxts: this.nxts,
            prxs: this.prxs,
            transferable: this.transferable,
        };
    }

    async incept(transferable: boolean): Promise<IdentifierManagerResult> {
        this.transferable = transferable;

        const signers = this.creator.create(
            this.icodes,
            this.count,
            this.code,
            this.transferable
        );
        this.prxs = signers.signers.map(
            (signer) => this.encrypter.encrypt(undefined, signer).qb64
        );

        const verfers = signers.signers.map((signer) => signer.verfer.qb64);

        const nsigners = this.creator.create(
            this.ncodes,
            this.ncount,
            this.ncode,
            this.transferable
        );

        this.nxts = nsigners.signers.map(
            (signer) => this.encrypter.encrypt(undefined, signer).qb64
        );

        const digers = nsigners.signers.map(
            (nsigner) =>
                new Diger({ code: this.dcode }, nsigner.verfer.qb64b).qb64
        );

        return [verfers, digers];
    }

    async rotate(
        ncodes: string[],
        transferable: boolean
    ): Promise<IdentifierManagerResult> {
        this.ncodes = ncodes;
        this.transferable = transferable;
        this.prxs = this.nxts;

        const signers = this.nxts!.map((nxt) =>
            this.decrypter.decrypt(
                undefined,
                new Cipher({ qb64: nxt }),
                this.transferable
            )
        );
        const verfers = signers.map((signer) => signer.verfer.qb64);
        const nsigners = this.creator.create(
            this.ncodes,
            this.ncount,
            this.ncode,
            this.transferable
        );

        this.nxts = nsigners.signers.map(
            (signer) => this.encrypter.encrypt(undefined, signer).qb64
        );

        const digers = nsigners.signers.map(
            (nsigner) =>
                new Diger({ code: this.dcode }, nsigner.verfer.qb64b).qb64
        );

        return [verfers, digers];
    }

    async sign(
        ser: Uint8Array,
        indexed = true,
        indices: number[] | undefined = undefined,
        ondices: number[] | undefined = undefined
    ): Promise<SignResult> {
        const signers = this.prxs!.map((prx) =>
            this.decrypter.decrypt(
                new Cipher({ qb64: prx }).qb64b,
                undefined,
                this.transferable
            )
        );

        if (indexed) {
            const sigers = [];
            let i = 0;
            for (const [j, signer] of signers.entries()) {
                if (indices != undefined) {
                    i = indices![j];
                    if (typeof i != 'number' || i < 0) {
                        throw new Error(
                            `Invalid signing index = ${i}, not whole number.`
                        );
                    }
                } else {
                    i = j;
                }
                let o = 0;
                if (ondices != undefined) {
                    o = ondices![j];
                    if (
                        (o == undefined ||
                            (typeof o == 'number' &&
                                typeof o != 'number' &&
                                o >= 0))!
                    ) {
                        throw new Error(
                            `Invalid ondex = ${o}, not whole number.`
                        );
                    }
                } else {
                    o = i;
                }
                sigers.push(
                    signer.sign(ser, i, o == undefined ? true : false, o)
                );
            }
            return sigers.map((siger) => siger.qb64);
        } else {
            const cigars = [];
            for (const [, signer] of signers.entries()) {
                cigars.push(signer.sign(ser));
            }
            return cigars.map((cigar) => cigar.qb64);
        }
    }
}

export class GroupIdentifierManager implements IdentifierManager {
    private manager: IdentifierManagerFactory;
    private mhab: HabState;
    private gkeys: string[] = [];
    private gdigs: string[] = [];
    public algo: Algos = Algos.group;
    public signers: Signer[];

    constructor(
        manager: IdentifierManagerFactory,
        mhab: HabState,
        states: KeyState[] | undefined = undefined,
        rstates: KeyState[] | undefined = undefined,
        keys: string[] = [],
        ndigs: string[] = []
    ) {
        this.manager = manager;
        if (states != undefined) {
            keys = states.map((state) => state['k'][0]);
        }

        if (rstates != undefined) {
            ndigs = rstates.map((state) => state['n'][0]);
        }

        this.gkeys = states?.map((state) => state['k'][0]) ?? keys;
        this.gdigs = rstates?.map((state) => state['n'][0]) ?? ndigs;
        this.mhab = mhab;
        this.signers = [];
    }

    async incept(): Promise<IdentifierManagerResult> {
        return [this.gkeys, this.gdigs];
    }

    /**
     * Performs a multisig rotation
     * @param _ncodes
     * @param _transferable
     * @param states
     * @param rstates key state records for the prior establishment event indicating next key digests.
     *                You should pass in the current key
     */
    async rotate(
        _ncodes: string[],
        _transferable: boolean,
        states: KeyState[],
        rstates: KeyState[]
    ): Promise<IdentifierManagerResult> {
        this.gkeys = states.map((state) => state['k'][0]);
        this.gdigs = rstates.map((state) => state['n'][0]);
        return [this.gkeys, this.gdigs];
    }

    async sign(ser: Uint8Array, indexed: boolean = true): Promise<SignResult> {
        if (!this.mhab.state) {
            throw new Error(`No state in mhab`);
        }

        const key = this.mhab['state']['k'][0];
        const ndig = this.mhab['state']['n'][0];

        const csi = this.gkeys!.indexOf(key); // csi = current signing index (from current rotation event)
        const pni = this.gdigs!.indexOf(ndig); // pni = prior next index (from last establishment event)
        const mkeeper = this.manager.get(this.mhab);

        return await mkeeper.sign(ser, indexed, [csi], [pni]);
    }

    params() {
        return {
            mhab: this.mhab,
            keys: this.gkeys,
            ndigs: this.gdigs,
        };
    }
}
