let signify:any;

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

    await fetch( "http://127.0.0.1:3903/boot", {
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

    let salt = 'abcdefghijk0123456789'
    let op = await identifiers.create("multisig-ts", {bran: salt})
    let aid = op["response"]

    console.log("Created AID: ", aid)
}

