import { strict as assert } from 'assert';
import libsodium from 'libsodium-wrappers-sumo';
import { Salter, Tier } from '../../src/keri/core/salter';
import { b } from '../../src/keri/core/core';
import { MtrDex } from '../../src/keri/core/matter';
import { designature, Signage, signature } from '../../src/keri/end/ending';
import { Siger } from '../../src/keri/core/siger';
import { Cigar } from '../../src/keri/core/cigar';
import { Signer } from '../../src/keri/core/signer';

function createSigner(name: string): Signer {
    const temp = true;

    const salter = new Salter({ raw: b('0123456789abcdef') });
    const signer0 = salter.signer(
        MtrDex.Ed25519_Seed,
        true,
        name,
        Tier.low,
        temp
    );

    return signer0;
}

let sigers: Siger[];
let cigars: Cigar[];
let text: Uint8Array;
let pre: string;
let digest: string;

beforeAll(async () => {
    await libsodium.ready;

    const name = 'Hilga';
    const signer0 = createSigner(`${name}00`);
    const signer1 = createSigner(`${name}01`);
    const signer2 = createSigner(`${name}02`);
    const signers = [signer0, signer1, signer2];
    text = b(
        JSON.stringify({
            seid: 'BA89hKezugU2LFKiFVbitoHAxXqJh6HQ8Rn9tH7fxd68',
            name: 'wit0',
            dts: '2021-01-01T00:00:00.000000+00:00',
            scheme: 'http',
            host: 'localhost',
            port: 8080,
            path: '/witness',
        })
    );
    sigers = signers.map((signer, idx) => signer.sign(text, idx) as Siger);
    cigars = signers.map((s) => s.sign(text) as Cigar);
    pre = 'EGqHykT1gVyuWxsVW6LUUsz_KtLJGYMi_SrohInwvjC-'; // Hab.pre from KERIpy test
    digest = pre;
});

describe('When indexed signatures', () => {
    const expectedHeader = [
        'indexed="?1"',
        '0="AACsufRGYI-sRvS2c0rsOueSoSRtrjODaf48DYLJbLvvD8aHe7b2sWGebZ-y9ichhsxMF3Hhn-3LYSKIrnmH3oIN"',
        '1="ABDs7m2-h5l7vpjYtbFXtksicpZK5Oclm43EOkE2xoQOfr08doj73VrlKZOKNfJmRumD3tfaiFFgVZqPgiHuFVoA"',
        '2="ACDVOy2LvGgFINUneL4iwA55ypJR6vDpLLbdleEsiANmFazwZARypJMiw9vu2Iu0oL7XCUiUT4JncU8P3HdIp40F"',
    ].join(';');

    it('Can create signature header', async () => {
        const signage = new Signage(sigers);
        const header = signature([signage]);
        assert.equal(header.has('Signature'), true);
        assert.equal(header.get('Signature'), expectedHeader);
    });

    it('Can parse signature header', async () => {
        const signages = designature(expectedHeader);
        assert.equal(signages.length, 1);
        const signage = signages[0];

        assert(signage.markers instanceof Map);
        assert.equal(signage.markers.size, 3);
        signage.markers.forEach((marker, tag) => {
            assert(marker instanceof Siger);
            const idx = parseInt(tag);
            const siger = sigers[idx];
            assert.equal(marker.qb64, siger.qb64);
            assert.equal(parseInt(tag), siger.index);
        });
    });
});

describe('When named signatures', () => {
    const expectedHeader = [
        'indexed="?1"',
        'siger0="AACsufRGYI-sRvS2c0rsOueSoSRtrjODaf48DYLJbLvvD8aHe7b2sWGebZ-y9ichhsxMF3Hhn-3LYSKIrnmH3oIN"',
        'siger1="ABDs7m2-h5l7vpjYtbFXtksicpZK5Oclm43EOkE2xoQOfr08doj73VrlKZOKNfJmRumD3tfaiFFgVZqPgiHuFVoA"',
        'siger2="ACDVOy2LvGgFINUneL4iwA55ypJR6vDpLLbdleEsiANmFazwZARypJMiw9vu2Iu0oL7XCUiUT4JncU8P3HdIp40F"',
    ].join(';');

    let markers: Map<string, Siger>;

    beforeEach(() => {
        markers = new Map<string, Siger>(
            sigers.map((s, idx) => [`siger${idx}`, s])
        );
    });

    it('Can create signature header', async () => {
        const signage = new Signage(markers);
        const header = signature([signage]);
        assert.equal(header.has('Signature'), true);
        assert.equal(header.get('Signature'), expectedHeader);
    });

    it('Can parse signature header', async () => {
        const signages = designature(expectedHeader);
        assert.equal(signages.length, 1);
        const signage = signages[0];

        assert(signage.markers instanceof Map);
        assert.equal(signage.markers.size, 3);
        signage.markers.forEach((marker, tag) => {
            const siger = markers.get(tag);

            assert(marker instanceof Siger);
            assert(siger);
            assert.equal(marker.qb64, siger.qb64);
        });
    });
});

