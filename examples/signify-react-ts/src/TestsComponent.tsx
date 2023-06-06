// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import { SignifyClient, ready, Serder } from "signify-ts";
import { Salty } from "./test_components/Salty";
import { Randy } from "./test_components/Randy";
export function TestsComponent() {

    return (
        <>
            < Salty />
            < Randy />
        </>
    )
}


