import _sodium from 'libsodium-wrappers-sumo';

export const ready: () => Promise<void> = async () => {
    try {
        const b3 = await import('blake3/browser-async');
        await b3.default(
            'https://cdn.jsdelivr.net/npm/blake3@2.1.7/dist/wasm/web/blake3_js_bg.wasm'
        );
        await _sodium.ready;
    } catch (e) {
        await _sodium.ready;
    }
};
