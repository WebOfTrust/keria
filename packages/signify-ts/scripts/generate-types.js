import path from 'node:path';
import { writeFile } from 'node:fs/promises';
import openapiTS, { astToString } from 'openapi-typescript';
import { isInterfaceDeclaration, isEnumDeclaration } from 'typescript';

const specUrl = process.env.SPEC_URL || 'http://localhost:3902/spec.yaml';
const outputFile = path.resolve('src/types/keria-api-schema.ts');

console.log(`📦 Generating types from ${specUrl}`);
const ast = await openapiTS(new URL(specUrl), {
    enum: true,
    rootTypes: false,
});

// Filter to keep components interface, enums
const content = ast.filter((s) => {
    // Keep enum declarations
    if (isEnumDeclaration(s)) {
        return true;
    }

    // Keep components interface
    if (isInterfaceDeclaration(s) && s.name.text === 'components') {
        return true;
    }

    return false;
});

const header = `// AUTO-GENERATED: Only components retained from OpenAPI schema\n\n`;
await writeFile(outputFile, `${header}${astToString(content)}`);

console.log(`🚀 ${specUrl} → ${outputFile}`);
