import signify, {
    Algos,
    CreateIdentiferArgs,
    CredentialData,
    Serder,
    Siger,
    SignifyClient,
    d,
    messagize,
    HabState,
    Operation,
    b,
    EventResult,
    IssueCredentialResult,
    CredentialResult,
} from '#signify-ts';
import { getStates, waitAndMarkNotification } from './test-util.ts';

export interface AcceptMultisigInceptArgs {
    groupName: string;
    localMemberName: string;
    msgSaid: string;
}

export interface StartMultisigInceptArgs {
    groupName: string;
    localMemberName: string;
    participants: string[];
    isith?: number | string | string[];
    nsith?: number | string | string[];
    toad?: number;
    wits?: string[];
    delpre?: string;
}

export async function acceptMultisigIncept(
    client2: SignifyClient,
    { groupName, localMemberName, msgSaid }: AcceptMultisigInceptArgs
): Promise<Operation> {
    const memberHab = await client2.identifiers().get(localMemberName);

    const res = await client2.groups().getRequest(msgSaid);
    const exn = res[0].exn;
    const icp = exn.e.icp;
    const smids = exn.a.smids;
    const rmids = exn.a.rmids;
    const states = await getStates(client2, smids);
    const rstates = await getStates(client2, rmids);

    const icpResult2 = await client2.identifiers().create(groupName, {
        algo: Algos.group,
        mhab: memberHab,
        isith: icp.kt,
        nsith: icp.nt,
        toad: parseInt(icp.bt),
        wits: icp.b,
        states: states,
        rstates: rstates,
        delpre: icp.di,
    });
    const op2 = await icpResult2.op();
    const serder = icpResult2.serder;
    const sigs = icpResult2.sigs;
    const sigers = sigs.map((sig) => new Siger({ qb64: sig }));

    const ims = d(messagize(serder, sigers));
    const atc = ims.substring(serder.size);
    const embeds = {
        icp: [serder, atc],
    };

    for (const smid of smids) {
        await client2
            .exchanges()
            .send(
                localMemberName,
                groupName,
                memberHab,
                '/multisig/icp',
                { gid: serder.pre, smids: smids, rmids: smids },
                embeds,
                smid
            );
    }

    return op2;
}

export async function addEndRoleMultisig(
    client: SignifyClient,
    groupHab: HabState,
    timestamp: string
): Promise<Operation[]> {
    if (!('group' in groupHab && groupHab.group)) {
        throw new Error('multisigAID is not a group AID');
    }

    const ops: Operation[] = [];
    const members = await client.identifiers().members(groupHab.name);
    const signings = members['signing'];
    const smids = signings.map((s: { aid: string }) => s.aid);

    for (const signing of signings) {
        const eid = Object.keys(signing.ends.agent)[0];
        const rpy = await client
            .identifiers()
            .addEndRole(groupHab.name, 'agent', eid, timestamp);
        const op = await rpy.op();
        ops.push(op);

        const seal = [
            'SealEvent',
            {
                i: groupHab.prefix,
                s: groupHab.state['ee']['s'],
                d: groupHab.state['ee']['d'],
            },
        ];
        const sigers = rpy.sigs.map(
            (sig: string) => new signify.Siger({ qb64: sig })
        );
        const roleims = signify.d(
            signify.messagize(
                rpy.serder,
                sigers,
                seal,
                undefined,
                undefined,
                false
            )
        );
        const atc = roleims.substring(rpy.serder.size);

        for (const smid of smids) {
            await client
                .exchanges()
                .send(
                    groupHab.group.mhab.name,
                    'multisig',
                    groupHab.group.mhab,
                    '/multisig/rpy',
                    { gid: groupHab.prefix },
                    { rpy: [rpy.serder, atc] },
                    smid
                );
        }
    }

    return ops;
}

