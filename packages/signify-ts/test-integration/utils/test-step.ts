/**
 * Provides a way to group logically related test steps in an integration test
 *
 * Can be useful to provide logging when a step succeeds, or to be able to use
 * locally scoped variables.
 *
 * In long tests it can also be useful to create visual groups.
 * @param description
 * @param fn
 * @returns
 */
export async function step<T>(
    description: string,
    fn: () => Promise<T>
): Promise<T> {
    try {
        const start = Date.now();
        const response = await fn();

        // Bypassing console.log to avoid the verbose log output from test runner
        process.stdout.write(
            `Step - ${description} - finished (${Date.now() - start}ms)\n`
        );
        return response;
    } catch (error) {
        throw new Error(`Step - ${description} - failed`, { cause: error });
    }
}
