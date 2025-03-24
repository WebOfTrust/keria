// @ts-check

import eslint from '@eslint/js';
import tseslint from 'typescript-eslint';
import prettier from 'eslint-config-prettier';

export default tseslint.config(
    eslint.configs.recommended,
    tseslint.configs.recommended,
    { rules: prettier.rules },
    {
        // These are files with more lenient lint config because they have not been "fixed" yet
        // Once a directory here is fixed, it should be removed from here so the strict rules applies
        files: ['src/keri/app/**', 'src/keri/core/**', 'test-integration/**'],
        rules: {
            'prefer-const': 'warn',
            'no-var': 'warn',
            'no-self-assign': 'warn',
            'no-case-declarations': 'warn',
            'no-constant-condition': 'warn',
            'no-empty': 'warn',
            '@typescript-eslint/no-non-null-asserted-optional-chain': 'warn',
            '@typescript-eslint/no-explicit-any': 'warn',
            '@typescript-eslint/no-namespace': 'warn',
            // '@typescript-eslint/ban-types': 'warn',
            '@typescript-eslint/no-unused-vars': 'warn',
        },
    }
);
