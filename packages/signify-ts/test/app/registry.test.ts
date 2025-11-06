import { SignifyClient } from '../../src/keri/app/clienting.ts';
import { anyOfClass, anything, instance, mock, when } from 'ts-mockito';
import libsodium from 'libsodium-wrappers-sumo';
import { Registries } from '../../src/keri/app/credentialing.ts';
import {
    Identifier,
    IdentifierManagerFactory,
    SaltyIdentifierManager,
} from '../../src/index.ts';
import { assert, describe, expect, it } from 'vitest';
import { HabState, KeyState } from '../../src/keri/core/keyState.ts';

describe('registry', () => {
    it('should create a registry', async () => {
        await libsodium.ready;
        const mockedClient = mock(SignifyClient);
        const mockedIdentifiers = mock(Identifier);
        const mockedKeyManager = mock(IdentifierManagerFactory);
        const mockedKeeper = mock(SaltyIdentifierManager);

        const hab = {
            prefix: 'hab prefix',
            state: { s: '0', d: 'a digest' } as KeyState,
        } as HabState;

        when(mockedClient.manager).thenReturn(instance(mockedKeyManager));
        when(mockedKeyManager.get(hab)).thenReturn(instance(mockedKeeper));

        when(mockedKeeper.sign(anyOfClass(Uint8Array))).thenResolve([
            'a signature',
        ]);

        when(mockedIdentifiers.get('a name')).thenResolve(hab);
        when(mockedClient.identifiers()).thenReturn(
            instance(mockedIdentifiers)
        );

        const mockedResponse = mock(Response);
        when(
            mockedClient.fetch(
                '/identifiers/a name/registries',
                'POST',
                anything()
            )
        ).thenResolve(instance(mockedResponse));

        const registries = new Registries(instance(mockedClient));

        const actual = await registries.create({
            name: 'a name',
            registryName: 'a registry name',
            nonce: '',
        });

        assert.equal(
            actual.regser.raw,
            '{"v":"KERI10JSON0000c5_","t":"vcp","d":"EMppKX_JxXBuL_xE3A_a6lOcseYwaB7jAvZ0YFdgecXX","i":"EMppKX_JxXBuL_xE3A_a6lOcseYwaB7jAvZ0YFdgecXX","ii":"hab prefix","s":"0","c":["NB"],"bt":"0","b":[],"n":""}'
        );
        assert.equal(
            actual.serder.raw,
            '{"v":"KERI10JSON0000f4_","t":"ixn","d":"EE5R61289Xnpxc2M-euPtsAkp849tUdNJ7DuyBeSiRtm","i":"hab prefix","s":"1","p":"a digest","a":[{"i":"EMppKX_JxXBuL_xE3A_a6lOcseYwaB7jAvZ0YFdgecXX","s":"0","d":"EMppKX_JxXBuL_xE3A_a6lOcseYwaB7jAvZ0YFdgecXX"}]}'
        );
    });

    it('should fail on estanblishmnet only for now', async () => {
        await libsodium.ready;
        const mockedClient = mock(SignifyClient);
        const mockedIdentifiers = mock(Identifier);
        const keystate: KeyState = {
            s: '0',
            d: 'a digest',
            i: '',
            p: '',
            f: '',
            dt: '',
            et: '',
            kt: '',
            k: [],
            nt: '',
            n: [],
            bt: '',
            b: [],
            c: ['EO'],
            ee: {
                s: '',
                d: '',
                br: [],
                ba: [],
            },
            di: '',
        };
        const hab = {
            prefix: 'hab prefix',
            state: keystate,
            name: 'a name',
            transferable: true,
            windexes: [],
            icp_dt: '2023-12-01T10:05:25.062609+00:00',
            randy: {
                prxs: [],
                nxts: [],
            },
        };

        when(mockedIdentifiers.get('a name')).thenResolve(hab);
        when(mockedClient.identifiers()).thenReturn(
            instance(mockedIdentifiers)
        );

        const registries = new Registries(instance(mockedClient));

        await expect(async () => {
            await registries.create({
                name: 'a name',
                registryName: 'a registry name',
                nonce: '',
            });
        }).rejects.toThrowError('establishment only not implemented');
    });
});
