export interface TestEnvironment {
    url: string;
    bootUrl: string;
    vleiServerUrl: string;
    witnessUrls: string[];
    witnessIds: string[];
}

const WAN = 'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha';
const WIL = 'BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM';
const WES = 'BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX';

export function resolveEnvironment(): TestEnvironment {
    const url = 'http://127.0.0.1:3901';
    const bootUrl = 'http://127.0.0.1:3903';

    return {
        url,
        bootUrl,
        vleiServerUrl: 'http://127.0.0.1:7723',
        witnessUrls: [
            'http://127.0.0.1:5642',
            'http://127.0.0.1:5643',
            'http://127.0.0.1:5644',
        ],
        witnessIds: [WAN, WIL, WES],
    };
}
