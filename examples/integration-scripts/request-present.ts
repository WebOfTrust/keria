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


    // Create two identifiers, one for each client
    let op1 = await client1.identifiers().create('issuer',  {
        toad: 3,
        wits: [
            "BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
            "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
            "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"]
        })
    while (!op1["done"] ) {
            op1 = await client1.operations().get(op1.name);
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    const aid1 = await client1.identifiers().get("issuer")
    await client1.identifiers().addEndRole("issuer", 'agent', client1!.agent!.pre)
    console.log("Issuer's AID:", aid1.prefix)

    let op2 = await client2.identifiers().create('recipient',  {
        toad: 3,
        wits: [
            "BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
            "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
            "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"]
        })
    while (!op2["done"] ) {
            op2 = await client2.operations().get(op2.name);
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    const aid2 = await client2.identifiers().get("recipient")
    await client2.identifiers().addEndRole("recipient", 'agent', client2!.agent!.pre)
    console.log("Recipient's AID:", aid2.prefix)

    let op3 = await client3.identifiers().create('verifier',  {
        toad: 3,
        wits: [
            "BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
            "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
            "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"]
        })
    while (!op3["done"] ) {
            op3 = await client3.operations().get(op3.name);
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    const aid3 = await client3.identifiers().get("verifier")
    await client3.identifiers().addEndRole("verifier", 'agent', client3!.agent!.pre)
    console.log("Verifier's AID:", aid3.prefix)

    const schemaSAID = "EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao"

    // Exchenge OOBIs
    console.log("Resolving OOBIs...")
    let oobi1 = await client1.oobis().get("issuer","agent")
    let oobi2 = await client2.oobis().get("recipient","agent")
    let oobi3 = await client3.oobis().get("verifier","agent")
    let schemaOobi = "http://127.0.0.1:7723/oobi/" + schemaSAID
    
    op1 = await client1.oobis().resolve(oobi2.oobis[0],"recipient")
    while (!op1["done"]) {
        op1 = await client1.operations().get(op1.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    op1 = await client1.oobis().resolve(oobi3.oobis[0],"verifier")
    while (!op1["done"]) {
        op1 = await client1.operations().get(op1.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    op1 = await client1.oobis().resolve(schemaOobi,"schema")
    while (!op1["done"]) {
        op1 = await client1.operations().get(op1.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    console.log("Issuer resolved 3 OOBIs")
    
    op2 = await client2.oobis().resolve(oobi1.oobis[0],"issuer")
    while (!op2["done"]) {
        op2 = await client2.operations().get(op2.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    op2 = await client2.oobis().resolve(oobi3.oobis[0],"verifier")
    while (!op2["done"]) {
        op2 = await client2.operations().get(op2.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    op2 = await client2.oobis().resolve(schemaOobi,"schema")
    while (!op2["done"]) {
        op2 = await client2.operations().get(op2.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    console.log("Recipient resolved 3 OOBIs")

    op3 = await client3.oobis().resolve(oobi1.oobis[0],"issuer")
    while (!op3["done"]) {
        op3 = await client3.operations().get(op3.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    op3 = await client3.oobis().resolve(oobi2.oobis[0],"recipient")
    while (!op3["done"]) {
        op3 = await client3.operations().get(op3.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    op3 = await client3.oobis().resolve(schemaOobi,"schema")
    while (!op3["done"]) {
        op3 = await client3.operations().get(op3.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    console.log("Verifier resolved 3 OOBIs")

    // Create registry for issuer
    op1 = await client1.registries().create('issuer','vLEI')
    while (!op1["done"]) {
        op1 = await client1.operations().get(op1.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    let registries = await client1.registries().list('issuer')
    assert.equal(registries.length, 1)
    assert.equal(registries[0].name, 'vLEI')
    let schema = await client1.schemas().get(schemaSAID)
    assert.equal(schema.$id, schemaSAID)
    let schemas = await client2.schemas().list()
    assert.equal(schemas.length, 1)
    assert.equal(schemas[0].$id, schemaSAID)
    console.log("Registry created")

    // Issue credential
    const vcdata = {
        "LEI": "5493001KJTIIGC8Y1R17"
      }
    op1 = await client1.credentials().issue('issuer',registries[0].regk, schemaSAID,aid2.prefix,vcdata)
    while (!op1["done"]) {
        op1 = await client1.operations().get(op1.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    let creds1 = await client1.credentials().list('issuer')
    assert.equal(creds1.length, 1)
    assert.equal(creds1[0].sad.s, schemaSAID)
    assert.equal(creds1[0].sad.i, aid1.prefix)
    assert.equal(creds1[0].status.s, "0") // 0 = issued
    console.log("Credential issued")

    // Recipient check issued credential
    let creds2 = await client2.credentials().list('recipient')
    assert.equal(creds2.length, 1)
    assert.equal(creds2[0].sad.s, schemaSAID)
    assert.equal(creds2[0].sad.i, aid1.prefix)
    assert.equal(creds2[0].status.s, "0") // 0 = issued
    console.log("Credential received by recipient")

    // Verifier request credential to recipient
    await client3.credentials().request('verifier', aid2.prefix, schemaSAID)

    // Recipient checks for a presentation request notification
    let requestReceived = false
    while (!requestReceived) {
        let notifications = await client2.notifications().list()
        for (let notif of notifications){
            if (notif.a.r == '/presentation/request') {
                assert.equal(notif.a.schema.n, schemaSAID)
                requestReceived = true
                await client2.notifications().mark(notif.i)
            }
        }
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    // Recipient present credential to verifier
    await client1.credentials().present('issuer', creds1[0].sad.d, 'verifier', true)

    // Verifier checks for a presentation notification
    requestReceived = false
    while (!requestReceived) {
        let notifications = await client3.notifications().list()
        for (let notif of notifications){
            if (notif.a.r == '/presentation') {
                assert.equal(notif.a.schema.n, schemaSAID)
                requestReceived = true
                await client3.notifications().mark(notif.i)
            }
        }
        await new Promise(resolve => setTimeout(resolve, 1000));
    }

    let creds3 = await client3.credentials().list('verifier',{filter:{"-i": {"$eq": aid1.prefix}}}) // filter by issuer
    assert.equal(creds3.length, 1)
    assert.equal(creds3[0].sad.s, schemaSAID)
    assert.equal(creds3[0].sad.i, aid1.prefix)
    assert.equal(creds3[0].status.s, "0") // 0 = issued
    assert.equal(creds3[0].sad.a.i, aid2.prefix) // verify that the issuee is the same as the presenter
    console.log("Credential presented and received by verifier")



}