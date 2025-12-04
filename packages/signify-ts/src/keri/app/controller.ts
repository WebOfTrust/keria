import { SaltyCreator } from '../core/manager.ts';
import { Salter, Tier } from '../core/salter.ts';
import { MtrDex } from '../core/matter.ts';
import { Diger } from '../core/diger.ts';
import { incept, rotate, interact } from '../core/eventing.ts';
import { Serder } from '../core/serder.ts';
import { Tholder } from '../core/tholder.ts';
import { Ilks, b, Serials, Vrsn_1_0 } from '../core/core.ts';
import { Verfer } from '../core/verfer.ts';
import { Encrypter } from '../core/encrypter.ts';
import { Decrypter } from '../core/decrypter.ts';
import { Cipher } from '../core/cipher.ts';
import { Seqner } from '../core/seqner.ts';
import { CesrNumber } from '../core/number.ts';

/**
 * Agent is a custodial entity that can be used in conjuntion with a local Client to establish the
 * KERI "signing at the edge" semantic
 */
export class Agent {
    pre: string;
    anchor: string;
    verfer: Verfer | null;
    state: any | null;
    sn: number | undefined;
    said: string | undefined;

    constructor(agent: any) {
        this.pre = '';
        this.anchor = '';
        this.verfer = null;
        this.state = null;
        this.sn = 0;
        this.said = '';
        this.parse(agent);
    }

    private parse(agent: Agent) {
        const [state, verfer] = this.event(agent);

        this.sn = new CesrNumber({}, undefined, state['s']).num;
        this.said = state['d'];

        if (state['et'] !== Ilks.dip) {
            throw new Error(`invalid inception event type ${state['et']}`);
        }

        this.pre = state['i'];
        if (!state['di']) {
            throw new Error('no anchor to controller AID');
        }

        this.anchor = state['di'];

        this.verfer = verfer;
        this.state = state;
    }

    private event(evt: any): [any, Verfer, Diger] {
        if (evt['k'].length !== 1) {
            throw new Error(`agent inception event can only have one key`);
        }

        const verfer = new Verfer({ qb64: evt['k'][0] });

        if (evt['n'].length !== 1) {
            throw new Error(`agent inception event can only have one next key`);
        }

        const diger = new Diger({ qb64: evt['n'][0] });

        const tholder = new Tholder({ sith: evt['kt'] });
        if (tholder.num !== 1) {
            throw new Error(`invalid threshold ${tholder.num}, must be 1`);
        }

        const ntholder = new Tholder({ sith: evt['nt'] });
        if (ntholder.num !== 1) {
            throw new Error(
                `invalid next threshold ${ntholder.num}, must be 1`
            );
        }
        return [evt, verfer, diger];
    }
}

/**
 * Controller is responsible for managing signing keys for the client and agent.  The client
 * signing key represents the Account for the client on the agent
 */
export class Controller {
    /*
    The bran is the combination of the first 21 characters of the passcode passed in prefixed with 'A' and '0A'.
    Looks like: '0A' + 'A' + 'thisismysecretkeyseed'
    Or: "0AAthisismysecretkeyseed"

    This is interpreted as encoded Base64URLSafe characters when used as the salt for key generation.
     */
    private bran: string;
    /**
     * The stem is the prefix for the stretched input bytes the controller's cryptographic
     * key pairs are derived from.
     */
    public stem: string;
    /**
     * The security tier for the identifiers created by this Controller.
     */
    public tier: Tier;
    /**
     * The rotation index used during key generation by this Controller.
     */
    public ridx: number;
    /**
     * The salter is a cryptographic salt used to derive the controller's cryptographic key pairs
     * and is deterministically derived from the bran and the security tier.
     */
    public salter: any;
    /**
     * The current signing key used to sign requests for this controller.
     */
    public signer: any;
    /**
     * The next signing key of which a digest is committed to in an establishment event (inception or rotation) to become the
     * signing key after the next rotation.
     * @private
     */
    private nsigner: any;
    /**
     * Either the current establishment event, inception or rotation, or the interaction event used for delegation approval.
     */
    public serder: Serder;
    /**
     * Current public keys formatted in fully-qualified Base64.
     * @private
     */
    private keys: string[];
    /**
     * Digests of the next public keys formatted in fully-qualified Base64.
     */
    public ndigs: string[];

