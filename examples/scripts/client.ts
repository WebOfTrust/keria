import signify from 'signify-ts';

await connect();

async function connect() {
    const url = 'http://127.0.0.1:3901';
    const bran = '0123456789abcdefghijk';

    await signify.ready();
    const client = new signify.SignifyClient(url, bran);
    console.log(client.controller.pre);
    const [evt, sign] = client.controller?.event ?? [];
    const data = {
        icp: evt.ked,
        sig: sign.qb64,
        stem: client.controller?.stem,
        pidx: 1,
        tier: client.controller?.tier,
    };

    await fetch('http://127.0.0.1:3903/boot', {
        method: 'POST',
        body: JSON.stringify(data),
        headers: {
            'Content-Type': 'application/json',
        },
    });

    await client.connect();
    const d = await client.state();
    console.log('Connected: ');
    console.log(' Agent: ', d.agent.i, '   Controller: ', d.controller.state.i);

    const identifiers = client.identifiers();
    const oobis = client.oobis();
    const operations = client.operations();
    const exchanges = client.exchanges();

    const salt = 'abcdefghijk0123456789';
    const res = await identifiers.create('multisig-ts', { bran: salt });
    let op = await res.op();
    let aid = op['response'];

    await identifiers.addEndRole('multisig-ts', 'agent', d.agent.i);

    console.log('Created AID: ', aid);

    console.log('Resolving delegator...');
    op = await oobis.resolve(
        'http://127.0.0.1:5642/oobi/EHpD0-CDWOdu5RJ8jHBSUkOqBZ3cXeDVHWNb_Ul89VI7/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv' +
            '_VmF_dJNN6vkf2Ha',
        'delegator'
    );
    while (!op['done']) {
        op = await operations.get(op['name']);
        await new Promise((resolve) => setTimeout(resolve, 1000)); // sleep for 1 second
    }
    console.log('done.');
    // let delegator = op['response']

    console.log('Resolving multisig-kli...');
    op = await oobis.resolve(
        'http://127.0.0.1:5642/oobi/EFBmwh8vdPTofoautCiEjjuA17gSlEnE3xc-xy-fGzWZ',
        'multisig-kli'
    );
    while (!op['done']) {
        op = await operations.get(op['name']);
        await new Promise((resolve) => setTimeout(resolve, 1000)); // sleep for 1 second
    }
    console.log('done.');
    const kli = op['response'];

    console.log('Resolving multisig-sigpy...');
    op = await oobis.resolve(
        'http://127.0.0.1:3902/oobi/EBcIURLpxmVwahksgrsGW6_dUw0zBhyEHYFk17eWrZfk/agent/EERMVxqeHfFo_eIvyzBXaKdT1EyobZdSs1QXuFyYLjmz',
        'multisig-sigpy'
    );
    while (!op['done']) {
        op = await operations.get(op['name']);
        await new Promise((resolve) => setTimeout(resolve, 1000)); // sleep for 1 second
    }
    console.log('done.');
    const sigPy = op['response'];

    aid = await identifiers.get('multisig-ts');
    const sigTs = aid['state'];

    const states = [sigPy, kli, sigTs];
    const ires = await identifiers.create('multisig', {
        algo: signify.Algos.group,
        mhab: aid,
        delpre: 'EHpD0-CDWOdu5RJ8jHBSUkOqBZ3cXeDVHWNb_Ul89VI7',
        toad: 2,
        wits: [
            'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha',
            'BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM',
            'BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX',
        ],
        isith: ['1/3', '1/3', '1/3'],
        nsith: ['1/3', '1/3', '1/3'],
        states: states,
        rstates: states,
    });

    const serder = ires.serder;
    const sigs = ires.sigs;
    const sigers = sigs.map((sig: any) => new signify.Siger({ qb64: sig }));

    const ims = signify.d(signify.messagize(serder, sigers));
    const atc = ims.substring(serder.size);
    const embeds = {
        icp: [serder, atc],
    };

    const smids = states.map((state) => state['i']);
    const recp = [sigPy, kli].map((state) => state['i']);

    await exchanges.send(
        'multisig-ts',
        'multisig',
        aid,
        '/multisig/icp',
        { gid: serder.pre, smids: smids, rmids: smids },
        embeds,
        recp
    );
}
