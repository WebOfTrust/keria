import signify from 'signify-ts';

await makeends();

async function makeends() {
    const url = 'http://127.0.0.1:3901';
    const bran = '0123456789abcdefghijk';

    await signify.ready();
    const client = new signify.SignifyClient(url, bran);
    await client.connect();
    const d = await client.state();
    console.log('Connected: ');
    console.log(' Agent: ', d.agent.i, '   Controller: ', d.controller.state.i);

    const identifiers = client.identifiers();
    const escrows = client.escrows();

    const members = await identifiers.members('multisig');
    const hab = await identifiers.get('multisig');
    const aid = hab['prefix'];
    const signing = members['signing'];

    const auths = new Map<string, Date>();
    const stamp = new Date();

    signing.forEach((end: any) => {
        const ends = end['ends'];
        const roles = ['agent', 'mailbox'];
        roles.forEach((role) => {
            if (role in ends) {
                Object.keys(ends[role]).forEach((k: any) => {
                    const key = [aid, role, k].join('.');
                    auths.set(key, stamp);
                });
            }
        });
    });

    const rpys = await escrows.listReply('/end/role');

    rpys.forEach((rpy: object) => {
        const serder = new signify.Serder(rpy);
        const payload = serder.ked['a'];

        const key = Object.values(payload).join('.');
        const then = new Date(Date.parse(serder.ked['dt']));
        if (auths.has(key) && then < stamp) {
            identifiers.addEndRole(
                'multisig',
                payload['role'],
                payload['eid'],
                serder.ked['dt']
            );
            auths.set(key, then); // track signed role auths by timestamp signed
        }
    });
}
