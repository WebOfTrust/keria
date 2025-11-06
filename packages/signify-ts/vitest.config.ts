import { defineConfig } from 'vitest/config';

export default defineConfig({
    test: {
        name: 'Unit tests',
        root: 'test',
        testTimeout: 10000,
    },
});
