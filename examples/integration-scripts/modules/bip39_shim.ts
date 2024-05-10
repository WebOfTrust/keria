import { mnemonicToSeedSync, generateMnemonic } from 'bip39';
import { Diger, Signer, MtrDex, Keeper, KeeperResult, Algos } from 'signify-ts';

export class BIP39Shim implements Keeper {
    private icount: number;
    private ncount: number;
    private dcode: string | undefined;
    private pidx: number = 0;
    private kidx: number = 0;
    private transferable: boolean;
    private stem: string;
    private mnemonics: string = '';
    algo: Algos = Algos.extern;
    signers: Signer[] = [];

    constructor(pidx: number, kargs: any) {
        this.icount = kargs.icount ?? 1;
        this.ncount = kargs.ncount ?? 1;
        this.pidx = pidx;
        this.kidx = kargs.kidx ?? 0;
        this.transferable = kargs.transferable ?? true;
        this.stem = kargs.stem ?? 'bip39_shim';
        if (kargs.extern != undefined && kargs.extern.mnemonics != undefined) {
            this.mnemonics = kargs.extern.mnemonics;
        }
        this.dcode = kargs.dcode;
    }

    params() {
        return {
            pidx: this.pidx,
            kidx: this.kidx,
            mnemonics: this.mnemonics,
        };
    }

    keys(count: number, kidx: number, transferable: boolean) {
        const keys = [];
        for (let idx = 0; idx < count; idx++) {
            const keyId = `${this.stem}-${this.pidx}-${kidx + idx}`;
            const seed = mnemonicToSeedSync(this.mnemonics, keyId);
            const signer = new Signer({
                raw: new Uint8Array(seed),
                code: MtrDex.Ed25519_Seed,
                transferable: transferable,
            });
            keys.push(signer);
        }
        return keys;
    }

    async incept(transferable: boolean): Promise<KeeperResult> {
        const signers = this.keys(this.icount, this.kidx, transferable);
        const verfers = signers.map((signer) => signer.verfer.qb64);

        const nsigners = this.keys(
            this.ncount,
            this.kidx + this.icount,
            transferable
        );
        const digers = nsigners.map(
            (nsigner) =>
                new Diger({ code: this.dcode }, nsigner.verfer.qb64b).qb64
        );
        return [verfers, digers];
    }

    async rotate(
        // TODO: This signature is incompatible with Keeper
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        count: any, //number,
        transferable: boolean
    ): Promise<KeeperResult> {
        const signers = this.keys(
            this.ncount,
            this.kidx + this.icount,
            transferable
        );
        const verfers = signers.map((signer) => signer.verfer.qb64);

        this.kidx = this.kidx + this.icount;
        this.icount = this.ncount;

        // TODO: Due to incompatible signature.
        this.ncount = count as number;

        const nsigners = this.keys(
            this.ncount,
            this.kidx + this.icount,
            this.transferable
        );
        const digers = nsigners.map(
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
    ) {
        const signers = this.keys(this.icount, this.kidx, this.transferable);

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

    generateMnemonic(strength: number) {
        return generateMnemonic(strength);
    }
}
