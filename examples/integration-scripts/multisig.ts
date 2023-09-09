import { strict as assert } from "assert"
import signify from "signify-ts"

const url = "http://127.0.0.1:3901"
const boot_url = "http://127.0.0.1:3903"

await run()

async function run() {
    await signify.ready()
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


    // Create three identifiers, one for each client
    let icpResult1 = client1.identifiers().create('member1',  {
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
    let aid1 = await client1.identifiers().get("member1")
    await client1.identifiers().addEndRole("member1", 'agent', client1!.agent!.pre)
    console.log("Member1's AID:", aid1.prefix)

    let icpResult2 = client2.identifiers().create('member2',  {
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
    let aid2 = await client2.identifiers().get("member2")
    await client2.identifiers().addEndRole("member2", 'agent', client2!.agent!.pre)
    console.log("Member2's AID:", aid2.prefix)

    let icpResult3 = client3.identifiers().create('member3',  {
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
    let aid3 = await client3.identifiers().get("member3")
    await client3.identifiers().addEndRole("member3", 'agent', client3!.agent!.pre)
    console.log("Member3's AID:", aid3.prefix)

    // Exchange OOBIs
    console.log("Resolving OOBIs")
    let oobi1 = await client1.oobis().get("member1","agent")
    let oobi2 = await client2.oobis().get("member2","agent")
    let oobi3 = await client3.oobis().get("member3","agent")
    
    op1 = await client1.oobis().resolve(oobi2.oobis[0],"member2")
    while (!op1["done"]) {
        op1 = await client1.operations().get(op1.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    op1 = await client1.oobis().resolve(oobi3.oobis[0],"member3")
    while (!op1["done"]) {
        op1 = await client1.operations().get(op1.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    console.log("Member1 resolved 2 OOBIs")
    
    op2 = await client2.oobis().resolve(oobi1.oobis[0],"member1")
    while (!op2["done"]) {
        op2 = await client2.operations().get(op2.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    op2 = await client2.oobis().resolve(oobi3.oobis[0],"member3")
    while (!op2["done"]) {
        op2 = await client2.operations().get(op2.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    console.log("Member2 resolved 2 OOBIs")

    op3 = await client3.oobis().resolve(oobi1.oobis[0],"member1")
    while (!op3["done"]) {
        op3 = await client3.operations().get(op3.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    op3 = await client3.oobis().resolve(oobi2.oobis[0],"member2")
    while (!op3["done"]) {
        op3 = await client3.operations().get(op3.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    console.log("Member3 resolved 2 OOBIs")
    
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

    await client1.exchanges().send("member1", "multisig", aid1, "/multisig/icp",
        {'gid': serder.pre, smids: smids, rmids: smids}, embeds, recp)
    console.log("Member1 initiated multisig, waiting for others to join...")

    // Second member check notifications and join the multisig  
    let msgSaid = ""
    while (msgSaid=="") {
        let notifications = await client2.notifications().list()
        for (let notif of notifications.notes){
            if (notif.a.r == '/multisig/icp') {
                msgSaid = notif.a.d
                await client2.notifications().mark(notif.i)
                console.log("Member2 received exchange message to join multisig")
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

    await client2.exchanges().send("member2", "multisig", aid2, "/multisig/icp",
        {'gid': serder.pre, smids: smids, rmids: smids}, embeds, recp)
    console.log("Member2 joined multisig, waiting for others...")


    // Third member check notifications and join the multisig  
    msgSaid = ""
    while (msgSaid=="") {
        let notifications = await client3.notifications().list()
        for (let notif of notifications.notes){
            if (notif.a.r == '/multisig/icp') {
                msgSaid = notif.a.d
                await client3.notifications().mark(notif.i)
                console.log("Member3 received exchange message to join multisig")
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

    await client3.exchanges().send("member3", "multisig", aid3, "/multisig/icp",
        {'gid': serder.pre, smids: smids, rmids: smids}, embeds, recp)
    console.log("Member3 joined, multisig waiting for others...")

    // Check for completion
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
    assert.equal(identifiers1.aids[0].name, "member1")
    assert.equal(identifiers1.aids[1].name, "multisig")

    const identifiers2 = await client2.identifiers().list()
    assert.equal(identifiers2.aids.length, 2)
    assert.equal(identifiers2.aids[0].name, "member2")
    assert.equal(identifiers2.aids[1].name, "multisig")

    const identifiers3 = await client3.identifiers().list()
    assert.equal(identifiers3.aids.length, 2)
    assert.equal(identifiers3.aids[0].name, "member3")
    assert.equal(identifiers3.aids[1].name, "multisig")

    console.log("Client 1 managed AIDs:", identifiers1.aids[0].name, identifiers1.aids[1].name)
    console.log("Client 2 managed AIDs:", identifiers2.aids[0].name, identifiers2.aids[1].name)
    console.log("Client 3 managed AIDs:", identifiers3.aids[0].name, identifiers3.aids[1].name)


    // MultiSig Interaction

    // Member1 initiates an interaction event
    let data = {"i": "EE77q3_zWb5ojgJr-R1vzsL5yiL4Nzm-bfSOQzQl02dy"}
    let eventResponse1 = await client1.identifiers().interact("multisig", data)
    op1 = await eventResponse1.op()
    serder = eventResponse1.serder
    sigs = eventResponse1.sigs
    sigers = sigs.map((sig: any) => new signify.Siger({qb64: sig}))

    ims = signify.d(signify.messagize(serder, sigers))
    atc = ims.substring(serder.size)
    let xembeds = {
        ixn: [serder, atc],
    }

    smids = states.map((state) =>  state['i'])
    recp = [aid2["state"], aid3["state"]].map((state) =>  state['i'])

    await client1.exchanges().send("member1", "multisig", aid1, "/multisig/ixn",
        {'gid': serder.pre, smids: smids, rmids: smids}, xembeds, recp)
    console.log("Member1 initiates interaction event, waiting for others to join...")

    // Member2 check for notifications and join the interaction event
    msgSaid = ""
    while (msgSaid=="") {
        let notifications = await client2.notifications().list()
        for (let notif of notifications.notes){
            if (notif.a.r == '/multisig/ixn') {
                msgSaid = notif.a.d
                await client2.notifications().mark(notif.i)
                console.log("Member2 received exchange message to join the interaction event")
            }
        }
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    res = await client2.groups().getRequest(msgSaid)
    exn = res[0].exn
    let ixn = exn.e.ixn
    data = ixn.a
    
    icpResult2 = await client2.identifiers().interact("multisig",data)
    op2 = await icpResult2.op()
    serder = icpResult2.serder
    sigs = icpResult2.sigs
    sigers = sigs.map((sig: any) => new signify.Siger({qb64: sig}))

    ims = signify.d(signify.messagize(serder, sigers))
    atc = ims.substring(serder.size)
    xembeds = {
        ixn: [serder, atc],
    }

    smids = exn.a.smids
    recp = [aid1["state"], aid3["state"]].map((state) =>  state['i'])

    await client2.exchanges().send("member2", "multisig", aid2, "/multisig/ixn",
        {'gid': serder.pre, smids: smids, rmids: smids}, xembeds, recp)
    console.log("Member2 joins interaction event, waiting for others...")

    // Member3 check for notifications and join the interaction event
    msgSaid = ""
    while (msgSaid=="") {
        let notifications = await client3.notifications().list()
        for (let notif of notifications.notes){
            if (notif.a.r == '/multisig/ixn') {
                msgSaid = notif.a.d
                await client3.notifications().mark(notif.i)
                console.log("Member3 received exchange message to join the interaction event")
            }
        }
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    res = await client3.groups().getRequest(msgSaid)
    exn = res[0].exn
    ixn = exn.e.ixn
    data = ixn.a
    
    icpResult3 = await client3.identifiers().interact("multisig",data)
    op3 = await icpResult3.op()
    serder = icpResult3.serder
    sigs = icpResult3.sigs
    sigers = sigs.map((sig: any) => new signify.Siger({qb64: sig}))

    ims = signify.d(signify.messagize(serder, sigers))
    atc = ims.substring(serder.size)
    xembeds = {
        ixn: [serder, atc],
    }

    smids = exn.a.smids
    recp = [aid1["state"], aid2["state"]].map((state) =>  state['i'])

    await client3.exchanges().send("member3", "multisig", aid3, "/multisig/ixn",
        {'gid': serder.pre, smids: smids, rmids: smids}, xembeds, recp)
    console.log("Member3 joins interaction event, waiting for others...")

    // Check for completion
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
    console.log("Multisig interaction completed!")

    // Members agree out of band to rotate keys
    console.log("Members agree out of band to rotate keys")
    icpResult1 = await client1.identifiers().rotate('member1')
    op1 = await icpResult1.op()
    while (!op1["done"]) {
        op1 = await client1.operations().get(op1.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    aid1 = await client1.identifiers().get("member1")

    console.log("Member1 rotated keys")
    icpResult2 = await client2.identifiers().rotate('member2')
    op2 = await icpResult2.op()
    while (!op2["done"]) {
        op2 = await client2.operations().get(op2.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    aid2 = await client2.identifiers().get("member2")
    console.log("Member2 rotated keys")
    icpResult3 = await client3.identifiers().rotate('member3')
    op3 = await icpResult3.op()
    while (!op3["done"]) {
        op3 = await client3.operations().get(op3.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    aid3 = await client3.identifiers().get("member3")
    console.log("Member3 rotated keys")
    
    // Update new key states
    op1 = await client1.keyStates().query(aid2.prefix,1)
    while (!op1["done"]) {
        op1 = await client1.operations().get(op1.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    let aid2State = op1["response"]
    op1 = await client1.keyStates().query(aid3.prefix,1)
    while (!op1["done"]) {
        op1 = await client1.operations().get(op1.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    let aid3State = op1["response"]

    op2 = await client2.keyStates().query(aid3.prefix,1)
    while (!op2["done"]) {
        op2 = await client2.operations().get(op2.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    op2 = await client2.keyStates().query(aid1.prefix,1)
    while (!op2["done"]) {
        op2 = await client2.operations().get(op2.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    let aid1State = op2["response"]

    op3 = await client3.keyStates().query(aid1.prefix,1)
    while (!op3["done"]) {
        op3 = await client3.operations().get(op3.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    op3 = await client3.keyStates().query(aid2.prefix,1)
    while (!op3["done"]) {
        op3 = await client3.operations().get(op3.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }

    rstates = [aid1State, aid2State, aid3State]
    states = rstates

    // Multisig Rotation

    // Member1 initiates a rotation event
    eventResponse1 = await client1.identifiers().rotate("multisig",{states: states,rstates: rstates})
    op1 = await eventResponse1.op()
    serder = eventResponse1.serder
    sigs = eventResponse1.sigs
    sigers = sigs.map((sig: any) => new signify.Siger({qb64: sig}))

    ims = signify.d(signify.messagize(serder, sigers))
    atc = ims.substring(serder.size)
    let rembeds = {
        rot: [serder, atc],
    }

    smids = states.map((state) =>  state['i'])
    recp = [aid2State, aid3State].map((state) =>  state['i'])

    await client1.exchanges().send("member1", "multisig", aid1 , "/multisig/rot",
        {'gid': serder.pre, smids: smids, rmids: smids}, rembeds, recp)
    console.log("Member1 initiates rotation event, waiting for others to join...")

    // Member2 check for notifications and join the rotation event
    msgSaid = ""
    while (msgSaid=="") {
        let notifications = await client2.notifications().list()
        for (let notif of notifications.notes){
            if (notif.a.r == '/multisig/rot') {
                msgSaid = notif.a.d
                await client2.notifications().mark(notif.i)
                console.log("Member2 received exchange message to join the rotation event")
            }
        }
        await new Promise(resolve => setTimeout(resolve, 1000));
    }

    await new Promise(resolve => setTimeout(resolve, 5000));
    res = await client2.groups().getRequest(msgSaid)
    exn = res[0].exn
    
    icpResult2 = await client2.identifiers().rotate("multisig",{states: states,rstates: rstates})
    op2 = await icpResult2.op()
    serder = icpResult2.serder
    sigs = icpResult2.sigs
    sigers = sigs.map((sig: any) => new signify.Siger({qb64: sig}))

    ims = signify.d(signify.messagize(serder, sigers))
    atc = ims.substring(serder.size)
    rembeds = {
        rot: [serder, atc],
    }

    smids = exn.a.smids
    recp = [aid1State, aid3State].map((state) =>  state['i'])

    await client2.exchanges().send("member2", "multisig", aid2, "/multisig/ixn",
        {'gid': serder.pre, smids: smids, rmids: smids}, rembeds, recp)
    console.log("Member2 joins rotation event, waiting for others...")

    // Member3 check for notifications and join the rotation event
    msgSaid = ""
    while (msgSaid=="") {
        let notifications = await client3.notifications().list(1)
        for (let notif of notifications.notes){
            if (notif.a.r == '/multisig/rot') {
                msgSaid = notif.a.d
                await client3.notifications().mark(notif.i)
                console.log("Member3 received exchange message to join the rotation event")
            }
        }
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    res = await client3.groups().getRequest(msgSaid)
    exn = res[0].exn
    
    icpResult3 = await client3.identifiers().rotate("multisig",{states: states,rstates: rstates})
    op3 = await icpResult3.op()
    serder = icpResult3.serder
    sigs = icpResult3.sigs
    sigers = sigs.map((sig: any) => new signify.Siger({qb64: sig}))

    ims = signify.d(signify.messagize(serder, sigers))
    atc = ims.substring(serder.size)
    rembeds = {
        rot: [serder, atc],
    }

    smids = exn.a.smids
    recp = [aid1State, aid2State].map((state) =>  state['i'])

    await client3.exchanges().send("member3", "multisig", aid3, "/multisig/ixn",
        {'gid': serder.pre, smids: smids, rmids: smids}, rembeds, recp)
    console.log("Member3 joins rotation event, waiting for others...")

    // Check for completion
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
    console.log("Multisig rotation completed!")
}