describe('When indexed CESR signatures', () => {
    const expectedHeader = [
        'indexed="?1"',
        'signer="EGqHykT1gVyuWxsVW6LUUsz_KtLJGYMi_SrohInwvjC-"',
        'ordinal="0"',
        'digest="EGqHykT1gVyuWxsVW6LUUsz_KtLJGYMi_SrohInwvjC-"',
        'kind="CESR"',
        '0="AACsufRGYI-sRvS2c0rsOueSoSRtrjODaf48DYLJbLvvD8aHe7b2sWGebZ-y9ichhsxMF3Hhn-3LYSKIrnmH3oIN"',
        '1="ABDs7m2-h5l7vpjYtbFXtksicpZK5Oclm43EOkE2xoQOfr08doj73VrlKZOKNfJmRumD3tfaiFFgVZqPgiHuFVoA"',
        '2="ACDVOy2LvGgFINUneL4iwA55ypJR6vDpLLbdleEsiANmFazwZARypJMiw9vu2Iu0oL7XCUiUT4JncU8P3HdIp40F"',
    ].join(';');

    it('Should create headers', async () => {
        const signage = new Signage(sigers, true, pre, '0', digest, 'CESR');
        const headers = signature([signage]);
        assert.equal(headers.has('Signature'), true);
        assert.equal(headers.get('Signature'), expectedHeader);
    });

    it('Should parse headers', async () => {
        const signages = designature(expectedHeader);
        assert.equal(signages.length, 1);
        const signage = signages[0];
        assert.equal(signage.indexed, true);
        assert.equal(signage.signer, pre);
        assert.equal(signage.digest, digest);
        assert.equal(signage.kind, 'CESR');

        assert(signage.markers instanceof Map);
        assert.equal(signage.markers.size, 3);
        signage.markers.forEach((marker, tag) => {
            assert(marker instanceof Siger);
            const idx = parseInt(tag);
            const siger = sigers[idx];
            assert.equal(marker.qb64, siger.qb64);
            assert.equal(parseInt(tag), siger.index);
        });
    });
});

describe('When non-indexed signatures', () => {
    const expectedHeader = [
        'indexed="?0"',
        'DAi2TaRNVtGmV8eSUvqHIBzTzIgrQi57vKzw5Svmy7jw="0BCsufRGYI-sRvS2c0rsOueSoSRtrjODaf48DYLJbLvvD8aHe7b2sWGebZ-y9ichhsxMF3Hhn-3LYSKIrnmH3oIN"',
        'DNK2KFnL0jUGlmvZHRse7HwNGVdtkM-ORvTZfFw7mDbt="0BDs7m2-h5l7vpjYtbFXtksicpZK5Oclm43EOkE2xoQOfr08doj73VrlKZOKNfJmRumD3tfaiFFgVZqPgiHuFVoA"',
        'DDvIoIYqeuXJ4Zb8e2luWfjPTg4FeIzfHzIO8lC56WjD="0BDVOy2LvGgFINUneL4iwA55ypJR6vDpLLbdleEsiANmFazwZARypJMiw9vu2Iu0oL7XCUiUT4JncU8P3HdIp40F"',
    ].join(';');

    it('Should create headers', () => {
        const signage = new Signage(cigars);
        const header = signature([signage]);
        assert.equal(header.has('Signature'), true);
        assert.equal(header.get('Signature'), expectedHeader);
    });

    it('Should parse headers', () => {
        const signages = designature(expectedHeader);
        assert.equal(signages.length, 1);
        const signage = signages[0];
        assert.equal(signage.indexed, false);
        assert(signage.markers instanceof Map);
        assert.equal(signage.markers.size, 3);

        signage.markers.forEach((marker, tag) => {
            assert(marker instanceof Cigar);
            const cigar = cigars.find((cigar) => cigar.verfer!.qb64 == tag);
            assert.notEqual(cigar, undefined);
            assert.equal(marker.qb64, cigar!.qb64);
            assert.equal(tag, cigar!.verfer!.qb64);
        });
    });
});