export async function admitMultisig(
    client: SignifyClient,
    aid: HabState,
    otherMembersAIDs: HabState[],
    multisigAID: HabState,
    recipientAID: HabState,
    timestamp: string
    // numGrantMsgs: number
) {
    const grantMsgSaid = await waitAndMarkNotification(
        client,
        '/exn/ipex/grant'
    );

    const [admit, sigs, end] = await client.ipex().admit({
        senderName: multisigAID.name,
        message: '',
        grantSaid: grantMsgSaid,
        recipient: recipientAID.prefix,
        datetime: timestamp,
    });

    await client.ipex().submitAdmit(multisigAID.name, admit, sigs, end);

    const mstate = multisigAID.state;
    const seal = [
        'SealEvent',
        { i: multisigAID.prefix, s: mstate['ee']['s'], d: mstate['ee']['d'] },
    ];
    const sigers = sigs.map((sig: string) => new signify.Siger({ qb64: sig }));
    const ims = signify.d(signify.messagize(admit, sigers, seal));
    let atc = ims.substring(admit.size);
    atc += end;
    const gembeds = {
        exn: [admit, atc],
    };

    await client
        .exchanges()
        .send(
            aid.name,
            'multisig',
            aid,
            '/multisig/exn',
            { gid: multisigAID.prefix },
            gembeds,
            multisigAID.prefix
        );
}

export async function createAIDMultisig(
    client: SignifyClient,
    aid: HabState,
    otherMembersAIDs: HabState[],
    groupName: string,
    kargs: CreateIdentiferArgs,
    isInitiator: boolean = false
) {
    if (!isInitiator) await waitAndMarkNotification(client, '/multisig/icp');

    const icpResult = await client.identifiers().create(groupName, kargs);
    const op = await icpResult.op();

    const serder = icpResult.serder;
    const sigs = icpResult.sigs;
    const sigers = sigs.map((sig) => new signify.Siger({ qb64: sig }));
    const ims = signify.d(signify.messagize(serder, sigers));
    const atc = ims.substring(serder.size);
    const embeds = {
        icp: [serder, atc],
    };
    const smids = kargs.states?.map((state) => state['i']) ?? [];

    for (const smid of smids) {
        await client
            .exchanges()
            .send(
                aid.name,
                'multisig',
                aid,
                '/multisig/icp',
                { gid: serder.pre, smids: smids, rmids: smids },
                embeds,
                smid
            );
    }

    return op;
}

export async function createRegistryMultisig(
    client: SignifyClient,
    aid: HabState,
    otherMembersAIDs: HabState[],
    multisigAID: HabState,
    registryName: string,
    nonce: string,
    isInitiator: boolean = false
) {
    if (!isInitiator)
        await waitAndMarkNotification(client, '/multisig/vcp', {
            timeout: 30000,
        });

    const vcpResult = await client.registries().create({
        name: multisigAID.name,
        registryName: registryName,
        nonce: nonce,
    });
    const op = await vcpResult.op();

    const serder = vcpResult.regser;
    const anc = vcpResult.serder;
    const sigs = vcpResult.sigs;
    const sigers = sigs.map((sig) => new signify.Siger({ qb64: sig }));
    const ims = signify.d(signify.messagize(anc, sigers));
    const atc = ims.substring(anc.size);
    const regbeds = {
        vcp: [serder, ''],
        anc: [anc, atc],
    };

    await client
        .exchanges()
        .send(
            aid.name,
            'registry',
            aid,
            '/multisig/vcp',
            { gid: multisigAID.prefix },
            regbeds,
            multisigAID.prefix
        );

    return op;
}

export async function delegateMultisig(
    client: SignifyClient,
    group: HabState,
    anchor: { i: string; s: string; d: string }
) {
    if (!('group' in group && group.group)) {
        throw new Error('group is not a group AID');
    }

    const result = await client.delegations().approve(group.name, anchor);
    const op = await result.op();

    const members = await client.identifiers().members(group.name);
    const signings = members['signing'];
    const smids = signings.map((s: { aid: string }) => s.aid);

    const sigers = result.sigs.map((sig) => new signify.Siger({ qb64: sig }));
    const ims = signify.d(signify.messagize(result.serder, sigers));
    const atc = ims.substring(result.serder.size);

    for (const smid of smids) {
        await client.exchanges().send(
            group.group.mhab.name,
            'multisig',
            group.group.mhab,
            '/multisig/ixn',
            { gid: result.serder.pre, smids: smids, rmids: smids },
            {
                ixn: [result.serder, atc],
            },
            smid
        );
    }

    return op;
}

