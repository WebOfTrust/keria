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

    let salt = 'abcdefghijk0123456789'
    let op = await identifiers.create("multisig-ts", {bran: salt})
    let aid = op["response"]

    console.log("Created AID: ", aid)

    console.log("Resolving multisig-kli...")
    op = await oobis.resolve(
        "http://127.0.0.1:5642/oobi/EFBmwh8vdPTofoautCiEjjuA17gSlEnE3xc-xy-fGzWZ/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv" +
        "_VmF_dJNN6vkf2Ha",
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
        "internal");
    while (!op["done"]) {
        op = await operations.get(op["name"]);
        await new Promise(resolve => setTimeout(resolve, 1000)); // sleep for 1 second
    }
    console.log("done.")
    let sigPy = op['response']

    aid = await identifiers.get("multisig-ts")
    let sigTs = aid['state']

    let states = [sigPy, kli, sigTs]
    identifiers.create("multisig", {
        algo: "group", mhab: aid,
        isith: ["1/2", "1/2", "1/2"], nsith: ["1/2", "1/2", "1/2"],
        toad: 2,
        wits: [
            "BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
            "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
            "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"
        ],
        states: states,
        rstates: states
    })
}

