import signify from 'signify-ts';
import promptSync from 'prompt-sync';

const prmpt = promptSync({ sigint: true });

await list_notifications();

async function list_notifications() {
    const url = 'http://127.0.0.1:3901';
    const bran = '0123456789abcdefghijk';

    await signify.ready();
    const client = new signify.SignifyClient(url, bran);
    await client.connect();
    const d = await client.state();
    console.log('Connected: ');
    console.log(' Agent: ', d.agent.i, '   Controller: ', d.controller.state.i);

    const identifiers = client.identifiers();
    const notifications = client.notifications();
    const groups = client.groups();
    const registries = client.registries();

    const res = await notifications.list();
    const notes = res.notes;

    for (const note of notes) {
        const payload = note.a;
        const route = payload.r;

        if (route === '/multisig/vcp') {
            const res = await groups.getRequest(payload.d);
            if (res.length == 0) {
                console.log(
                    'error extracting exns matching nre for ' + payload.data
                );
            }
            const msg = res[0];

            let sender = msg['sender'];
            const group = msg['groupName'];

            const exn = msg['exn'];
            const usage = exn['a']['usage'];
            console.log(
                'Credential registry inception request for group AID  :' + group
            );
            console.log('\tReceived from:  ' + sender);
            console.log('\tPurpose:  ' + usage);
            console.log('\nAuto-creating new registry...');
            const yes = prmpt('Approve [Y|n]? ');
            if (yes === 'y' || yes === 'Y' || yes === '') {
                try {
                    const registryName = prmpt(
                        'Enter new local name for registry: '
                    );
                    let embeds = exn['e'];
                    const vcp = embeds['vcp'];
                    const ixn = embeds['ixn'];
                    const serder = new signify.Serder(ixn);
                    const ghab = await identifiers.get(group);

                    let keeper = client.manager!.get(ghab);
                    const sigs = keeper.sign(signify.b(serder.raw));
                    const sigers = sigs.map(
                        (sig: any) => new signify.Siger({ qb64: sig })
                    );

                    const ims = signify.d(signify.messagize(serder, sigers));
                    const atc = ims.substring(serder.size);
                    embeds = {
                        vcp: [new signify.Serder(vcp), undefined],
                        ixn: [serder, atc],
                    };

                    sender = ghab['group']['mhab'];
                    keeper = client.manager!.get(sender);
                    const [nexn, end] = signify.exchange(
                        '/multisig/vcp',
                        { gid: ghab['prefix'], usage: 'test' },
                        sender['prefix'],
                        undefined,
                        undefined,
                        undefined,
                        undefined,
                        embeds
                    );

                    console.log(nexn.pretty());
                    const esigs = keeper.sign(signify.b(nexn.raw));
                    await groups.sendRequest(
                        group,
                        nexn.ked,
                        esigs,
                        signify.d(end)
                    );

                    return await registries.createFromEvents(
                        ghab,
                        group,
                        registryName,
                        vcp,
                        ixn,
                        sigs
                    );
                } catch (e: any) {
                    console.log(e);
                }
            }
        }
    }
}
