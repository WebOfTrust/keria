# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.basing module

Testing the database classes
"""
import random

from keri.app import habbing
from keri.core import coring

from keria.db import basing

QVI_SAID = "EFgnk_c08WmZGgv9_mpldibRuqFMTQN-rAgtD-TCOwbs"
LE_SAID = "ENTAoj2oNBFpaniRswwPcca9W1ElEeH2V7ahw68HV4G5"


def test_seeker(helpers, seeder, mockHelpingNowUTC):
    salt = b'0123456789abcdef'

    with habbing.openHab(name="hal", salt=salt, temp=True) as (issueeHby, issueeHab), \
            habbing.openHab(name="issuer", salt=salt, temp=True) as (issuerHby, issuerHab), \
            helpers.withIssuer(name="issuer", hby=issuerHby) as issuer:

        seeker = basing.Seeker(db=issuerHby.db, reger=issuer.rgy.reger, reopen=True, temp=True)

        seeder.seedSchema(issueeHby.db)
        seeder.seedSchema(issuerHby.db)

        indexes = seeker.generateIndexes(QVI_SAID)

        # Verify the indexes created for the QVI schema
        assert indexes == ['5AABAA-i',
                           '5AABAA-i.5AABAA-s',
                           '4AAB-a-d',
                           '5AABAA-s.4AAB-a-d',
                           '5AABAA-i.4AAB-a-d',
                           '5AABAA-i.5AABAA-s.4AAB-a-d',
                           '4AAB-a-i.4AAB-a-d',
                           '4AAB-a-i.5AABAA-s.4AAB-a-d',
                           '4AAB-a-i',
                           '5AABAA-s.4AAB-a-i',
                           '5AABAA-i.4AAB-a-i',
                           '5AABAA-i.5AABAA-s.4AAB-a-i',
                           '4AAB-a-i.4AAB-a-i',
                           '4AAB-a-i.5AABAA-s.4AAB-a-i',
                           '6AACAAA-a-dt',
                           '5AABAA-s.6AACAAA-a-dt',
                           '5AABAA-i.6AACAAA-a-dt',
                           '5AABAA-i.5AABAA-s.6AACAAA-a-dt',
                           '4AAB-a-i.6AACAAA-a-dt',
                           '4AAB-a-i.5AABAA-s.6AACAAA-a-dt',
                           '5AACAA-a-LEI',
                           '5AABAA-s.5AACAA-a-LEI',
                           '5AABAA-i.5AACAA-a-LEI',
                           '5AABAA-i.5AABAA-s.5AACAA-a-LEI',
                           '4AAB-a-i.5AACAA-a-LEI',
                           '4AAB-a-i.5AABAA-s.5AACAA-a-LEI']

        # Test that the index tables were correctly ereated
        assert len(seeker.indexes) == 29

        indexes = seeker.generateIndexes(LE_SAID)

        # Test the indexes assigned to the LE schema
        assert indexes == ['5AABAA-i',
                           '5AABAA-i.5AABAA-s',
                           '4AAB-a-d',
                           '5AABAA-s.4AAB-a-d',
                           '5AABAA-i.4AAB-a-d',
                           '5AABAA-i.5AABAA-s.4AAB-a-d',
                           '4AAB-a-i.4AAB-a-d',
                           '4AAB-a-i.5AABAA-s.4AAB-a-d',
                           '4AAB-a-i',
                           '5AABAA-s.4AAB-a-i',
                           '5AABAA-i.4AAB-a-i',
                           '5AABAA-i.5AABAA-s.4AAB-a-i',
                           '4AAB-a-i.4AAB-a-i',
                           '4AAB-a-i.5AABAA-s.4AAB-a-i',
                           '6AACAAA-a-dt',
                           '5AABAA-s.6AACAAA-a-dt',
                           '5AABAA-i.6AACAAA-a-dt',
                           '5AABAA-i.5AABAA-s.6AACAAA-a-dt',
                           '4AAB-a-i.6AACAAA-a-dt',
                           '4AAB-a-i.5AABAA-s.6AACAAA-a-dt',
                           '5AACAA-a-LEI',
                           '5AABAA-s.5AACAA-a-LEI',
                           '5AABAA-i.5AACAA-a-LEI',
                           '5AABAA-i.5AABAA-s.5AACAA-a-LEI',
                           '4AAB-a-i.5AACAA-a-LEI',
                           '4AAB-a-i.5AABAA-s.5AACAA-a-LEI']

        # Assure that no knew index tables needed to be created
        assert len(seeker.indexes) == 29

        issuer.createRegistry(issuerHab.pre, name="issuer")

        for _ in range(50):
            LEI = randomLEI()
            qvisaid = issuer.issueQVIvLEI("issuer", issuerHab, issueeHab.pre, LEI)
            seeker.index(qvisaid)

        for _ in range(50):
            LEI = randomLEI()
            lesaid = issuer.issueLegalEntityvLEI("issuer", issuerHab, issueeHab.pre, LEI)
            seeker.index(lesaid)

        saids = seeker.find(
            fields=['-i'],
            values=[issuerHab.pre],
            order=['-a-LEI'],
            start=20,
            limit=30
        )

        for said in saids:
            creder = seeker.reger.creds.get(keys=(said,))
            print(creder.ked['a']['LEI'])


def randomLEI():
    values = "0123456789ABCDEFGHIJKLNMOPQRTUVXZY"
    lei = []
    for _ in range(20):
        lei.append(random.choice(values))

    return "".join(lei)
