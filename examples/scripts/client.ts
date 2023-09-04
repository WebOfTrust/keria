// @ts-ignore
let signify: any;

// @ts-ignore
import('signify-ts').then(
    (module) => {
        signify = module
        signify.ready().then(() => {
            console.log("Signify client ready!");
            connect().then(() => {
                console.log("Done")
            });
        });
    }
)

async function connect() {
    let url = "http://127.0.0.1:3901"
    let bran = '0123456789abcdefghijk'

    const client = new signify.SignifyClient(url, bran);
    console.log(client.controller.pre)
    const [evt, sign] = client.controller?.event ?? [];
    const data = {
        icp: evt.ked,
        sig: sign.qb64,
        stem: client.controller?.stem,
        pidx: 1,
        tier: client.controller?.tier
    };

    await fetch("http://127.0.0.1:3903/boot", {
        method: "POST",
        body: JSON.stringify(data),
        headers: {
            "Content-Type": "application/json"
        }
    })


    await client.connect()
    let d = await client.state()
    console.log("Connected: ")
    console.log(" Agent: ", d.agent.i, "   Controller: ", d.controller.state.i)

    let identifiers = client.identifiers()
    const oobis = client.oobis()
    const operations = client.operations()
    const exchanges = client.exchanges()

    let salt = 'abcdefghijk0123456789'
    let res = identifiers.create("multisig-ts", {bran: salt})
    let op = await res.op()
    let aid = op["response"]

    await identifiers.addEndRole("multisig-ts", "agent", d.agent.i)

    console.log("Created AID: ", aid)

    console.log("Resolving delegator...")
    op = await oobis.resolve(
        "http://127.0.0.1:5642/oobi/EHpD0-CDWOdu5RJ8jHBSUkOqBZ3cXeDVHWNb_Ul89VI7/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv" +
        "_VmF_dJNN6vkf2Ha",
        "delegator");
    while (!op["done"]) {
        op = await operations.get(op["name"]);
        await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
    }
    console.log("done.")
    // let delegator = op['response']

    console.log("Resolving multisig-kli...")
    op = await oobis.resolve(
        "http://127.0.0.1:5642/oobi/EFBmwh8vdPTofoautCiEjjuA17gSlEnE3xc-xy-fGzWZ",
        "multisig-kli");
    while (!op["done"]) {
        op = await operations.get(op["name"]);
        await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
    }
    console.log("done.")
    let kli = op['response']

    console.log("Resolving multisig-sigpy...")
    op = await oobis.resolve(
        "http://127.0.0.1:3902/oobi/EBcIURLpxmVwahksgrsGW6_dUw0zBhyEHYFk17eWrZfk/agent/EERMVxqeHfFo_eIvyzBXaKdT1EyobZdSs1QXuFyYLjmz",
        "multisig-sigpy");
    while (!op["done"]) {
        op = await operations.get(op["name"]);
        await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
    }
    console.log("done.")
    let sigPy = op['response']

    aid = await identifiers.get("multisig-ts")
    let sigTs = aid['state']

    let states = [sigPy, kli, sigTs]
    let ires = identifiers.create("multisig", {
        algo: "group", mhab: aid,
        delpre: "EHpD0-CDWOdu5RJ8jHBSUkOqBZ3cXeDVHWNb_Ul89VI7",
        toad: 2,
        wits: [
            "BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
            "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
            "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"
        ],
        isith: ["1/3", "1/3", "1/3"], nsith: ["1/3", "1/3", "1/3"],
        states: states,
        rstates: states
    })

    let serder = ires.serder
    let sigs = ires.sigs
    let sigers = sigs.map((sig: any) => new signify.Siger({qb64: sig}))

    let ims = signify.d(signify.messagize(serder, sigers))
    let atc = ims.substring(serder.size)
    let embeds = {
        icp: [serder, atc],
    }

    let smids = states.map((state) =>  state['i'])
    let recp = [sigPy, kli].map((state) =>  state['i'])

    await exchanges.send("multisig-ts", "multisig", aid, "/multisig/icp",
        {'gid': serder.pre, smids: smids, rmids: smids}, embeds, recp)

}

