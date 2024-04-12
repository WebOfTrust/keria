import { Operation, SignifyClient } from 'signify-ts';
import { RetryOptions, retry } from './retry';

export function sleep(ms: number): Promise<void> {
    return new Promise((resolve) => {
        setTimeout(resolve, ms);
    });
}

/**
 * Assert that all operations were waited for.
 * <p>This is a postcondition check to make sure all long-running operations have been waited for
 * @see waitOperation
 */
export async function assertOperations(
    ...clients: SignifyClient[]
): Promise<void> {
    for (const client of clients) {
        const operations = await client.operations().list();
        expect(operations).toHaveLength(0);
    }
}

/**
 * Assert that all notifications were handled.
 * <p>This is a postcondition check to make sure all notifications have been handled
 * @see markNotification
 * @see markAndRemoveNotification
 */
export async function assertNotifications(
    ...clients: SignifyClient[]
): Promise<void> {
    for (const client of clients) {
        const res = await client.notifications().list();
        const notes = res.notes.filter((i: { r: boolean }) => i.r === false);
        expect(notes).toHaveLength(0);
    }
}

/**
 * Logs a warning for each un-handled notification.
 * <p>Replace warnNotifications with assertNotifications when test handles all notifications
 * @see assertNotifications
 */
export async function warnNotifications(
    ...clients: SignifyClient[]
): Promise<void> {
    let count = 0;
    for (const client of clients) {
        const res = await client.notifications().list();
        const notes = res.notes.filter((i: { r: boolean }) => i.r === false);
        if (notes.length > 0) {
            count += notes.length;
            console.warn('notifications', notes);
        }
    }
    expect(count).toBeGreaterThan(0); // replace warnNotifications with assertNotifications
}

/**
 * Poll for operation to become completed.
 * Removes completed operation
 */
export async function waitOperation<T = any>(
    client: SignifyClient,
    op: Operation<T> | string,
    signal?: AbortSignal
): Promise<Operation<T>> {
    if (typeof op === 'string') {
        op = await client.operations().get(op);
    }

    op = await client
        .operations()
        .wait(op, { signal: signal ?? AbortSignal.timeout(30000) });
    await deleteOperations(client, op);

    return op;
}

async function deleteOperations<T = any>(
    client: SignifyClient,
    op: Operation<T>
) {
    if (op.metadata?.depends) {
        await deleteOperations(client, op.metadata.depends);
    }

    await client.operations().delete(op.name);
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

/**
 * Mark notification as read.
 */
export async function markNotification(
    client: SignifyClient,
    note: Notification
): Promise<void> {
    await client.notifications().mark(note.i);
}

/**
 * Mark and remove notification.
 */
export async function markAndRemoveNotification(
    client: SignifyClient,
    note: Notification
): Promise<void> {
    try {
        await client.notifications().mark(note.i);
    } finally {
        await client.notifications().delete(note.i);
    }
}
