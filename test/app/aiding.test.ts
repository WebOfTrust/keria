import { strict as assert } from 'assert';
import {
    CreateIdentiferArgs,
    RotateIdentifierArgs,
} from '../../src/keri/app/aiding';
import { Algos } from '../../src/keri/core/manager';
import libsodium from 'libsodium-wrappers-sumo';
import { randomUUID } from 'crypto';
import {
    Controller,
    Identifier,
    IdentifierDeps,
    KeyManager,
    Tier,
    randomPasscode,
} from '../../src';
import { createMockIdentifierState } from './test-utils';

const bran = '0123456789abcdefghijk';

export class MockClient implements IdentifierDeps {
    manager: KeyManager;
    controller: Controller;
    pidx = 0;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    fetch = jest.fn<Promise<Response>, [string, string, any]>();

    constructor(bran: string) {
        this.controller = new Controller(bran, Tier.low);
        this.manager = new KeyManager(this.controller.salter);
    }

    identifiers() {
        return new Identifier(this);
    }

    getLastMockRequest() {
        const [pathname, method, body] = this.fetch.mock.lastCall ?? [];

        return {
            path: pathname,
            method: method,
            body: body,
        };
    }
}

let client: MockClient;
beforeEach(async () => {
    await libsodium.ready;
    client = new MockClient(bran);
});

