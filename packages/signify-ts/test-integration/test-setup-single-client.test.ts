import { SignifyClient } from 'signify-ts';
import { resolveEnvironment } from './utils/resolve-env.ts';
import {
    assertOperations,
    getOrCreateClients,
    getOrCreateIdentifier,
} from './utils/test-util.ts';
import { afterAll, assert, beforeAll, describe, test } from 'vitest';

let client: SignifyClient;
let name1_id: string, name1_oobi: string;

beforeAll(async () => {
    // Create client with pre-defined secret. Allows working with known identifiers
    [client] = await getOrCreateClients(1, ['0ADF2TpptgqcDE5IQUF1HeTp']);
    [name1_id, name1_oobi] = await getOrCreateIdentifier(client, 'name1');
});

afterAll(async () => {
    await assertOperations(client);
});

describe('test-setup-single-client', () => {
    test('step1', async () => {
        assert.equal(
            client.controller?.pre,
            'EB3UGWwIMq7ppzcQ697ImQIuXlBG5jzh-baSx-YG3-tY'
        );
    });

    test('step2', async () => {
        const env = resolveEnvironment();
        const oobi = await client.oobis().get('name1', 'witness');
        assert.strictEqual(oobi.oobis.length, 3);
        switch (env.preset) {
            case 'local':
                assert.equal(
                    name1_oobi,
                    `http://127.0.0.1:3902/oobi/${name1_id}/agent/${client.agent?.pre}`
                );
                assert.equal(
                    oobi.oobis[0],
                    `http://127.0.0.1:5642/oobi/${name1_id}/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha`
                );
                assert.equal(
                    oobi.oobis[1],
                    `http://127.0.0.1:5643/oobi/${name1_id}/witness/BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM`
                );
                assert.equal(
                    oobi.oobis[2],
                    `http://127.0.0.1:5644/oobi/${name1_id}/witness/BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX`
                );
                break;
            case 'docker':
                assert.equal(
                    name1_oobi,
                    `http://keria:3902/oobi/${name1_id}/agent/${client.agent?.pre}`
                );
                assert.equal(
                    oobi.oobis[0],
                    `http://witness-demo:5642/oobi/${name1_id}/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha`
                );
                assert.equal(
                    oobi.oobis[1],
                    `http://witness-demo:5643/oobi/${name1_id}/witness/BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM`
                );
                assert.equal(
                    oobi.oobis[2],
                    `http://witness-demo:5644/oobi/${name1_id}/witness/BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX`
                );
                break;
        }
    });

    test('validate config', async () => {
        const env = resolveEnvironment();
        const config = await client.config().get();
        switch (env.preset) {
            case 'local':
                assert.deepEqual(config, {
                    iurls: [
                        'http://127.0.0.1:5642/oobi/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha/controller?name=Wan&tag=witness',
                        'http://127.0.0.1:5643/oobi/BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM/controller?name=Wes&tag=witness',
                        'http://127.0.0.1:5644/oobi/BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX/controller?name=Wil&tag=witness',
                    ],
                });
                break;
            case 'docker':
                assert.deepEqual(config, {
                    iurls: [
                        'http://witness-demo:5642/oobi/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha/controller',
                        'http://witness-demo:5643/oobi/BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM/controller',
                        'http://witness-demo:5644/oobi/BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX/controller',
                        'http://witness-demo:5645/oobi/BM35JN8XeJSEfpxopjn5jr7tAHCE5749f0OobhMLCorE/controller',
                        'http://witness-demo:5646/oobi/BIj15u5V11bkbtAxMA7gcNJZcax-7TgaBMLsQnMHpYHP/controller',
                        'http://witness-demo:5647/oobi/BF2rZTW79z4IXocYRQnjjsOuvFUQv-ptCf8Yltd7PfsM/controller',
                    ],
                });
                break;
        }
    });
});
