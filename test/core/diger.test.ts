const Base64 = require('urlsafe-base64');
const blake3 = require('blake3');
import {strict as assert} from "assert";

const { Diger } = require('../../src/keri/core/diger');
const derivationCodes = require('../../src/keri/core/derivationCodes');


describe('Diger', () => {
  it('should generate digests', () => {
      // Create something to digest and verify
      const ser = Buffer.from('abcdefghijklmnopqrstuvwxyz0123456789', 'binary');
      const hasher = blake3.createHash();
      const dig = blake3.hash(ser);
      console.log(Base64.encode(dig))
      const digest = hasher.update(ser).digest('');

      let diger = new Diger(digest);
      assert.deepStrictEqual(diger.code(), derivationCodes.oneCharCode.Blake3_256);
      assert.deepStrictEqual(
        diger.raw().length,
        derivationCodes.CryOneRawSizes[diger.code()],
      );
      let result = diger.verify(ser);
      assert.equal(result, true);

      result = diger.verify(
        Buffer.concat([ser, Buffer.from('2j2idjpwjfepjtgi', 'binary')]),
      );
      assert.equal(result, false);
      diger = new Diger(digest, null, derivationCodes.oneCharCode.Blake3_256);
      assert.deepStrictEqual(diger.code(), derivationCodes.oneCharCode.Blake3_256);
      assert.deepStrictEqual(
        diger.raw().length,
        derivationCodes.CryOneRawSizes[diger.getCode],
      );
      result = diger.verify(ser);
      assert.equal(result, true);

      diger = new Diger(null, ser);
      assert.deepStrictEqual(diger.code(), derivationCodes.oneCharCode.Blake3_256);
      assert.deepStrictEqual(
        diger.raw().length,
        derivationCodes.CryOneRawSizes[diger.code()],
      );
      result = diger.verify(ser);
      assert.equal(result, true);
    });
});