    /**
     * Creates a Signify Controller starting at key index 0 that generates keys in
     * memory based on the provided seed, or bran, the tier, and the rotation index.
     *
     * The rotation index is used as follows:
     *
     * @param bran
     * @param tier
     * @param ridx
     * @param state
     */
    constructor(
        bran: string,
        tier: Tier,
        ridx: number = 0,
        state: any | null = null
    ) {
        this.bran = MtrDex.Salt_128 + 'A' + bran.substring(0, 21); // qb64 salt for seed
        this.stem = 'signify:controller';
        this.tier = tier;
        this.ridx = ridx;
        const codes = undefined; // Defines the types of seeds that the SaltyCreator will create. Defaults to undefined.
        const keyCount = 1; // The number of keys to create. Defaults to 1.
        const transferable = true; // Whether the keys are transferable. Defaults to true.
        const code = MtrDex.Ed25519_Seed; // The type  cryptographic seed to create by default when not overiddeen by "codes".
        const pidx = 0; // The index of this identifier prefix of all managed identifiers created for this SignifyClient Controller. Defaults to 0.
        const kidx = 0; // The overall starting key index for the first key this rotation set of keys. This is not a local index to this set of keys but an index in the overall set of keys for all keys in this sequence.
        // Defaults to 0. Multiply rotation index (ridx) times key count to get the overall key index.

        this.salter = new Salter({ qb64: this.bran, tier: this.tier });

        const creator = new SaltyCreator(
            this.salter.qb64,
            this.tier,
            this.stem
        );

        // Creates the first key pair used to sign the inception event.
        // noinspection UnnecessaryLocalVariableJS
        const initialKeyIndex = ridx; // will be zero for inception
        this.signer = creator
            .create(
                codes,
                keyCount,
                code,
                transferable,
                pidx,
                initialKeyIndex,
                kidx
            )
            .signers.pop(); // assumes only one key pair is created because keyCount is 1

        // Creates the second key pair which a digest of the public key is committed to in the inception event.
        const nextKeyIndex = ridx + 1;
        this.nsigner = creator
            .create(
                codes,
                keyCount,
                code,
                transferable,
                pidx,
                nextKeyIndex,
                kidx
            )
            .signers.pop(); // assumes only one key pair is created because keyCount is 1
        this.keys = [this.signer.verfer.qb64];
        this.ndigs = [
            new Diger({ code: MtrDex.Blake3_256 }, this.nsigner.verfer.qb64b)
                .qb64,
        ];

        if (state == null || state['ee']['s'] == 0) {
            this.serder = incept({
                keys: this.keys,
                isith: '1',
                nsith: '1',
                ndigs: this.ndigs,
                code: MtrDex.Blake3_256,
                toad: '0',
                wits: [],
            });
        } else {
            this.serder = new Serder(state['ee']);
        }
    }

    approveDelegation(_agent: Agent) {
        const seqner = new Seqner({ sn: _agent.sn });
        const anchor = { i: _agent.pre, s: seqner.snh, d: _agent.said };
        const sn = new CesrNumber({}, undefined, this.serder.sad['s']).num + 1;
        this.serder = interact({
            pre: this.serder.pre,
            dig: this.serder.sad['d'],
            sn: sn,
            data: [anchor],
            version: Vrsn_1_0,
            kind: Serials.JSON,
        });
        return [this.signer.sign(this.serder.raw, 0).qb64];
    }

    get pre(): string {
        return this.serder.pre;
    }

    get event() {
        const siger = this.signer.sign(this.serder.raw, 0);
        return [this.serder, siger];
    }

    get verfers(): [] {
        return this.signer.verfer();
    }

    derive(state: any) {
        if (state != undefined && state['ee']['s'] === '0') {
            return incept({
                keys: this.keys,
                isith: '1',
                nsith: '1',
                ndigs: this.ndigs,
                code: MtrDex.Blake3_256,
                toad: '0',
                wits: [],
            });
        } else {
            return new Serder({ sad: state.controller['ee'] });
        }
    }

