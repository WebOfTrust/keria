import { Operation, SignifyClient } from 'signify-ts';
import { RetryOptions, retry } from './retry';

export function sleep(ms: number): Promise<void> {
    return new Promise((resolve) => {
        setTimeout(resolve, ms);
    });
}

/**
 * Poll for operation to become completed
 */
export async function waitOperation<T = any>(
    client: SignifyClient,
    op: Operation<T>,
    options: RetryOptions = {}
): Promise<Operation<T>> {
    return retry(async () => {
        op = await client.operations().get(op.name);

        if (op.done !== true) {
            throw new Error(`Operation ${op.name} not done`);
        }

        return op;
    }, options);
}

export async function resolveOobi(
    client: SignifyClient,
    oobi: string,
    alias?: string
) {
    const op = await client.oobis().resolve(oobi, alias);
    await waitOperation(client, op);
}

export interface Notification {
    i: string;
    dt: string;
    r: boolean;
    a: { r: string; d?: string; m?: string };
}

export async function waitForNotifications(
    client: SignifyClient,
    route: string,
    options: RetryOptions = {}
): Promise<Notification[]> {
    return retry(async () => {
        const response: { notes: Notification[] } = await client
            .notifications()
            .list();

        const notes = response.notes.filter(
            (note) => note.a.r === route && note.r === false
        );

        if (!notes.length) {
            throw new Error(`No notifications with route ${route}`);
        }

        return notes;
    }, options);
}
