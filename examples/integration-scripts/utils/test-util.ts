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

export interface WaitOptions {
    timeout?: number;
}

/**
 * Retry fn until timeout, throws the last caught excetion after timeout passed
 */
export async function wait<T>(
    fn: () => Promise<T>,
    options: WaitOptions = {}
): Promise<T> {
    const start = Date.now();
    const timeout = options.timeout ?? 10000;
    let error: Error | null = null;

    while (Date.now() - start < timeout) {
        try {
            const result = await fn();
            return result;
        } catch (err) {
            error = err as Error;
            if (Date.now() - start < timeout) {
                await new Promise((resolve) => setTimeout(resolve, 1000));
            }
        }
    }

    if (error) {
        throw error;
    } else {
        throw new Error(`Timeout after ${Date.now() - start}ms`);
    }
}
