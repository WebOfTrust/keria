import { strict as assert } from 'assert';
import { Tholder } from '../../src/keri/core/tholder';
import { math } from '../../src';

describe('THolder', () => {
    it('should hold thresholds', async () => {
        let tholder = new Tholder({ sith: 'b' });
        assert.equal(tholder.thold, 11);
        assert.equal(tholder.size, 11);
        assert.deepEqual(tholder.limen, new Uint8Array([77, 65, 115, 65]));
        assert.equal(tholder.sith, 'b');
        assert.equal(tholder.json, '"b"');
        assert.equal(tholder.num, 11);
        assert.notEqual(tholder.satisfy([1, 2, 3]), true);
        assert.equal(
            tholder.satisfy([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]),
            true
        );

        tholder = new Tholder({ sith: 11 });
        assert.equal(tholder.thold, 11);
        assert.equal(tholder.size, 11);
        assert.deepEqual(tholder.limen, new Uint8Array([77, 65, 115, 65]));
        assert.equal(tholder.sith, 'b');
        assert.equal(tholder.json, '"b"');
        assert.equal(tholder.num, 11);
        assert.notEqual(tholder.satisfy([1, 2, 3]), true);
        assert.equal(
            tholder.satisfy([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]),
            true
        );

        tholder = new Tholder({ thold: 2 });
        assert.equal(tholder.thold, 2);
        assert.equal(tholder.size, 2);
        assert.deepEqual(tholder.limen, new Uint8Array([77, 65, 73, 65]));
        assert.equal(tholder.sith, '2');
        assert.equal(tholder.json, '"2"');
        assert.equal(tholder.num, 2);
        assert.notEqual(tholder.satisfy([1]), true);
        assert.equal(tholder.satisfy([1, 2]), true);
        assert.equal(tholder.satisfy([1, 2, 3, 4]), true);

        assert.throws(() => {
            new Tholder({ sith: -1 });
        });

        assert.throws(() => {
            tholder = new Tholder({
                sith: ['1/2', '1/2', ['1/3', '1/3', '1/3']],
            });
        });

        assert.throws(() => {
            tholder = new Tholder({
                sith: [
                    ['1/2', '1/2'],
                    ['1/4', '1/4', '1/4'],
                ],
            });
        });

        // math.fractional Weights
        tholder = new Tholder({ sith: ['1/2', '1/2', '1/4', '1/4', '1/4'] });
        assert.equal(tholder.weighted, true);
        assert.equal(tholder.size, 5);
        assert.deepStrictEqual(tholder.thold, [
            [
                math.fraction('1/2'),
                math.fraction('1/2'),
                math.fraction('1/4'),
                math.fraction('1/4'),
                math.fraction('1/4'),
            ],
        ]);
        assert.equal(tholder.satisfy([0, 1]), true);
        assert.equal(tholder.satisfy([0, 2, 4]), true);
        assert.equal(tholder.satisfy([1, 3, 4]), true);
        assert.equal(tholder.satisfy([0, 1, 2, 3, 4]), true);
        assert.equal(tholder.satisfy([0, 2, 3]), true);
        assert.equal(tholder.satisfy([0, 0, 1, 2, 1]), true);
        assert.notEqual(tholder.satisfy([0]), true);
        assert.notEqual(tholder.satisfy([0, 2]), true);
        assert.notEqual(tholder.satisfy([2, 3, 4]), true);

        tholder = new Tholder({
            sith: [
                ['1/2', '1/2', '1/2'],
                ['1/3', '1/3', '1/3', '1/3'],
            ],
        });
        assert.equal(tholder.weighted, true);
        assert.equal(tholder.size, 7);
        assert.deepStrictEqual(tholder.sith, [
            ['1/2', '1/2', '1/2'],
            ['1/3', '1/3', '1/3', '1/3'],
        ]);
        assert.deepStrictEqual(tholder.thold, [
            [math.fraction(1, 2), math.fraction(1, 2), math.fraction(1, 2)],
            [
                math.fraction(1, 3),
                math.fraction(1, 3),
                math.fraction(1, 3),
                math.fraction(1, 3),
            ],
        ]);
        assert.equal(tholder.satisfy([0, 2, 3, 5, 6]), true);
        assert.equal(tholder.satisfy([1, 2, 3, 4, 5]), true);
        assert.notEqual(tholder.satisfy([0, 1]), true);
        assert.notEqual(tholder.satisfy([0, 2]), true);
        assert.notEqual(tholder.satisfy([4, 5, 6]), true);
        assert.notEqual(tholder.satisfy([1, 4, 5, 6]), true);

        tholder = new Tholder({
            sith: '[["1/2", "1/2", "1/4", "1/4", "1/4"], ["1/1", "1"]]',
        });
        assert.equal(tholder.weighted, true);
        assert.equal(tholder.size, 7);
        assert.deepStrictEqual(tholder.sith, [
            ['1/2', '1/2', '1/4', '1/4', '1/4'],
            ['1', '1'],
        ]);
        assert.deepStrictEqual(tholder.thold, [
            [
                math.fraction(1, 2),
                math.fraction(1, 2),
                math.fraction(1, 4),
                math.fraction(1, 4),
                math.fraction(1, 4),
            ],
            [math.fraction(1, 1), math.fraction(1, 1)],
        ]);
        assert.equal(tholder.satisfy([1, 2, 3, 5]), true);
        assert.equal(tholder.satisfy([0, 1, 6]), true);
        assert.notEqual(tholder.satisfy([0, 1]), true);
        assert.notEqual(tholder.satisfy([5, 6]), true);
        assert.notEqual(tholder.satisfy([2, 3, 4]), true);
        assert.notEqual(tholder.satisfy([]), true);

        tholder = new Tholder({
            sith: [
                ['1/2', '1/2', '1/4', '1/4', '1/4'],
                ['1/1', '1'],
            ],
        });
        assert.equal(tholder.weighted, true);
        assert.equal(tholder.size, 7);
        assert.deepStrictEqual(tholder.sith, [
            ['1/2', '1/2', '1/4', '1/4', '1/4'],
            ['1', '1'],
        ]);
        assert.deepStrictEqual(
            tholder.json,
            '[["1/2","1/2","1/4","1/4","1/4"],["1","1"]]'
        );
        assert.deepStrictEqual(tholder.thold, [
            [
                math.fraction(1, 2),
                math.fraction(1, 2),
                math.fraction(1, 4),
                math.fraction(1, 4),
                math.fraction(1, 4),
            ],
            [math.fraction(1, 1), math.fraction(1, 1)],
        ]);
        assert.equal(tholder.satisfy([1, 2, 3, 5]), true);
        assert.equal(tholder.satisfy([0, 1, 6]), true);
        assert.notEqual(tholder.satisfy([0, 1]), true);
        assert.notEqual(tholder.satisfy([5, 6]), true);
        assert.notEqual(tholder.satisfy([2, 3, 4]), true);
        assert.notEqual(tholder.satisfy([]), true);
    });
});
