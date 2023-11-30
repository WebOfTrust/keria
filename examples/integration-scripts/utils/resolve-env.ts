export type TestEnvironmentPreset = 'local' | 'docker';

export interface TestEnvironment {
    url: string;
    bootUrl: string;
    vleiServerUrl: string;
    witnessUrls: string[];
}

export function resolveEnvironment(
    input?: TestEnvironmentPreset
): TestEnvironment {
    const preset = input ?? process.env.TEST_ENVIRONMENT ?? 'docker';

    const url = 'http://127.0.0.1:3901';
    const bootUrl = 'http://127.0.0.1:3903';

    switch (preset) {
        case 'docker':
            return {
                url,
                bootUrl,
                witnessUrls: [
                    'http://witness-demo:5642',
                    'http://witness-demo:5643',
                    'http://witness-demo:5644',
                ],
                vleiServerUrl: 'http://vlei-server:7723',
            };
        case 'local':
            return {
                url,
                bootUrl,
                vleiServerUrl: 'http://localhost:7723',
                witnessUrls: [
                    'http://localhost:5642',
                    'http://localhost:5643',
                    'http://localhost:5644',
                ],
            };
        default:
            throw new Error(`Unknown test environment preset '${preset}'`);
    }
}
