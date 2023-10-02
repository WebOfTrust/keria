import { strict as assert } from "assert"
import signify,{Serder} from "signify-ts"

const url = "http://127.0.0.1:3901"
const boot_url = "http://127.0.0.1:3903"

await run()

async function run() {
    await signify.ready()
    // Boot two clients
    const bran1 = signify.randomPasscode()
    const bran2 = signify.randomPasscode()
    const client1 = new signify.SignifyClient(url, bran1, signify.Tier.low, boot_url);
    const client2 = new signify.SignifyClient(url, bran2, signify.Tier.low, boot_url);
    await client1.boot()
    await client2.boot()
    await client1.connect()
    await client2.connect()
    const state1 = await client1.state()
    const state2 = await client2.state()
    console.log("Client 1 connected. Client AID:",state1.controller.state.i,"Agent AID: ", state1.agent.i)
    console.log("Client 2 connected. Client AID:",state2.controller.state.i,"Agent AID: ", state2.agent.i)

    // Generate challenge words
    const challenge1_small = await client1.challenges().generate(128)
    assert.equal(challenge1_small.words.length, 12)
    const challenge1_big = await client1.challenges().generate(256)
    assert.equal(challenge1_big.words.length, 24)

    // Create two identifiers, one for each client
    let icpResult1 = await client1.identifiers().create('alice',  {
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
    const aid1 = op1['response']
    await client1.identifiers().addEndRole("alice", 'agent', client1!.agent!.pre)
    console.log("Alice's AID:", aid1.i)

    let icpResult2 = await client2.identifiers().create('bob',  {
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
    const aid2 = op2['response']
    await client2.identifiers().addEndRole("bob", 'agent', client2!.agent!.pre)
    console.log("Bob's AID:", aid2.i)

    // Exchenge OOBIs
    let oobi1 = await client1.oobis().get("alice","agent")
    let oobi2 = await client2.oobis().get("bob","agent")
    
    op1 = await client1.oobis().resolve(oobi2.oobis[0],"bob")
    while (!op1["done"]) {
        op1 = await client1.operations().get(op1.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    console.log("Client 1 resolved Bob's OOBI")
    op2 = await client2.oobis().resolve(oobi1.oobis[0],"alice")
    while (!op2["done"]) {
        op2 = await client2.operations().get(op2.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    console.log("Client 2 resolved Alice's OOBI")

    // List Client 1 contacts
    let contacts1 = await client1.contacts().list()
    assert.equal(contacts1[0].alias,'bob')

    // Bob responds to Alice challenge
    await client2.challenges().respond('bob', aid1.i, challenge1_small.words)
    console.log("Bob responded to Alice challenge with signed words")

    // Alice verifies Bob's response
    op1 = await client1.challenges().verify('alice', aid2.i, challenge1_small.words)
    while (!op1["done"]) {
        op1 = await client1.operations().get(op1.name);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    console.log("Alice verified challenge response")

    //Alice mark response as accepted
    let exn = new Serder(op1.response.exn)
    op1 = await client1.challenges().responded('alice', aid2.i, exn.ked.d)
    console.log("Alice marked challenge response as accepted")
    
    // Check Bob's challenge in conctats
    contacts1 = await client1.contacts().list()
    console.log("Challenge authenticated")

}