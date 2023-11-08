import { Ident, Saider, Serder, Serials, d, versify } from '../../src';
import {
    serializeACDCAttachment,
    serializeIssExnAttachment,
} from '../../src/keri/core/utils';

describe(serializeIssExnAttachment, () => {
    it('serializes iss data', () => {
        const [saider, data] = Saider.saidify({
            d: '',
            v: versify(Ident.KERI, undefined, Serials.JSON, 0),
        });

        const result = serializeIssExnAttachment(new Serder(data), saider);

        expect(d(result)).toEqual(
            '-VAS-GAB0AAAAAAAAAAAAAAAAAAAAAAAEKZPmzJqhx76bcC2ftPQgeRirmOd8ZBOtGVqHJrSm7F1'
        );
    });
});

describe(serializeACDCAttachment, () => {
    it('serializes acdc data', () => {
        const [saider, data] = Saider.saidify({
            d: '',
            v: versify(Ident.ACDC, undefined, Serials.JSON, 0),
            a: {
                LEI: '123',
            },
        });

        const result = serializeACDCAttachment(new Serder(data), saider);

        expect(d(result)).toEqual(
            '-IABBHsiZCI6IkVORTZzbWw4X1NMZVIzdk9NajRJRExLX2Nn0AAAAAAAAAAAAAAAAAAAAAAAENE6sml8_SLeR3vOMj4IDLK_cgd-A-vtg0Jnu7ozdBjW'
        );
    });
});