export async function grantMultisig(
    client: SignifyClient,
    aid: HabState,
    _otherMembersAIDs: HabState[],
    multisigAID: HabState,
    recipientAID: HabState,
    credential: CredentialResult,
    timestamp: string,
    isInitiator: boolean = false
) {
    if (!isInitiator) await waitAndMarkNotification(client, '/multisig/exn');

    const [grant, sigs, end] = await client.ipex().grant({
        senderName: multisigAID.name,
        acdc: new Serder(credential.sad),
        anc: new Serder(credential.anc),
        iss: new Serder(credential.iss),
        recipient: recipientAID.prefix,
        datetime: timestamp,
    });

    await client.ipex().submitGrant(multisigAID.name, grant, sigs, end);

    const mstate = multisigAID.state;
    const seal = [
        'SealEvent',
        { i: multisigAID.prefix, s: mstate['ee']['s'], d: mstate['ee']['d'] },
    ];
    const sigers = sigs.map((sig) => new signify.Siger({ qb64: sig }));
    const gims = signify.d(signify.messagize(grant, sigers, seal));
    let atc = gims.substring(grant.size);
    atc += end;
    const gembeds = {
        exn: [grant, atc],
    };

    await client
        .exchanges()
        .send(
            aid.name,
            'multisig',
            aid,
            '/multisig/exn',
            { gid: multisigAID.prefix },
            gembeds,
            multisigAID.prefix
        );
}

export async function issueCredentialMultisig(
    client: SignifyClient,
    aid: HabState,
    otherMembersAIDs: HabState[],
    multisigAIDName: string,
    kargsIss: CredentialData,
    isInitiator: boolean = false
) {
    if (!isInitiator) await waitAndMarkNotification(client, '/multisig/iss');

    const credResult = await client
        .credentials()
        .issue(multisigAIDName, kargsIss);
    const op = credResult.op;

    const multisigAID = await client.identifiers().get(multisigAIDName);
    const keeper = client.manager!.get(multisigAID);
    const sigs = await keeper.sign(signify.b(credResult.anc.raw));
    const sigers = sigs.map((sig: string) => new signify.Siger({ qb64: sig }));
    const ims = signify.d(signify.messagize(credResult.anc, sigers));
    const atc = ims.substring(credResult.anc.size);
    const embeds = {
        acdc: [credResult.acdc, ''],
        iss: [credResult.iss, ''],
        anc: [credResult.anc, atc],
    };

    await client
        .exchanges()
        .send(
            aid.name,
            'multisig',
            aid,
            '/multisig/iss',
            { gid: multisigAID.prefix },
            embeds,
            multisigAID.prefix
        );

    return op;
}

export async function startMultisigIncept(
    client: SignifyClient,
    {
        groupName,
        localMemberName,
        participants,
        ...args
    }: StartMultisigInceptArgs
): Promise<Operation> {
    const aid1 = await client.identifiers().get(localMemberName);
    const participantStates = await getStates(client, participants);
    const icpResult1 = await client.identifiers().create(groupName, {
        algo: Algos.group,
        mhab: aid1,
        isith: args.isith,
        nsith: args.nsith,
        toad: args.toad,
        wits: args.wits,
        delpre: args.delpre,
        states: participantStates,
        rstates: participantStates,
    });
    const op1 = await icpResult1.op();
    const serder = icpResult1.serder;

    const sigs = icpResult1.sigs;
    const sigers = sigs.map((sig) => new Siger({ qb64: sig }));
    const ims = d(messagize(serder, sigers));
    const atc = ims.substring(serder.size);
    const embeds = {
        icp: [serder, atc],
    };

    const smids = participantStates.map((state) => state['i']);

    for (const smid of smids) {
        await client
            .exchanges()
            .send(
                localMemberName,
                groupName,
                aid1,
                '/multisig/icp',
                { gid: serder.pre, smids: smids, rmids: smids },
                embeds,
                smid
            );
    }

    return op1;
}

export interface RotateMultisigArgs {
    group: HabState;
    smids: string[];
    rmids: string[];
}

export async function rotate(
    client: SignifyClient,
    args: RotateMultisigArgs
): Promise<Operation> {
    if (!('group' in args.group) || !args.group.group) {
        throw new Error('args.group is not a group AID');
    }

    const states = await getStates(client, args.smids);
    const rstates = await getStates(client, args.rmids);

    const rot = await client.identifiers().rotate(args.group.name, {
        states,
        rstates,
    });

    const sigers = rot.sigs.map((sig) => new signify.Siger({ qb64: sig }));
    const ims = signify.d(signify.messagize(rot.serder, sigers));
    const atc = ims.substring(rot.serder.size);

    const smids = states.map((state) => state['i']);
    const rmids = rstates.map((state) => state['i']);

    for (const rmid of rmids) {
        await client
            .exchanges()
            .send(
                args.group.group.mhab.name,
                'multisig',
                args.group.group.mhab,
                '/multisig/rot',
                { gid: rot.serder.pre, smids, rmids },
                { rot: [rot.serder, atc] },
                rmid
            );
    }

    return rot.op();
}

