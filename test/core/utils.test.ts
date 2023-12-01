import { Ident, Saider, Serder, Serials, d, versify } from '../../src';
import {
    serializeACDCAttachment,
    serializeIssExnAttachment,
} from '../../src/keri/core/utils';

describe(serializeIssExnAttachment, () => {
    it('serializes iss data', () => {
        const [, data] = Saider.saidify({
            d: '',
            v: versify(Ident.KERI, undefined, Serials.JSON, 0),
        });

        const result = serializeIssExnAttachment(new Serder(data));

        expect(d(result)).toEqual(
            '-VAS-GAB0AAAAAAAAAAAAAAAAAAAAAAAEKZPmzJqhx76bcC2ftPQgeRirmOd8ZBOtGVqHJrSm7F1'
        );
    });
});

describe(serializeACDCAttachment, () => {
    it('serializes acdc data', () => {
        const [, data] = Saider.saidify({
            i: 'EP-hA0w9X5FDonCDxQv32OTCAvcxkZxgDLOnDb3Jcn3a',
            d: '',
            v: versify(Ident.ACDC, undefined, Serials.JSON, 0),
            a: {
                LEI: '123',
            },
        });

        const result = serializeACDCAttachment(new Serder(data));

        expect(d(result)).toEqual(
            '-IABEP-hA0w9X5FDonCDxQv32OTCAvcxkZxgDLOnDb3Jcn3a0AAAAAAAAAAAAAAAAAAAAAAAEHGU7u7cSMjMcJ1UyN8r-MnoZ3cDw4sMQNYxRLjqGVJI'
        );
    });
});
