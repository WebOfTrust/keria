import { Operation, SignifyClient } from 'signify-ts';

export function sleep(ms: number): Promise<void> {
    return new Promise((resolve) => {
        setTimeout(resolve, ms);
    });
}

/**
 * Poll for operation to become completed
 */
export async function waitOperation<T>(
    client: SignifyClient,
    op: Operation<T>,
    retries: number = 10
): Promise<Operation<T>> {
    const WAIT = 500; // 0.5 seconds
    while (retries-- > 0) {
        op = await client.operations().get(op.name);
        if (op.done === true) return op;
        await sleep(WAIT);
    }
    throw new Error(`Timeout: operation ${op.name}`);
}

export async function resolveOobi(
    client: SignifyClient,
    oobi: string,
    alias: string
) {
    const op = await client.oobis().resolve(oobi, alias);
    await waitOperation(client, op);
}
