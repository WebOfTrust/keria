import { SignifyClient } from "signify-ts";

export function sleep(ms: number): Promise<void> {
    return new Promise(resolve => {
        setTimeout(resolve, ms);
    });
}

/**
 * Poll for operation to become completed
 */
export async function waitOperation(client: SignifyClient, op: any, retries: number | undefined = undefined): Promise<any> {
    const WAIT = 500; // 0.5 seconds
    retries ??= 10; // default 10 retries or 5 seconds
    while (retries-- > 0) {
        op = await client.operations().get(op.name);
        if (op.done === true) return op;
        await sleep(WAIT);
    }
    throw new Error(`Timeout: operation ${op.name}`);
}
