import path from 'node:path';
import { writeFile } from 'node:fs/promises';
import openapiTS, { astToString } from 'openapi-typescript';
import { isInterfaceDeclaration } from 'typescript';

const specUrl = process.env.SPEC_URL || 'http://localhost:3902/spec.yaml';
const outputFile = path.resolve('src/types/keria-api-schema.ts');

console.log(`📦 Generating types from ${specUrl}`);
const ast = await openapiTS(new URL(specUrl), { rootTypes: true });
const content = ast.filter(
    (s) => isInterfaceDeclaration(s) && s.name.text === 'components'
);

const header = `// AUTO-GENERATED: Only components retained from OpenAPI schema\n\n`;
await writeFile(outputFile, `${header}${astToString(content)}`);

console.log(`🚀 ${specUrl} → ${outputFile}`);
