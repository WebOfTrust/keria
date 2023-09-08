import {strict as assert} from "assert";
import {randomPasscode, randomNonce} from '../../src/keri/app/apping'
import libsodium from "libsodium-wrappers-sumo"
import {CreateIdentiferArgs, RotateIdentifierArgs} from "../../src/keri/app/signify";

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

    it('CreateIdentiferArgs', () => {
        let args: CreateIdentiferArgs;
        args = {
            isith: 1,
            nsith: 1
        };
        args = {
            isith: "1",
            nsith: "1"
        };
        args = {
            isith: ["1"],
            nsith: ["1"]
        };
    })

    it('RotateIdentifierArgs', () => {
        let args: RotateIdentifierArgs;
        args = {
            nsith: 1
        };
        args = {
            nsith: "1"
        };
        args = {
            nsith: ["1"]
        };
    })


})