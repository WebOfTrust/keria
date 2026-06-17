import { assert, expect } from 'vitest';
import { SignifyClient } from '#signify-ts';

export async function assertCredentialReadable(
    client: SignifyClient,
    said: string
) {
    const credential = await client.credentials().get(said);
    assert.strictEqual(credential.sad.d, said);
    assert(credential.iss, 'expected iss TEL event on readable credential');
    return credential;
}

export async function assertCredentialBroken(
    client: SignifyClient,
    said: string
) {
    await expect(client.credentials().get(said)).rejects.toThrow();
}

/** Raw KERIA GET /credentials/{said} — surfaces 500 when TEL iss is missing. */
export async function probeCredentialGet(
    client: SignifyClient,
    said: string
): Promise<Response> {
    return client.fetch(`/credentials/${said}`, 'GET', null);
}

export async function probeCredentialState(
    client: SignifyClient,
    said: string,
    label: string
) {
    const res = await probeCredentialGet(client, said);
    let detail: unknown;
    try {
        detail = res.ok ? await res.json() : await res.text();
    } catch {
        detail = null;
    }
    const hasIss =
        res.ok &&
        typeof detail === 'object' &&
        detail !== null &&
        'iss' in detail &&
        !!(detail as { iss?: unknown }).iss;
    return { label, said, ok: res.ok, status: res.status, hasIss, detail };
}
