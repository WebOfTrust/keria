import signify from 'signify-ts';

await connect();

async function connect() {
    let url = 'http://127.0.0.1:3901';
    let bran = '0123456789abcdefghijk';

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
    let d = await client.state();
    console.log('Connected: ');
    console.log(' Agent: ', d.agent.i, '   Controller: ', d.controller.state.i);

    let identifiers = client.identifiers();
    const oobis = client.oobis();
    const operations = client.operations();
    const exchanges = client.exchanges();

    let salt = '0123456789lmnopqrstuv';
    let res = await identifiers.create('agent0', {bran: salt});
    let op = await res.op();
    let aid = op['response'];

    await identifiers.addEndRole('agent0', 'agent', d.agent.i);

    console.log('Created AID: ', aid);

    console.log('Resolving multisig1...');
    op = await oobis.resolve(
        'http://127.0.0.1:5642/oobi/EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4/witness',
        'multisig1'
    );
    while (!op['done']) {
        op = await operations.get(op['name']);
        await new Promise((resolve) => setTimeout(resolve, 1000)); // sleep for 1 second
    }
    console.log('done.');
    let multisig1 = op['response'];

    console.log('Resolving multisig2...');
    op = await oobis.resolve(
        'http://127.0.0.1:5642/oobi/EJccSRTfXYF6wrUVuenAIHzwcx3hJugeiJsEKmndi5q1/witness',
        'multisig2'
    );
    while (!op['done']) {
        op = await operations.get(op['name']);
        await new Promise((resolve) => setTimeout(resolve, 1000)); // sleep for 1 second
    }
    console.log('done.');
    let multisig2 = op['response'];

    aid = await identifiers.get('agent0');
    let agent0 = aid['state'];

    let states = [multisig2, multisig1, agent0];
    let ires = await identifiers.create('multisig', {
        algo: signify.Algos.group,
        mhab: aid,
        toad: 3,
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

    let serder = ires.serder;
    let sigs = ires.sigs;
    let sigers = sigs.map((sig: any) => new signify.Siger({qb64: sig}));

    let ims = signify.d(signify.messagize(serder, sigers));
    let atc = ims.substring(serder.size);
    let embeds = {
        icp: [serder, atc],
    };

    let smids = states.map((state) => state['i']);
    let recp = [multisig2, multisig1].map((state) => state['i']);

    await exchanges.send(
        'agent0',
        'multisig',
        aid,
        '/multisig/icp',
        {gid: serder.pre, smids: smids, rmids: smids},
        embeds,
        recp
    );

    let multisigAID = serder.pre
    console.log("Waiting for multisig AID to be created")

    op = await ires.op()
    while (!op['done']) {
        op = await operations.get(op['name']);
        await new Promise((resolve) => setTimeout(resolve, 1000)); // sleep for 1 second
    }
    console.log('done.');

    console.log("Resolving schema...")
    op = await oobis.resolve(
        'http://127.0.0.1:7723/oobi/EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao',
        'schema'
    );
    while (!op['done']) {
        op = await operations.get(op['name']);
        await new Promise((resolve) => setTimeout(resolve, 1000)); // sleep for 1 second
    }
    console.log('done.');
    let schemaSAID = "EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao"


    console.log("Creating registry...")
    let vcpRes1 = await client.registries().create({
        name: 'multisig',
        registryName: 'vLEI Registry',
        nonce: 'AHSNDV3ABI6U8OIgKaj3aky91ZpNL54I5_7-qwtC6q2s',
    });

    let op1 = await vcpRes1.op();
    serder = vcpRes1.regser;
    let regk = serder.pre
    let anc = vcpRes1.serder;
    sigs = vcpRes1.sigs;

    sigers = sigs.map((sig: any) => new signify.Siger({qb64: sig}));
    ims = signify.d(signify.messagize(anc, sigers));
    atc = ims.substring(anc.size);

    let regbeds = {
        vcp: [serder, ''],
        anc: [anc, atc],
    };

    recp = ["EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4", "EJccSRTfXYF6wrUVuenAIHzwcx3hJugeiJsEKmndi5q1"]
    await client.exchanges().send(
        'agent0',
        'multisig',
        aid,
        '/multisig/vcp',
        {gid: multisigAID, usage: 'Issue vLEIs'},
        regbeds,
        recp
    );

    while (!op1['done']) {
        op1 = await operations.get(op1['name']);
        await new Promise((resolve) => setTimeout(resolve, 1000)); // sleep for 1 second
    }
    console.log('done.');

    console.log("Creating credential from multisig...")
    // Issue credential
    const vcdata = {
        LEI: '5493001KJTIIGC8Y1R17',
    };
    let holder = "ELjSFdrTdCebJlmvbFNX9-TLhR2PO0_60al1kQp5_e6k"

    let TIME = "2023-09-25T16:01:37.000000+00:00"
    let credRes = await client.credentials().issue('multisig', regk, schemaSAID, holder, vcdata,
        undefined, undefined, TIME);
    op1 = await credRes.op()

    let acdc = new signify.Serder(credRes.acdc)
    let iss = credRes.iserder
    let ianc = credRes.anc
    let isigs = credRes.sigs

    sigers = isigs.map((sig: any) => new signify.Siger({qb64: sig}));
    ims = signify.d(signify.messagize(ianc, sigers));
    atc = ims.substring(anc.size);

    let vcembeds = {
        acdc: [acdc, ''],
        iss: [iss, ''],
        anc: [ianc, atc],
    };

    await client.exchanges().send(
        'agent0',
        'multisig',
        aid,
        '/multisig/iss',
        {gid: multisigAID},
        vcembeds,
        recp
    );

    while (!op1['done']) {
        op1 = await client.operations().get(op1.name);
        await new Promise((resolve) => setTimeout(resolve, 1000));
    }

    console.log("Creating IPEX grant message to send...")

    let [grant, gsigs, end] = await client.ipex().grant("multisig", holder, "", acdc, iss, ianc, atc, undefined, TIME)
    let m = await client.identifiers().get("multisig")

    let mstate = m["state"]
    let seal = ['SealEvent', {i: m['prefix'], s: mstate["ee"]["s"], d: mstate["ee"]["d"]}];
    sigers = gsigs.map((sig: any) => new signify.Siger({qb64: sig}));

    let gims = signify.d(signify.messagize(grant, sigers, seal, undefined, undefined, true));
    atc = gims.substring(grant.size)
    atc += end

    let gembeds: any = {
        exn: [grant, atc]
    }

    await client.exchanges().send(
        'agent0',
        'multisig',
        aid,
        '/multisig/exn',
        {gid: multisigAID},
        gembeds,
        recp
    );

    console.log("... done!")
}
