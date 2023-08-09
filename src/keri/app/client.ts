

/**
 * Client
 */
export class Client {
    private readonly _url: string

    constructor(url: string) {
        this._url = url
    }

    private url(path: string): string {
        let url = new URL(path, this._url)

        return url.href
    }

    /**
     * 
     * @param name 
     * @returns 
     */
    getAccount(name: string): Promise<Response> {
        let url = this.url(`/account/${name}`)
        let req = new Request(url, {method: "GET"})
        return fetch(req)
    }

    /**
     * 
     * @param name 
     * @param key 
     * @param ndig 
     * @returns 
     */
    createAccount(name: string, key: string, ndig: string): Promise<Response> {
        let url = this.url(`/account/${name}`)
        let body = {key, ndig}
        let req = new Request(url, {method: "POST", body: JSON.stringify(body)})
        return fetch(req)
    }
}