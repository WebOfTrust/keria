import { strict as assert } from 'assert';

import { Sizage } from '../../src/keri/core/matter';

describe('Sizage', () => {
    it('should hold size values in 4 properties', async () => {
        const sizage = new Sizage(1, 2, 3, 4);
        assert.equal(sizage.hs, 1);
        assert.equal(sizage.ss, 2);
        assert.equal(sizage.fs, 3);
        assert.equal(sizage.ls, 4);
    });
});
