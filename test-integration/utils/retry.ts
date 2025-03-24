import { setTimeout } from 'timers/promises';

export interface RetryOptions {
    maxSleep?: number;
    minSleep?: number;
    maxRetries?: number;
    timeout?: number;
    signal?: AbortSignal;
}

export async function retry<T>(
    fn: () => Promise<T>,
    options: RetryOptions = {}
): Promise<T> {
    const {
        maxSleep = 1000,
        minSleep = 10,
        maxRetries,
        timeout = 10000,
    } = options;

    const increaseFactor = 50;

    let retries = 0;
    let cause: Error | null = null;
    const start = Date.now();

    while (
        (options.signal === undefined || options.signal.aborted === false) &&
        Date.now() - start < timeout &&
        (maxRetries === undefined || retries < maxRetries)
    ) {
        try {
            const result = await fn();
            return result;
        } catch (err) {
            cause = err as Error;
            const delay = Math.max(
                minSleep,
                Math.min(maxSleep, 2 ** retries * increaseFactor)
            );
            retries++;
            await setTimeout(delay, undefined, { signal: options.signal });
        }
    }

    if (!cause) {
        cause = new Error(`Failed after ${retries} attempts`);
    }

    Object.assign(cause, { retries, maxAttempts: maxRetries });
    throw cause;
}
