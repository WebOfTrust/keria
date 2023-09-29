import libsodium from "libsodium-wrappers-sumo";
import { vdr } from "../../src/keri/core/vdring";
import { strict as assert } from "assert";

describe('vdr', () => {
    it('should create registry inception events ', async () => {
        await libsodium.ready;
        let actual = vdr.incept({ pre: "ECJIoBpEcCWMzvquk861dXP8JJZ-vbmJczlDR-NYcE3g", toad: 0 });
        assert.equal(actual.pre.length, 44);

        actual = vdr.incept({ pre: "ECJIoBpEcCWMzvquk861dXP8JJZ-vbmJczlDR-NYcE3g", toad: 0, nonce: "AHSNDV3ABI6U8OIgKaj3aky91ZpNL54I5_7-qwtC6q2s" });
        assert.equal(actual.pre, "EDAsrwU75uoh8sii7w-KN-Txy2d0dhHiUP34TQVBJiPS");
        assert.equal(actual.code, "E");
        assert.equal(actual.raw,
            '{"v":"KERI10JSON00010f_","t":"vcp","d":"EDAsrwU75uoh8sii7w-KN-Txy2d0dhHiUP34TQVBJiPS","i":"EDAsrwU75uoh8sii7w-KN-Txy2d0dhHiUP34TQVBJiPS","ii":"ECJIoBpEcCWMzvquk861dXP8JJZ-vbmJczlDR-NYcE3g","s":"0","c":[],"bt":"0","b":[],"n":"AHSNDV3ABI6U8OIgKaj3aky91ZpNL54I5_7-qwtC6q2s"}');
        assert.equal(actual.size, 271);
    });

    it('should fail on NB config with backers', async () => {
        await libsodium.ready;
        let cnfg = ["NB"];
        assert.throws(() => {
            vdr.incept({
                pre: "ECJIoBpEcCWMzvquk861dXP8JJZ-vbmJczlDR-NYcE3g", toad: 0, nonce: "AHSNDV3ABI6U8OIgKaj3aky91ZpNL54I5_7-qwtC6q2s",
                cnfg: cnfg, baks: ["a backer"]
            })
        },
            {
                name: 'Error',
                message: '1 backers specified for NB vcp, 0 allowed',
            });
    });

    it('should fail with duplicate backers', async () => {
        await libsodium.ready;
        assert.throws(() => {
            vdr.incept({
                pre: "ECJIoBpEcCWMzvquk861dXP8JJZ-vbmJczlDR-NYcE3g", toad: 0, nonce: "AHSNDV3ABI6U8OIgKaj3aky91ZpNL54I5_7-qwtC6q2s",
                baks: ["a backer", "a backer"]
            })
        },
            {
                name: 'Error',
                message: 'Invalid baks a backer,a backer has duplicates',
            });
    });


    it('should fail with invalid toad config for backers', async () => {
        await libsodium.ready;
        assert.throws(() => {
            vdr.incept({
                pre: "ECJIoBpEcCWMzvquk861dXP8JJZ-vbmJczlDR-NYcE3g", toad: 0, nonce: "AHSNDV3ABI6U8OIgKaj3aky91ZpNL54I5_7-qwtC6q2s",
                baks: ["a backer"]
            })
        },
            {
                name: 'Error',
                message: 'Invalid toad 0 for baks in a backer',
            });
    });

    it('should fail with invalid toad for no backers', async () => {
        await libsodium.ready;
        assert.throws(() => {
            vdr.incept({ pre: "ECJIoBpEcCWMzvquk861dXP8JJZ-vbmJczlDR-NYcE3g", toad: 1, nonce: "AHSNDV3ABI6U8OIgKaj3aky91ZpNL54I5_7-qwtC6q2s" })
        },
            {
                name: 'Error',
                message: 'Invalid toad 1 for no baks',
            });
    });

    it('should allow optional toad and no backers', async () => {
        await libsodium.ready;
        let actual = vdr.incept({ pre: "ECJIoBpEcCWMzvquk861dXP8JJZ-vbmJczlDR-NYcE3g", nonce: "AHSNDV3ABI6U8OIgKaj3aky91ZpNL54I5_7-qwtC6q2s" });

        assert.equal(actual.pre, "EDAsrwU75uoh8sii7w-KN-Txy2d0dhHiUP34TQVBJiPS");
        assert.equal(actual.code, "E");
        assert.equal(actual.raw,
            '{"v":"KERI10JSON00010f_","t":"vcp","d":"EDAsrwU75uoh8sii7w-KN-Txy2d0dhHiUP34TQVBJiPS","i":"EDAsrwU75uoh8sii7w-KN-Txy2d0dhHiUP34TQVBJiPS","ii":"ECJIoBpEcCWMzvquk861dXP8JJZ-vbmJczlDR-NYcE3g","s":"0","c":[],"bt":"0","b":[],"n":"AHSNDV3ABI6U8OIgKaj3aky91ZpNL54I5_7-qwtC6q2s"}');
        assert.equal(actual.size, 271);
    });

    it('should allow optional toad and backers', async () => {
        await libsodium.ready;
        let actual = vdr.incept({ pre: "ECJIoBpEcCWMzvquk861dXP8JJZ-vbmJczlDR-NYcE3g", nonce: "AHSNDV3ABI6U8OIgKaj3aky91ZpNL54I5_7-qwtC6q2s", baks: ["a backer"]});

        assert.equal(actual.pre, "ELdKGV_ojDYC47GVHBRakgib5LJQLKcA72oAMUF5Jsou");
        assert.equal(actual.code, "E");
        assert.equal(actual.raw,
            '{"v":"KERI10JSON000119_","t":"vcp","d":"ELdKGV_ojDYC47GVHBRakgib5LJQLKcA72oAMUF5Jsou","i":"ELdKGV_ojDYC47GVHBRakgib5LJQLKcA72oAMUF5Jsou","ii":"ECJIoBpEcCWMzvquk861dXP8JJZ-vbmJczlDR-NYcE3g","s":"0","c":[],"bt":"0","b":["a backer"],"n":"AHSNDV3ABI6U8OIgKaj3aky91ZpNL54I5_7-qwtC6q2s"}');
        assert.equal(actual.size, 281);
    });
});
