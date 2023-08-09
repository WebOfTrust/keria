

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
     * getAccount
     * @param {string} name 
     * @returns {Promise<Response>}
     */
    getAccount(name: string): Promise<Response> {
        let url = this.url(`/account/${name}`)
        let req = new Request(url, {method: "GET"})
        return fetch(req)
    }

    /**
     * createAccount
     * @param {string} name 
     * @param {string} key 
     * @param {string} ndig 
     * @returns {Promise<Response>}
     */
    createAccount(name: string, key: string, ndig: string): Promise<Response> {
        let url = this.url(`/account/${name}`)
        let body = {key, ndig}
        let req = new Request(url, {method: "POST", body: JSON.stringify(body)})
        return fetch(req)
    }
}