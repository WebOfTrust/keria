export type TestEnvironmentPreset = 'local' | 'docker';

export interface TestEnvironment {
    preset: TestEnvironmentPreset;
    url: string;
    bootUrl: string;
    vleiServerUrl: string;
    witnessUrls: string[];
    witnessIds: string[];
}

const WAN = 'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha';
const WIL = 'BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM';
const WES = 'BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX';

export function resolveEnvironment(
    input?: TestEnvironmentPreset
): TestEnvironment {
    const preset = input ?? process.env.TEST_ENVIRONMENT ?? 'docker';

    const url = 'http://127.0.0.1:3901';
    const bootUrl = 'http://127.0.0.1:3903';

    switch (preset) {
        case 'docker':
            return {
                preset: preset,
                url,
                bootUrl,
                witnessUrls: [
                    'http://witness-demo:5642',
                    'http://witness-demo:5643',
                    'http://witness-demo:5644',
                ],
                witnessIds: [WAN, WIL, WES],
                vleiServerUrl: 'http://vlei-server:7723',
            };
        case 'local':
            return {
                preset: preset,
                url,
                bootUrl,
                vleiServerUrl: 'http://localhost:7723',
                witnessUrls: [
                    'http://localhost:5642',
                    'http://localhost:5643',
                    'http://localhost:5644',
                ],
                witnessIds: [WAN, WIL, WES],
            };
        default:
            throw new Error(`Unknown test environment preset '${preset}'`);
    }
}
