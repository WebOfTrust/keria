import { strict as assert } from "assert";

let signify: any;
const url = "http://127.0.0.1:3901"
const boot_url = "http://127.0.0.1:3903"

// @ts-ignore
import('signify-ts').then(
    (module) => {
        signify = module
        signify.ready().then(() => {
            console.log("*** Starting MULTISIG test ***");
            run().then(() => {
                console.log("*** Test complete ***")
            });
        });
    }
)

async function run() {
    
    // Boot three clients
    const bran1 = signify.randomPasscode()
    const bran2 = signify.randomPasscode()
    const bran3 = signify.randomPasscode()
    const client1 = new signify.SignifyClient(url, bran1, signify.Tier.low, boot_url);
    const client2 = new signify.SignifyClient(url, bran2, signify.Tier.low, boot_url);
    const client3 = new signify.SignifyClient(url, bran3, signify.Tier.low, boot_url);
    await client1.boot()
    await client2.boot()
    await client3.boot()
    await client1.connect()
    await client2.connect()
    await client3.connect()
    const state1 = await client1.state()
    const state2 = await client2.state()
    const state3 = await client3.state()
    console.log("Client 1 connected. Client AID:",state1.controller.state.i,"Agent AID: ", state1.agent.i)
    console.log("Client 2 connected. Client AID:",state2.controller.state.i,"Agent AID: ", state2.agent.i)
    console.log("Client 3 connected. Client AID:",state3.controller.state.i,"Agent AID: ", state3.agent.i)


    // Create two identifiers, one for each client
    let icpResult1 = client1.identifiers().create('multisig1',  {
        toad: 3,
        wits: [
            "BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
            "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
            "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"]
        })
    let op1 = await icpResult1.op()
    while (!op1["done"] ) {
            op1 = await client1.operations().get(op1.name);
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    const aid1 = await client1.identifiers().get("multisig1")
    await client1.identifiers().addEndRole("multisig1", 'agent', client1!.agent!.pre)
    console.log("Multisig1's AID:", aid1.prefix)

    let icpResult2 = client2.identifiers().create('multisig2',  {
        toad: 3,
        wits: [
            "BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
            "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
            "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"]
        })
    let op2 = await icpResult2.op()
    while (!op2["done"] ) {
            op2 = await client2.operations().get(op2.name);
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    const aid2 = await client2.identifiers().get("multisig2")
    await client2.identifiers().addEndRole("multisig2", 'agent', client2!.agent!.pre)
    console.log("Multisig2's AID:", aid2.prefix)

    let icpResult3 = client3.identifiers().create('multisig3',  {
        toad: 3,
        wits: [
            "BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
            "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
            "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"]
        })
    let op3 = await icpResult3.op()
    while (!op3["done"] ) {
            op3 = await client3.operations().get(op3.name);
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    const aid3 = await client3.identifiers().get("multisig3")
    await client3.identifiers().addEndRole("multisig3", 'agent', client3!.agent!.pre)
    console.log("Multisig3's AID:", aid3.prefix)

    // Exchenge OOBIs
    console.log("Resolving OOBIs")
    let oobi1 = await client1.oobis().get("multisig1","agent")
    let oobi2 = await client2.oobis().get("multisig2","agent")
    let oobi3 = await client3.oobis().get("multisig3","agent")
    
    op1 = await client1.oobis().resolve(oobi2.oobis[0],"multisig2")
    while (!op1["done"]) {
        op1 = await client1.operations().get(op1.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    op1 = await client1.oobis().resolve(oobi3.oobis[0],"multisig3")
    while (!op1["done"]) {
        op1 = await client1.operations().get(op1.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    console.log("Multisig1 resolved 2 OOBIs")
    
    op2 = await client2.oobis().resolve(oobi1.oobis[0],"multisig1")
    while (!op2["done"]) {
        op2 = await client2.operations().get(op2.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    op2 = await client2.oobis().resolve(oobi3.oobis[0],"multisig3")
    while (!op2["done"]) {
        op2 = await client2.operations().get(op2.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    console.log("Multisig2 resolved 2 OOBIs")

    op3 = await client3.oobis().resolve(oobi1.oobis[0],"multisig1")
    while (!op3["done"]) {
        op3 = await client3.operations().get(op3.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    op3 = await client3.oobis().resolve(oobi2.oobis[0],"multisig2")
    while (!op3["done"]) {
        op3 = await client3.operations().get(op3.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    console.log("Multisig3 resolved 2 OOBIs")
    
    // First member start the creation of a multisig identifier
    let rstates = [aid1["state"], aid2["state"], aid3["state"]]
    let states = rstates
    icpResult1 = client1.identifiers().create("multisig",{
        algo: signify.Algos.group,
        mhab: aid1,
        isith: 3, 
        nsith: 3,
        toad: 3,
        wits: [
            "BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
            "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
            "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"],
        states: states,
        rstates: rstates
    })
    op1 = await icpResult1.op()
    let serder = icpResult1.serder
    let sigs = icpResult1.sigs
    let sigers = sigs.map((sig: any) => new signify.Siger({qb64: sig}))

    let ims = signify.d(signify.messagize(serder, sigers))
    let atc = ims.substring(serder.size)
    let embeds = {
        icp: [serder, atc],
    }

    let smids = states.map((state) =>  state['i'])
    let recp = [aid2["state"], aid3["state"]].map((state) =>  state['i'])

    await client1.exchanges().send("multisig1", "multisig", aid1, "/multisig/icp",
        {'gid': serder.pre, smids: smids, rmids: smids}, embeds, recp)
    console.log("Multisig1 create multisig, waiting for others...")

    // Second member check notifications and join the multisig  
    let msgSaid = ""
    while (msgSaid=="") {
        let notifications = await client2.notifications().list()
        for (let notif of notifications.notes){
            if (notif.a.r == '/multisig/icp') {
                msgSaid = notif.a.d
                await client2.notifications().mark(notif.i)
                console.log("Multisig2 received request to join multisig")
            }
        }
        await new Promise(resolve => setTimeout(resolve, 1000));
    }

    let res = await client2.groups().getRequest(msgSaid)
    let exn = res[0].exn
    let icp = exn.e.icp
    
    icpResult2 = client2.identifiers().create("multisig",{
        algo: signify.Algos.group,
        mhab: aid2,
        isith: icp.kt, 
        nsith: icp.nt,
        toad: parseInt(icp.bt),
        wits: icp.b,
        states: states,
        rstates: rstates
    })
    op2 = await icpResult2.op()
    serder = icpResult2.serder
    sigs = icpResult2.sigs
    sigers = sigs.map((sig: any) => new signify.Siger({qb64: sig}))

    ims = signify.d(signify.messagize(serder, sigers))
    atc = ims.substring(serder.size)
    embeds = {
        icp: [serder, atc],
    }

    smids = exn.a.smids
    recp = [aid1["state"], aid3["state"]].map((state) =>  state['i'])

    await client2.exchanges().send("multisig2", "multisig", aid2, "/multisig/icp",
        {'gid': serder.pre, smids: smids, rmids: smids}, embeds, recp)
    console.log("Multisig2 joined multisig, waiting for others...")


    // Third member check notifications and join the multisig  
    msgSaid = ""
    while (msgSaid=="") {
        let notifications = await client3.notifications().list()
        for (let notif of notifications.notes){
            if (notif.a.r == '/multisig/icp') {
                msgSaid = notif.a.d
                await client3.notifications().mark(notif.i)
                console.log("Multisig3 received request to join multisig")
            }
        }
        await new Promise(resolve => setTimeout(resolve, 1000));
    }

    res = await client3.groups().getRequest(msgSaid)
    exn = res[0].exn
    icp = exn.e.icp
    icpResult3 = client3.identifiers().create("multisig",{
        algo: signify.Algos.group,
        mhab: aid3,
        isith: icp.kt, 
        nsith: icp.nt,
        toad: parseInt(icp.bt),
        wits: icp.b,
        states: states,
        rstates: rstates
    })
    op3 = await icpResult3.op()
    serder = icpResult3.serder
    sigs = icpResult3.sigs
    sigers = sigs.map((sig: any) => new signify.Siger({qb64: sig}))

    ims = signify.d(signify.messagize(serder, sigers))
    atc = ims.substring(serder.size)
    embeds = {
        icp: [serder, atc],
    }

    smids = exn.a.smids
    recp = [aid1["state"], aid2["state"]].map((state) =>  state['i'])

    await client3.exchanges().send("multisig3", "multisig", aid3, "/multisig/icp",
        {'gid': serder.pre, smids: smids, rmids: smids}, embeds, recp)
    console.log("Multisig3 joined, multisig waiting for others...")

    while (!op1["done"]) {
        op1 = await client1.operations().get(op1.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    while (!op2["done"]) {
        op2 = await client2.operations().get(op2.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    while (!op3["done"]) {
        op3 = await client3.operations().get(op3.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    console.log("Multisig created!")

    const identifiers1 = await client1.identifiers().list()
    assert.equal(identifiers1.aids.length, 2)
    assert.equal(identifiers1.aids[0].name, "multisig")
    assert.equal(identifiers1.aids[1].name, "multisig1")

    const identifiers2 = await client2.identifiers().list()
    assert.equal(identifiers2.aids.length, 2)
    assert.equal(identifiers2.aids[0].name, "multisig")
    assert.equal(identifiers2.aids[1].name, "multisig2")

    const identifiers3 = await client3.identifiers().list()
    assert.equal(identifiers3.aids.length, 2)
    assert.equal(identifiers3.aids[0].name, "multisig")
    assert.equal(identifiers3.aids[1].name, "multisig3")

    console.log("Client 1 identifiers:", identifiers1.aids[0].name, identifiers1.aids[1].name)
    console.log("Client 2 identifiers:", identifiers2.aids[0].name, identifiers2.aids[1].name)
    console.log("Client 3 identifiers:", identifiers3.aids[0].name, identifiers3.aids[1].name)

}