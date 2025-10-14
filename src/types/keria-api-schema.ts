// AUTO-GENERATED: Only components retained from OpenAPI schema

export interface components {
    schemas: {
        ACDCAttributes: {
            dt?: string;
            i?: string;
            u?: string;
        } & {
            [key: string]: unknown;
        };
        ACDC_V_1:
            | {
                  v: string;
                  d: string;
                  i: string;
                  s: string;
                  u?: string;
                  ri?: string;
                  e?: string;
                  r?: string;
                  a?: components['schemas']['ACDCAttributes'];
              }
            | {
                  v: string;
                  d: string;
                  i: string;
                  s: string;
                  u?: string;
                  ri?: string;
                  e?: string;
                  r?: string;
                  A?: string | unknown[];
              };
        ACDC_V_2:
            | {
                  v: string;
                  d: string;
                  i: string;
                  s: string;
                  u?: string;
                  rd?: string;
                  e?: string;
                  r?: string;
                  a?: components['schemas']['ACDCAttributes'];
              }
            | {
                  v: string;
                  d: string;
                  i: string;
                  s: string;
                  u?: string;
                  rd?: string;
                  e?: string;
                  r?: string;
                  A?: string | unknown[];
              };
        IssEvent: {
            v: string;
            /** @enum {unknown} */
            t: 'iss' | 'bis';
            d: string;
            i: string;
            s: string;
            ri: string;
            dt: string;
        };
        Schema: {
            $id: string;
            $schema: string;
            title: string;
            description: string;
            type: string;
            credentialType: string;
            version: string;
            properties: {
                [key: string]: unknown;
            };
            additionalProperties: boolean;
            required: string[];
        };
        Anchor: {
            pre: string;
            sn: number;
            d: string;
        };
        Seal: {
            s: string;
            d: string;
            i?: string;
        };
        IXN_V_1: {
            v: string;
            t: string;
            d: string;
            i: string;
            s: string;
            p: string;
            a: components['schemas']['Seal'][];
        };
        IXN_V_2: {
            v: string;
            t: string;
            d: string;
            i: string;
            s: string;
            p: string;
            a: components['schemas']['Seal'][];
        };
        ICP_V_1: {
            v: string;
            t: string;
            d: string;
            i: string;
            s: string;
            kt: string;
            k: string[];
            nt: string;
            n: string[];
            bt: string;
            b: string[];
            c: string[];
            a: unknown;
        };
        ICP_V_2: {
            v: string;
            t: string;
            d: string;
            i: string;
            s: string;
            kt: string;
            k: string[];
            nt: string;
            n: string[];
            bt: string;
            b: string[];
            c: string[];
            a: unknown;
        };
        ROT_V_1: {
            v: string;
            t: string;
            d: string;
            i: string;
            s: string;
            p: string;
            kt: string;
            k: string[];
            nt: string;
            n: string[];
            bt: string;
            br: string[];
            ba: string[];
            a: unknown;
        };
        ROT_V_2: {
            v: string;
            t: string;
            d: string;
            i: string;
            s: string;
            p: string;
            kt: string;
            k: string[];
            nt: string;
            n: string[];
            bt: string;
            br: string[];
            ba: string[];
            c: string[];
            a: unknown;
        };
        DIP_V_1: {
            v: string;
            t: string;
            d: string;
            i: string;
            s: string;
            kt: string;
            k: string[];
            nt: string;
            n: string[];
            bt: string;
            b: string[];
            c: string[];
            a: unknown;
            di: string;
        };
        DIP_V_2: {
            v: string;
            t: string;
            d: string;
            i: string;
            s: string;
            kt: string;
            k: string[];
            nt: string;
            n: string[];
            bt: string;
            b: string[];
            c: string[];
            a: unknown;
            di: string;
        };
        DRT_V_1: {
            v: string;
            t: string;
            d: string;
            i: string;
            s: string;
            p: string;
            kt: string;
            k: string[];
            nt: string;
            n: string[];
            bt: string;
            br: string[];
            ba: string[];
            a: unknown;
        };
        DRT_V_2: {
            v: string;
            t: string;
            d: string;
            i: string;
            s: string;
            p: string;
            kt: string;
            k: string[];
            nt: string;
            n: string[];
            bt: string;
            br: string[];
            ba: string[];
            c: string[];
            a: unknown;
        };
        Credential: {
            sad:
                | components['schemas']['ACDC_V_1']
                | components['schemas']['ACDC_V_2'];
            atc: string;
            iss: components['schemas']['IssEvent'];
            issatc: string;
            pre: string;
            schema: components['schemas']['Schema'];
            chains: {
                [key: string]: unknown;
            }[];
            status: components['schemas']['CredentialState'];
            anchor: components['schemas']['Anchor'];
            anc:
                | components['schemas']['IXN_V_1']
                | components['schemas']['IXN_V_2']
                | components['schemas']['ICP_V_1']
                | components['schemas']['ICP_V_2']
                | components['schemas']['ROT_V_1']
                | components['schemas']['ROT_V_2']
                | components['schemas']['DIP_V_1']
                | components['schemas']['DIP_V_2']
                | components['schemas']['DRT_V_1']
                | components['schemas']['DRT_V_2'];
            ancatc: string;
        };
        OperationStatus: {
            code: number;
            message: string;
            details?: {
                [key: string]: unknown;
            } | null;
        };
        Operation: {
            name: string;
            error?: components['schemas']['OperationStatus'];
            done?: boolean;
            metadata?: Record<string, never>;
            response?: Record<string, never>;
        };
        EmptyDict: Record<string, never>;
        CredentialStateIssOrRev: {
            vn: unknown;
            i: string;
            s: string;
            d: string;
            ri: string;
            a: components['schemas']['Seal'];
            dt: string;
            /** @enum {unknown} */
            et: 'iss' | 'rev';
            ra: components['schemas']['EmptyDict'];
        };
        RaFields: {
            i: string;
            s: string;
            d: string;
        };
        CredentialStateBisOrBrv: {
            vn: unknown;
            i: string;
            s: string;
            d: string;
            ri: string;
            a: components['schemas']['Seal'];
            dt: string;
            /** @enum {unknown} */
            et: 'bis' | 'brv';
            ra: components['schemas']['RaFields'];
        };
        CredentialState:
            | components['schemas']['CredentialStateIssOrRev']
            | components['schemas']['CredentialStateBisOrBrv'];
        Registry: {
            name: string;
            regk: string;
            pre: string;
            state: components['schemas']['CredentialState'];
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