describe('Aiding', () => {
    it('Can list identifiers', async () => {
        client.fetch.mockResolvedValue(Response.json({}));
        await client.identifiers().list();
        const lastCall = client.getLastMockRequest();
        expect(lastCall.path).toEqual('/identifiers');
        expect(lastCall.method).toEqual('GET');
    });

    it('Can create salty identifiers', async () => {
        client.fetch.mockResolvedValue(Response.json({}));
        await client
            .identifiers()
            .create('aid1', { bran: '0123456789abcdefghijk' });

        const lastCall = client.getLastMockRequest();
        assert.equal(lastCall.path, '/identifiers');
        assert.equal(lastCall.method, 'POST');
        assert.equal(lastCall.body.name, 'aid1');
        assert.deepEqual(lastCall.body.icp, {
            v: 'KERI10JSON00012b_',
            t: 'icp',
            d: 'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK',
            i: 'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK',
            s: '0',
            kt: '1',
            k: ['DPmhSfdhCPxr3EqjxzEtF8TVy0YX7ATo0Uc8oo2cnmY9'],
            nt: '1',
            n: ['EAORnRtObOgNiOlMolji-KijC_isa3lRDpHCsol79cOc'],
            bt: '0',
            b: [],
            c: [],
            a: [],
        });
        assert.deepEqual(lastCall.body.sigs, [
            'AACZZe75PvUZ1lCREPxFAcX59XHo-BGMYTAGni-I4E0eqKznrEoK2d-mtWmWHwKns7tfnjOzTfDUcv7PLFJ52g0A',
        ]);
        assert.deepEqual(lastCall.body.salty.pidx, 0);
        assert.deepEqual(lastCall.body.salty.kidx, 0);
        assert.deepEqual(lastCall.body.salty.stem, 'signify:aid');
        assert.deepEqual(lastCall.body.salty.tier, 'low');
        assert.deepEqual(lastCall.body.salty.icodes, ['A']);
        assert.deepEqual(lastCall.body.salty.ncodes, ['A']);
        assert.deepEqual(lastCall.body.salty.dcode, 'E');
        assert.deepEqual(lastCall.body.salty.transferable, true);
    });

    it('Can get identifiers with special characters in the name', async () => {
        client.fetch.mockResolvedValue(Response.json({}));
        await client.identifiers().get('a name with ñ!');

        const lastCall = client.getLastMockRequest();
        assert.equal(lastCall.method, 'GET');
        assert.equal(lastCall.path, '/identifiers/a%20name%20with%20%C3%B1!');
    });

    it('Can create salty AID with multiple signatures', async () => {
        client.fetch.mockResolvedValue(Response.json({}));

        const result = await client.identifiers().create('aid2', {
            count: 3,
            ncount: 3,
            isith: '2',
            nsith: '2',
            bran: '0123456789lmnopqrstuv',
        });

        await result.op();
        const lastCall = client.getLastMockRequest();
        assert.equal(lastCall.path, '/identifiers');
        assert.equal(lastCall.method, 'POST');
        assert.equal(lastCall.body.name, 'aid2');
        assert.deepEqual(lastCall.body.icp, {
            v: 'KERI10JSON0001e7_',
            t: 'icp',
            d: 'EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX',
            i: 'EP10ooRj0DJF0HWZePEYMLPl-arMV-MAoTKK-o3DXbgX',
            s: '0',
            kt: '2',
            k: [
                'DGBw7C7AfC7jbD3jLLRS3SzIWFndM947TyNWKQ52iQx5',
                'DD_bHYFsgWXuCbz3SD0HjCIe_ITjRvEoCGuZ4PcNFFDz',
                'DEe9u8k0fm1wMFAuOIsCtCNrpduoaV5R21rAcJl0awze',
            ],
            nt: '2',
            n: [
                'EML5FrjCpz8SEl4dh0U15l8bMRhV_O5iDcR1opLJGBSH',
                'EJpKquuibYTqpwMDqEFAFs0gwq0PASAHZ_iDmSF3I2Vg',
                'ELplTAiEKdobFhlf-dh1vUb2iVDW0dYOSzs1dR7fQo60',
            ],
            bt: '0',
            b: [],
            c: [],
            a: [],
        });
        assert.deepEqual(lastCall.body.sigs, [
            'AAD9_IgPaUEBjAl1Ck61Jkn78ErzsnVkIxpaFBYSdSEAW4NbtXsLiUn1olijzdTQYn_Byq6MaEk-eoMN3Oc0WEEC',
            'ABBWJ7KkAXXiRK8JyEUpeARHJTTzlBHu_ev-jUrNEhV9sX4_4lI7wxowrQisumt5r50bUNfYBK7pxSwHk8I4IFQP',
            'ACDTITaEquHdYKkS-94tVCxL3IYrtvhlTt__sSUavTJT6fI3KB-uwXV7L0SfzMq0gFqYxkheH2LdC4HkAW2mH4QJ',
        ]);
        assert.deepEqual(lastCall.body.salty.pidx, 0);
        assert.deepEqual(lastCall.body.salty.kidx, 0);
        assert.deepEqual(lastCall.body.salty.stem, 'signify:aid');
        assert.deepEqual(lastCall.body.salty.tier, 'low');
        assert.deepEqual(lastCall.body.salty.icodes, ['A', 'A', 'A']);
        assert.deepEqual(lastCall.body.salty.ncodes, ['A', 'A', 'A']);
        assert.deepEqual(lastCall.body.salty.dcode, 'E');
        assert.deepEqual(lastCall.body.salty.transferable, true);
    });

    it('Can rotate salty identifier', async () => {
        const aid1 = await createMockIdentifierState('aid1', bran, {});
        client.fetch.mockResolvedValueOnce(Response.json(aid1));
        client.fetch.mockResolvedValueOnce(Response.json({}));

        await client.identifiers().rotate('aid1');
        const lastCall = client.getLastMockRequest();
        assert.equal(lastCall.path, '/identifiers/aid1');
        assert.equal(lastCall.method, 'PUT');
        assert.deepEqual(lastCall.body.rot, {
            v: 'KERI10JSON000160_',
            t: 'rot',
            d: 'EBQABdRgaxJONrSLcgrdtbASflkvLxJkiDO0H-XmuhGg',
            i: 'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK',
            s: '1',
            p: 'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK',
            kt: '1',
            k: ['DHgomzINlGJHr-XP3sv2ZcR9QsIEYS3LJhs4KRaZYKly'],
            nt: '1',
            n: ['EJMovBlrBuD6BVeUsGSxLjczbLEbZU9YnTSud9K4nVzk'],
            bt: '0',
            br: [],
            ba: [],
            a: [],
        });
        assert.deepEqual(lastCall.body.sigs, [
            'AABWSckRpAWLpfFSrpnDR3SzQASrRSVKGh8AnHxauhN_43qKkqPb9l04utnTm2ixNpGGJ-UB8qdKMjfkEQ61AIQC',
        ]);
        assert.deepEqual(lastCall.body.salty.pidx, 0);
        assert.deepEqual(lastCall.body.salty.kidx, 1);
        assert.deepEqual(lastCall.body.salty.stem, 'signify:aid');
        assert.deepEqual(lastCall.body.salty.tier, 'low');
        assert.deepEqual([...lastCall.body.salty.icodes], ['A']);
        assert.deepEqual([...lastCall.body.salty.ncodes], ['A']);
        assert.deepEqual(lastCall.body.salty.dcode, 'E');
        assert.deepEqual(lastCall.body.salty.transferable, true);
    });

    it('Can rotate salty identifier with sn > 10', async () => {
        const aid1 = await createMockIdentifierState('aid1', bran, {});
        client.fetch.mockResolvedValueOnce(
            Response.json({
                ...aid1,
                state: {
                    ...aid1.state,
                    s: 'a',
                },
            })
        );
        client.fetch.mockResolvedValueOnce(Response.json({}));

        await client.identifiers().rotate('aid1');
        const lastCall = client.getLastMockRequest();
        assert.equal(lastCall.path, '/identifiers/aid1');
        assert.equal(lastCall.method, 'PUT');
        expect(lastCall.body.rot).toMatchObject({
            v: 'KERI10JSON000160_',
            t: 'rot',
            s: 'b',
        });
    });

    it('Can create interact event', async () => {
        const data = [
            {
                i: 'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK',
                s: 0,
                d: 'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK',
            },
        ];

        const aid1 = await createMockIdentifierState('aid1', bran);
        client.fetch.mockResolvedValueOnce(Response.json(aid1));
        client.fetch.mockResolvedValueOnce(Response.json({}));

        await client.identifiers().interact('aid1', data);

        const lastCall = client.getLastMockRequest();

        expect(lastCall.path).toEqual('/identifiers/aid1?type=ixn');
        expect(lastCall.method).toEqual('PUT');
        expect(lastCall.body.ixn).toMatchObject({
            v: 'KERI10JSON000138_',
            t: 'ixn',
            d: 'EPtNJLDft3CB-oz3qIhe86fnTKs-GYWiWyx8fJv3VO5e',
            i: 'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK',
            s: '1',
            p: 'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK',
            a: data,
        });

        assert.deepEqual(lastCall.body.sigs, [
            'AADEzKk-5LT6vH-PWFb_1i1A8FW-KGHORtTOCZrKF4gtWkCr9vN1z_mDSVKRc6MKktpdeB3Ub1fWCGpnS50hRgoJ',
        ]);
    });

    it('Can create interact event when sequence number > 10', async () => {
        const data = [
            {
                i: 'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK',
                s: 0,
                d: 'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK',
            },
        ];

        const aid1 = await createMockIdentifierState('aid1', bran);
        client.fetch.mockResolvedValueOnce(
            Response.json({
                ...aid1,
                state: {
                    ...aid1.state,
                    s: 'a',
                },
            })
        );
        client.fetch.mockResolvedValueOnce(Response.json({}));

        await client.identifiers().interact('aid1', data);

        const lastCall = client.getLastMockRequest();

        expect(lastCall.path).toEqual('/identifiers/aid1?type=ixn');
        expect(lastCall.method).toEqual('PUT');
        expect(lastCall.body.ixn).toMatchObject({
            s: 'b',
            a: data,
        });
    });

    it('Can add end role', async () => {
        const aid1 = await createMockIdentifierState('aid1', bran, {});
        client.fetch.mockResolvedValueOnce(Response.json(aid1));
        client.fetch.mockResolvedValueOnce(Response.json({}));

        await client.identifiers().addEndRole('aid1', 'agent');
        const lastCall = client.getLastMockRequest();
        assert.equal(lastCall.path, '/identifiers/aid1/endroles');
        assert.equal(lastCall.method, 'POST');
        assert.equal(lastCall.body.rpy.t, 'rpy');
        assert.equal(lastCall.body.rpy.r, '/end/role/add');
        assert.deepEqual(lastCall.body.rpy.a, {
            cid: 'ELUvZ8aJEHAQE-0nsevyYTP98rBbGJUrTj5an-pCmwrK',
            role: 'agent',
        });
    });

    it('Can get members', async () => {
        client.fetch.mockResolvedValue(Response.json({}));
        await client.identifiers().members('aid1');
        const lastCall = client.getLastMockRequest();
        assert.equal(lastCall.path, '/identifiers/aid1/members');
        assert.equal(lastCall.method, 'GET');
    });

    it('Randy identifiers', async () => {
        client.fetch.mockResolvedValue(Response.json({}));
        await client.identifiers().create('aid1', {
            bran: '0123456789abcdefghijk',
            algo: Algos.randy,
        });
        const lastCall = client.getLastMockRequest();
        assert.equal(lastCall.path, '/identifiers');
        assert.equal(lastCall.method, 'POST');
        assert.equal(lastCall.body.name, 'aid1');
        assert.deepEqual(lastCall.body.icp.s, '0');
        assert.deepEqual(lastCall.body.icp.kt, '1');
        assert.deepEqual(lastCall.body.randy.transferable, true);
    });

    describe('Group identifiers', () => {
        it('Can Rotate group', async () => {
            const member1 = await createMockIdentifierState(
                randomUUID(),
                bran,
                {}
            );
            const member2 = await createMockIdentifierState(
                randomUUID(),
                randomPasscode(),
                {}
            );

            const group = await createMockIdentifierState(randomUUID(), bran, {
                algo: Algos.group,
                mhab: member1,
                nsith: '1',
                isith: '1',
                states: [member1.state, member2.state],
                rstates: [member1.state, member2.state],
            });

            client.fetch.mockResolvedValueOnce(
                Response.json(group, { status: 200 })
            );
            client.fetch.mockResolvedValueOnce(
                Response.json({}, { status: 202 })
            );

            const args: RotateIdentifierArgs = {
                nsith: '1',
                states: [member1.state, member2.state],
                rstates: [member1.state, member2.state],
            };

            await client.identifiers().rotate(group.name, args);
            const request = client.getLastMockRequest();
            const body = request.body;
            expect(body).toMatchObject({
                rot: {
                    t: 'rot',
                },
            });
        });

        it('Should use the previous sign threshold as the default next threshold', async () => {
            const member1 = await createMockIdentifierState(randomUUID(), bran);
            const member2 = await createMockIdentifierState(
                randomUUID(),
                randomPasscode()
            );

            const nextThreshold = ['1/2', '1/2'];
            const group = await createMockIdentifierState(randomUUID(), bran, {
                algo: Algos.group,
                mhab: member1,
                isith: ['1/3', '2/3'],
                nsith: nextThreshold,
                states: [member1.state, member2.state],
                rstates: [member1.state, member2.state],
            });

            client.fetch.mockResolvedValueOnce(Response.json(group));
            client.fetch.mockResolvedValueOnce(Response.json({}));
            await client.identifiers().rotate(group.name, {
                nsith: '1',
                states: [member1.state, member2.state],
                rstates: [member1.state, member2.state],
            });
            const request = client.getLastMockRequest();
            expect(request.body.rot).toMatchObject({
                t: 'rot',
                kt: nextThreshold,
            });
        });
    });

    describe('Typings test', () => {
        it('CreateIdentiferArgs', () => {
            let args: CreateIdentiferArgs;
            args = {
                isith: 1,
                nsith: 1,
            };
            args = {
                isith: '1',
                nsith: '1',
            };
            args = {
                isith: ['1'],
                nsith: ['1'],
            };
            args !== null; // avoids TS6133
        });

        it('RotateIdentifierArgs', () => {
            let args: RotateIdentifierArgs;
            args = {
                nsith: 1,
            };
            args = {
                nsith: '1',
            };
            args = {
                nsith: ['1'],
            };
            args !== null; // avoids TS6133
        });
    });
});
