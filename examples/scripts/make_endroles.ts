import signify from "signify-ts";

await makeends();

async function makeends() {
    let url = "http://127.0.0.1:3901"
    let bran = '0123456789abcdefghijk'

    await signify.ready();
    const client = new signify.SignifyClient(url, bran);
    await client.connect()
    let d = await client.state()
    console.log("Connected: ")
    console.log(" Agent: ", d.agent.i, "   Controller: ", d.controller.state.i)

    let identifiers = client.identifiers()
    let escrows = client.escrows()

    let members = await identifiers.members("multisig")
    let hab = await identifiers.get("multisig")
    let aid = hab["prefix"]
    let signing = members['signing']

    let auths = new Map<string, Date>()
    let stamp = new Date()

    signing.forEach((end: any) => {
        let ends = end["ends"]
        let roles = ["agent", "mailbox"]
        roles.forEach((role) => {
            if (role in ends) {
                Object.keys(ends[role]).forEach((k:any) => {
                    let key = [aid, role, k].join(".")
                    auths.set(key, stamp)
                })
            }
        })
    })

    let rpys = await escrows.listReply("/end/role")

    rpys.forEach((rpy:object) => {
        let serder = new signify.Serder(rpy)
        let payload = serder.ked['a']

        let key = Object.values(payload).join(".")
        let then = new Date(Date.parse(serder.ked["dt"]))
        if (auths.has(key) && then < stamp) {
            identifiers.addEndRole("multisig", payload["role"], payload["eid"], serder.ked["dt"])
            auths.set(key, then)  // track signed role auths by timestamp signed
        }
    })

}

