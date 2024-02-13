import { Algos, Siger, SignifyClient, d, messagize } from 'signify-ts';

export interface AcceptMultisigInceptArgs {
    groupName: string;
    localMemberName: string;
    msgSaid: string;
}

export async function acceptMultisigIncept(
    client2: SignifyClient,
    { groupName, localMemberName, msgSaid }: AcceptMultisigInceptArgs
) {
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

    const recipients = smids.filter((id: string) => memberHab.prefix !== id);

    await client2
        .exchanges()
        .send(
            localMemberName,
            'multisig',
            memberHab,
            '/multisig/icp',
            { gid: serder.pre, smids: smids, rmids: smids },
            embeds,
            recipients
        );

    return op2;
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

export async function startMultisigIncept(
    client: SignifyClient,
    {
        groupName,
        localMemberName,
        participants,
        ...args
    }: StartMultisigInceptArgs
) {
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

    await client
        .exchanges()
        .send(
            'member1',
            'multisig',
            aid1,
            '/multisig/icp',
            { gid: serder.pre, smids: smids, rmids: smids },
            embeds,
            participants
        );
    return op1;
}

async function getStates(client: SignifyClient, prefixes: string[]) {
    const participantStates = await Promise.all(
        prefixes.map((p) => client.keyStates().get(p))
    );
    return participantStates.map((s) => s[0]);
}
