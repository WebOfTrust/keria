import _sodium from 'libsodium-wrappers-sumo';

export const ready: () => Promise<void> = async () => {
    await _sodium.ready;
};
