import {Habery} from "./habery";
import {Accountant} from "./accountant";
import {Client} from "./client";


export class Signify {
    private readonly _hby?: Habery
    private readonly _act?: Accountant
    private readonly _client?: Client
    constructor(url:string, name:string, passcode: string) {
    }
}