    rotate(bran: string, aids: Array<any>) {
        const nbran = MtrDex.Salt_128 + 'A' + bran.substring(0, 21); // qb64 salt for seed
        const nsalter = new Salter({ qb64: nbran, tier: this.tier });
        const nsigner = this.salter.signer(undefined, false);

        const creator = new SaltyCreator(
            this.salter.qb64,
            this.tier,
            this.stem
        );
        const signer = creator
            .create(
                undefined,
                1,
                MtrDex.Ed25519_Seed,
                true,
                0,
                this.ridx + 1,
                0,
                false
            )
            .signers.pop();

        const ncreator = new SaltyCreator(nsalter.qb64, this.tier, this.stem);
        this.signer = ncreator
            .create(
                undefined,
                1,
                MtrDex.Ed25519_Seed,
                true,
                0,
                this.ridx,
                0,
                false
            )
            .signers.pop();
        this.nsigner = ncreator
            .create(
                undefined,
                1,
                MtrDex.Ed25519_Seed,
                true,
                0,
                this.ridx + 1,
                0,
                false
            )
            .signers.pop();

        this.keys = [this.signer.verfer.qb64, signer?.verfer.qb64];
        this.ndigs = [new Diger({}, this.nsigner.verfer.qb64b).qb64];

        const rot = rotate({
            pre: this.pre,
            keys: this.keys,
            dig: this.serder.sad['d'],
            isith: ['1', '0'],
            nsith: '1',
            ndigs: this.ndigs,
        });

        const sigs = [
            signer?.sign(b(rot.raw), 1, false, 0).qb64,
            this.signer.sign(rot.raw, 0).qb64,
        ];
        const encrypter = new Encrypter({}, b(nsigner.verfer.qb64));
        const decrypter = new Decrypter({}, nsigner.qb64b);
        const sxlt = encrypter.encrypt(b(this.bran)).qb64;

        const keys: Record<any, any> = {};

        for (const aid of aids) {
            const pre: string = aid['prefix'] as string;
            if ('salty' in aid) {
                const salty: any = aid['salty'];
                const cipher = new Cipher({ qb64: salty['sxlt'] });
                const dnxt = decrypter.decrypt(null, cipher).qb64;

                // Now we have the AID salt, use it to verify against the current public keys
                const acreator = new SaltyCreator(
                    dnxt,
                    salty['tier'],
                    salty['stem']
                );
                const signers = acreator.create(
                    salty['icodes'],
                    undefined,
                    MtrDex.Ed25519_Seed,
                    salty['transferable'],
                    salty['pidx'],
                    0,
                    salty['kidx'],
                    false
                );
                const _signers = [];
                for (const signer of signers.signers) {
                    _signers.push(signer.verfer.qb64);
                }
                const pubs = aid['state']['k'];

                if (pubs.join(',') != _signers.join(',')) {
                    throw new Error('Invalid Salty AID');
                }

                const asxlt = encrypter.encrypt(b(dnxt)).qb64;
                keys[pre] = {
                    sxlt: asxlt,
                };
            } else if ('randy' in aid) {
                const randy = aid['randy'];
                const prxs = randy['prxs'];
                const nxts = randy['nxts'];

                const nprxs = [];
                const signers = [];
                for (const prx of prxs) {
                    const cipher = new Cipher({ qb64: prx });
                    const dsigner = decrypter.decrypt(null, cipher, true);
                    signers.push(dsigner);
                    nprxs.push(encrypter.encrypt(b(dsigner.qb64)).qb64);
                }
                const pubs = aid['state']['k'];
                const _signers = [];
                for (const signer of signers) {
                    _signers.push(signer.verfer.qb64);
                }

                if (pubs.join(',') != _signers.join(',')) {
                    throw new Error(
                        `unable to rotate, validation of encrypted public keys ${pubs} failed`
                    );
                }

                const nnxts = [];
                for (const nxt of nxts) {
                    nnxts.push(this.recrypt(nxt, decrypter, encrypter));
                }

                keys[pre] = {
                    prxs: nprxs,
                    nxts: nnxts,
                };
            } else {
                throw new Error('invalid aid type ');
            }
        }

        const data = {
            rot: rot.sad,
            sigs: sigs,
            sxlt: sxlt,
            keys: keys,
        };
        return data;
    }

    recrypt(enc: string, decrypter: Decrypter, encrypter: Encrypter) {
        const cipher = new Cipher({ qb64: enc });
        const dnxt = decrypter.decrypt(null, cipher).qb64;
        return encrypter.encrypt(b(dnxt)).qb64;
    }
}
