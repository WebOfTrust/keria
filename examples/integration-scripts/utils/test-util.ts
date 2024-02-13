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
    for (let client of clients) {
        let operations = await client.operations().list();
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
    for (let client of clients) {
        let res = await client.notifications().list();
        let notes = res.notes.filter((i: any) => i.r === false);
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
    for (let client of clients) {
        let res = await client.notifications().list();
        let notes = res.notes.filter((i: any) => i.r === false);
        if (notes.length > 0) {
            count += notes.length;
            console.warn('notifications', notes);
        }
    }
    expect(count).toBeGreaterThan(0); // replace warnNotifications with assertNotifications
}

/**
 * Get status of operation.
 * If parameter recurse is set then also checks status of dependent operations.
 */
async function getOperation<T>(
    client: SignifyClient,
    name: string,
    recurse?: boolean
): Promise<Operation<T>> {
    const result = await client.operations().get<T>(name);
    if (recurse === true) {
        let i: Operation | undefined = result;
        while (result.done && i?.metadata?.depends !== undefined) {
            let depends: Operation = await client
                .operations()
                .get(i.metadata.depends.name);
            result.done = result.done && depends.done;
            i.metadata.depends = depends;
            i = depends.metadata?.depends;
        }
    }
    return result;
}

/**
 * Poll for operation to become completed.
 * Removes completed operation
 */
export async function waitOperation<T = any>(
    client: SignifyClient,
    op: Operation<T> | string,
    options: RetryOptions = {}
): Promise<Operation<T>> {
    const ctrl = new AbortController();
    options.signal?.addEventListener('abort', (e: Event) => {
        const s = e.target as AbortSignal;
        ctrl.abort(s.reason);
    });
    let name: string;
    if (typeof op === 'string') {
        name = op;
    } else if (typeof op === 'object' && 'name' in op) {
        name = op.name;
    } else {
        throw new Error();
    }
    const result: Operation<T> = await retry(async () => {
        let t: Operation<T>;
        try {
            t = await getOperation<T>(client, name, true);
        } catch (e) {
            ctrl.abort(e);
            throw e;
        }
        if (t.done !== true) {
            throw new Error(`Operation ${name} not done`);
        }
        console.log('DONE', name);
        return t;
    }, options);
    let i: Operation | undefined = result;
    while (i !== undefined) {
        // console.log('DELETE', i.name);
        await client.operations().delete(i.name);
        i = i.metadata?.depends;
    }
    return result;
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