export interface AcceptRotationArgs {
    said: string;
}

export async function acceptRotation(
    client: SignifyClient,
    args: AcceptRotationArgs
) {
    const res = await client.groups().getRequest(args.said);
    const exn = res[0].exn;
    const serder = new Serder(exn.e.rot);
    const group = await client.identifiers().get(exn.a.gid);

    if (!('group' in group) || !group.group) {
        throw new Error('group is not a group AID');
    }

    const smids = exn.a.smids;
    const rmids = exn.a.rmids;
    const states = await getStates(client, smids);
    const rstates = await getStates(client, rmids);

    const keeper = client.manager!.get(group);

    await keeper.rotate([], true, states, rstates);
    const sigs = await keeper.sign(b(serder.raw));

    const response = await client.fetch(
        `/identifiers/${group.name}/events`,
        'POST',
        {
            [keeper.algo]: keeper.params(),
            rot: serder.sad,
            sigs: sigs,
            smids,
            rmids,
        }
    );

    const result = new EventResult(serder, sigs, response);

    const sigers = sigs.map((sig) => new signify.Siger({ qb64: sig }));
    const ims = signify.d(signify.messagize(serder, sigers));
    const atc = ims.substring(serder.size);

    for (const rmid of rmids) {
        await client
            .exchanges()
            .send(
                group.group.mhab.name,
                'multisig',
                group.group.mhab,
                '/multisig/rot',
                { gid: serder.pre, smids, rmids },
                { rot: [serder, atc] },
                rmid
            );
    }

    return await result.op();
}

/**
 * Bug-faithful co-signer accept: re-issues via credentials().issue(group, exn.e.acdc)
 * instead of using embedded iss/anc from the multisig message (wallet acceptMultisigIssuance).
 */
export async function acceptMultisigIssuanceBugFaithful(
    client: SignifyClient,
    groupName: string
): Promise<Operation> {
    const msgSaid = await waitAndMarkNotification(client, '/multisig/iss');
    const res = await client.groups().getRequest(msgSaid);
    const exn = res[0].exn;
    const iss = await client.credentials().issue(groupName, exn.e.acdc);
    await multisigIssue(client, groupName, iss);
    return iss.op;
}

export async function multisigIssue(
    client: SignifyClient,
    groupName: string,
    result: IssueCredentialResult
) {
    const hab = await client.identifiers().get(groupName);

    if (!('group' in hab && hab.group)) {
        throw new Error('groupHab is not a group AID');
    }
    const members = await client.identifiers().members(groupName);

    const keeper = client.manager!.get(hab);
    const sigs = await keeper.sign(signify.b(result.anc.raw));
    const sigers = sigs.map((sig: string) => new signify.Siger({ qb64: sig }));
    const ims = signify.d(signify.messagize(result.anc, sigers));
    const atc = ims.substring(result.anc.size);

    const embeds = {
        acdc: [result.acdc, ''],
        iss: [result.iss, ''],
        anc: [result.anc, atc],
    };

    const smids = members.signing.map((m: { aid: string }) => m.aid);

    for (const smid of smids) {
        await client
            .exchanges()
            .send(
                hab.group.mhab.name,
                'multisig',
                hab.group.mhab,
                '/multisig/iss',
                { gid: hab.prefix },
                embeds,
                smid
            );
    }
}

export async function multisigRevoke(
    client: SignifyClient,
    groupName: string,
    rev: Serder,
    anc: Serder
) {
    const hab = await client.identifiers().get(groupName);

    if (!('group' in hab && hab.group)) {
        throw new Error('groupHab is not a group AID');
    }

    const members = await client.identifiers().members(groupName);

    const keeper = client.manager!.get(hab);
    const sigs = await keeper.sign(signify.b(anc.raw));
    const sigers = sigs.map((sig: string) => new signify.Siger({ qb64: sig }));
    const ims = signify.d(signify.messagize(anc, sigers));
    const atc = ims.substring(anc.size);

    const embeds = {
        iss: [rev, ''],
        anc: [anc, atc],
    };

    for (const smid of members.signing.map((m: { aid: string }) => m.aid)) {
        await client
            .exchanges()
            .send(
                hab.group.mhab.name,
                'multisig',
                hab.group.mhab,
                '/multisig/rev',
                { gid: hab.prefix },
                embeds,
                smid
            );
    }
}
