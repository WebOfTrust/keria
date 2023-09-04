
const prmpt = require("prompt-sync")({ sigint: true });
// @ts-ignore
let signify: any;

// @ts-ignore
import('signify-ts').then(
    (module) => {
        signify = module
        signify.ready().then(() => {
            console.log("Signify client ready!");
            list_notifications().then(() => {
                console.log("Done")
            });
        });
    }
)

async function list_notifications() {
    let url = "http://127.0.0.1:3901"
    let bran = '0123456789abcdefghijk'

    const client = new signify.SignifyClient(url, bran);
    await client.connect()
    let d = await client.state()
    console.log("Connected: ")
    console.log(" Agent: ", d.agent.i, "   Controller: ", d.controller.state.i)

    let identifiers = client.identifiers()
    let notifications = client.notifications()
    let groups = client.groups()
    let registries = client.registries()

    let res = await notifications.list()
    let notes = res.notes

    for (const note of notes) {
        let payload = note.a
        let route = payload.r

        if (route === '/multisig/vcp') {
            let res = await groups.getRequest(payload.d)
            if (res.length == 0) {
                console.log("error extracting exns matching nre for " + payload.data)
            }
            let msg = res[0]

            let sender = msg['sender']
            let group = msg["groupName"]

            let exn = msg['exn']
            let usage = exn['a']["usage"]
            console.log("Credential registry inception request for group AID  :" + group)
            console.log("\tReceived from:  " + sender)
            console.log("\tPurpose:  " + usage)
            console.log("\nAuto-creating new registry...")
            let yes = prmpt("Approve [Y|n]? ")
            if (yes  === "y" || yes === "Y" || yes === "") {
                try {
                    let registryName = prmpt("Enter new local name for registry: ")
                    let embeds = exn['e']
                    let vcp = embeds['vcp']
                    let ixn = embeds['ixn']
                    let serder = new signify.Serder(ixn)
                    let ghab = await identifiers.get(group)

                    let keeper = client.manager.get(ghab)
                    let sigs = keeper.sign(signify.b(serder.raw))
                    let sigers = sigs.map((sig: any) => new signify.Siger({qb64: sig}))

                    let ims = signify.d(signify.messagize(serder, sigers))
                    let atc = ims.substring(serder.size)
                    embeds = {
                        vcp: [new signify.Serder(vcp), undefined],
                        ixn: [serder, atc]
                    }

                    sender = ghab["group"]["mhab"]
                    keeper = client.manager.get(sender)
                    let [nexn, end] = signify.exchange("/multisig/vcp",
                        {'gid': ghab["prefix"], 'usage': "test"},
                        sender["prefix"], undefined, undefined, undefined, undefined, embeds)

                    console.log(nexn.pretty())
                    let esigs = keeper.sign(nexn.raw)
                    await groups.sendRequest(group, nexn.ked, esigs, signify.d(end))

                    return await registries.createFromEvents(ghab, group, registryName, vcp, ixn, sigs)
                } catch(e: any) {
                    console.log(e)
                }
            }



        }

    }

}

