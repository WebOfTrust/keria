import {
    Algos,
    Controller,
    CreateIdentiferArgs,
    IdentifierManagerFactory,
    MtrDex,
    Serials,
    Tier,
    Vrsn_1_0,
    incept,
} from '../../src';
import {
    EstablishmentState,
    HabState,
    KeyState,
} from '../../src/keri/core/keyState';

export async function createMockIdentifierState(
    name: string,
    bran: string,
    kargs: CreateIdentiferArgs = {}
): Promise<HabState> {
    const controller = new Controller(bran, Tier.low);
    const manager = new IdentifierManagerFactory(controller.salter);
    const algo = kargs.algo == undefined ? Algos.salty : kargs.algo;

    const transferable = kargs.transferable ?? true;
    const isith = kargs.isith ?? '1';
    const nsith = kargs.nsith ?? '1';
    const wits = kargs.wits ?? [];
    const toad = kargs.toad ?? 0;
    const dcode = kargs.dcode ?? MtrDex.Blake3_256;
    const proxy = kargs.proxy;
    const delpre = kargs.delpre;
    const data = kargs.data != undefined ? [kargs.data] : [];
    const pre = kargs.pre;
    const states = kargs.states;
    const rstates = kargs.rstates;
    const prxs = kargs.prxs;
    const nxts = kargs.nxts;
    const mhab = kargs.mhab;
    const _keys = kargs.keys;
    const _ndigs = kargs.ndigs;
    const count = kargs.count;
    const ncount = kargs.ncount;
    const tier = kargs.tier;
    const extern_type = kargs.extern_type;
    const extern = kargs.extern;

    const keeper = manager!.new(algo, 0, {
        transferable: transferable,
        isith: isith,
        nsith: nsith,
        wits: wits,
        toad: toad,
        proxy: proxy,
        delpre: delpre,
        dcode: dcode,
        data: data,
        algo: algo,
        pre: pre,
        prxs: prxs,
        nxts: nxts,
        mhab: mhab,
        states: states,
        rstates: rstates,
        keys: _keys,
        ndigs: _ndigs,
        bran: bran,
        count: count,
        ncount: ncount,
        tier: tier,
        extern_type: extern_type,
        extern: extern,
    });
    const [keys, ndigs] = await keeper!.incept(transferable);
    const serder = incept({
        keys: keys!,
        isith: isith,
        ndigs: ndigs,
        nsith: nsith,
        toad: toad,
        wits: wits,
        cnfg: [],
        data: data,
        version: Vrsn_1_0,
        kind: Serials.JSON,
        code: dcode,
        intive: false,
        ...(delpre ? { delpre } : {}),
    });

    return {
        name: name,
        prefix: serder.pre,
        [algo]: keeper.params(),
        transferable,
        windexes: [],
        state: {
            vn: [serder.version.major, serder.version.minor],
            s: serder.sad.s,
            d: serder.sad.d,
            i: serder.pre,
            ee: serder.sad as EstablishmentState,
            kt: serder.sad.kt,
            k: serder.sad.k,
            nt: serder.sad.nt,
            n: serder.sad.n,
            bt: serder.sad.bt,
            b: serder.sad.b,
            p: serder.sad.p ?? '',
            f: '',
            dt: new Date().toISOString().replace('Z', '000+00:00'),
            et: '',
            c: [],
            di: serder.sad.di ?? '',
        } as KeyState,
        icp_dt: '2023-12-01T10:05:25.062609+00:00',
    };
}