describe('Combined headers', () => {
    const expectedHeader = [
        'indexed="?1"',
        'signer="EGqHykT1gVyuWxsVW6LUUsz_KtLJGYMi_SrohInwvjC-"',
        'kind="CESR"',
        '0="AACsufRGYI-sRvS2c0rsOueSoSRtrjODaf48DYLJbLvvD8aHe7b2sWGebZ-y9ichhsxMF3Hhn-3LYSKIrnmH3oIN"',
        '1="ABDs7m2-h5l7vpjYtbFXtksicpZK5Oclm43EOkE2xoQOfr08doj73VrlKZOKNfJmRumD3tfaiFFgVZqPgiHuFVoA"',
        '2="ACDVOy2LvGgFINUneL4iwA55ypJR6vDpLLbdleEsiANmFazwZARypJMiw9vu2Iu0oL7XCUiUT4JncU8P3HdIp40F",indexed="?0"',
        'signer="EGqHykT1gVyuWxsVW6LUUsz_KtLJGYMi_SrohInwvjC-"',
        'kind="CESR"',
        'DAi2TaRNVtGmV8eSUvqHIBzTzIgrQi57vKzw5Svmy7jw="0BCsufRGYI-sRvS2c0rsOueSoSRtrjODaf48DYLJbLvvD8aHe7b2sWGebZ-y9ichhsxMF3Hhn-3LYSKIrnmH3oIN"',
        'DNK2KFnL0jUGlmvZHRse7HwNGVdtkM-ORvTZfFw7mDbt="0BDs7m2-h5l7vpjYtbFXtksicpZK5Oclm43EOkE2xoQOfr08doj73VrlKZOKNfJmRumD3tfaiFFgVZqPgiHuFVoA"',
        'DDvIoIYqeuXJ4Zb8e2luWfjPTg4FeIzfHzIO8lC56WjD="0BDVOy2LvGgFINUneL4iwA55ypJR6vDpLLbdleEsiANmFazwZARypJMiw9vu2Iu0oL7XCUiUT4JncU8P3HdIp40F"',
    ].join(';');

    it('Should create header', () => {
        const signages: Signage[] = [
            new Signage(sigers, true, pre, undefined, undefined, 'CESR'),
            new Signage(cigars, false, pre, undefined, undefined, 'CESR'),
        ];

        const header = signature(signages);
        assert.equal(header.has('Signature'), true);
        assert.equal(header.get('Signature'), expectedHeader);
    });

    it('Should parse hader', () => {
        const signages = designature(expectedHeader);
        assert.equal(signages.length, 2);

        const signage0 = signages[0];
        assert.equal(signage0.indexed, true);
        assert.equal(signage0.signer, pre);
        assert.equal(signage0.kind, 'CESR');
        assert(signage0.markers instanceof Map);
        assert.equal(signage0.markers.size, 3);
        signage0.markers.forEach((marker, tag) => {
            assert(marker instanceof Siger);
            const idx = parseInt(tag);
            const siger = sigers[idx];
            assert.equal(marker.qb64, siger.qb64);
            assert.equal(parseInt(tag), siger.index);
        });

        const signage1 = signages[1];
        assert.equal(signage1.indexed, false);
        assert.equal(signage1.signer, pre);
        assert.equal(signage1.kind, 'CESR');
        assert(signage1.markers instanceof Map);
        assert.equal(signage1.markers.size, 3);
        signage1.markers.forEach((marker, tag) => {
            assert(marker instanceof Cigar);
            const cigar = cigars.find((cigar) => cigar.verfer!.qb64 == tag);
            assert.notEqual(cigar, undefined);
            assert.equal(marker.qb64, cigar!.qb64);
            assert.equal(tag, cigar!.verfer!.qb64);
        });
    });
});
