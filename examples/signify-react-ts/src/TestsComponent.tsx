// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import { SignifyClient, ready, Serder } from "signify-ts";
import { Salty } from "./test_components/Salty";
import { Randy } from "./test_components/Randy";
import { Delegation } from "./test_components/Delegation";
import { Witnesses } from "./test_components/Witnesses";
import { Multisig } from "./test_components/Multisig";
import { Credentials } from "./test_components/Credentials";
import { Challenges } from "./test_components/Challenges";
import { Rotation } from "./test_components/Rotation";
export function TestsComponent() {

    return (
        <>
            < Rotation />
            < Challenges />
            < Credentials />
            < Salty />
            < Randy />
            < Witnesses />
            < Delegation />
            < Multisig />
        </>
    )
}


