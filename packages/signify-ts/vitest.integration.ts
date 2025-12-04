import { defineConfig } from 'vitest/config';
import tsconfig from 'vite-tsconfig-paths';

export default defineConfig({
    plugins: [tsconfig()],
    test: {
        fileParallelism: false,
        name: 'Integration tests',
        root: 'test-integration',
        bail: 1,
        testTimeout: 60000,
        watch: false,
    },
});
