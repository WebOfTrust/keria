import {strict as assert} from "assert";
import {randomPasscode, randomNonce} from '../../src/keri/app/apping'
import libsodium from "libsodium-wrappers-sumo"

describe('Controller', () => {
    it('Random passcode', async () => {
        await libsodium.ready;
        let passcode = randomPasscode()
        assert.equal(passcode.length, 22)
    })

    it('Random nonce', async () => {
        await libsodium.ready;
        let nonce = randomNonce()
        assert.equal(nonce.length, 44)
    })



})