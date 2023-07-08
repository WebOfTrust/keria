# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.basing module

Testing the database classes
"""
import random

from keri.app import habbing

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

        for LEI in LEIs:
            qvisaid = issuer.issueQVIvLEI("issuer", issuerHab, issueeHab.pre, LEI)
            seeker.index(qvisaid)

        saids = seeker.find({})
        assert len(list(saids)) == 25

        saids = seeker.find({}).limit(50)
        assert len(list(saids)) == 50

        saids = seeker.find({'-d': "EAzc9zFLaK22zbrKDGIgKtrpDBNKWKvl8B0FKYAo19z_"})
        assert list(saids) == ['EAzc9zFLaK22zbrKDGIgKtrpDBNKWKvl8B0FKYAo19z_']

        saids = seeker.find({'-a-LEI': "OKB9487U4IDOG92KVVFN"})
        assert list(saids) == ['EJJzx89f1sTNdOPGHRx3e7ukcFW0F4nq9o7e8taLoNXt']

        saids = seeker.find({'-a-LEI': {"$eq": "OKB9487U4IDOG92KVVFN"}})
        assert list(saids) == ['EJJzx89f1sTNdOPGHRx3e7ukcFW0F4nq9o7e8taLoNXt']

        saids = seeker.find({}).sort(['-a-LEI']).limit(5)
        assert list(saids) == ['EAzc9zFLaK22zbrKDGIgKtrpDBNKWKvl8B0FKYAo19z_',
                               'EFW50stHOz-0_8Dh7EcYs0DsLZ06d4hwGKjRbOB8hgnR',
                               'EBiyZ2iyZodulzaUACzl_Cg6fRc1D0EPyNOooFemFK3e',
                               'EIn3igRf049kPQvpLjjLjU80QITreObH4BJguAxMPqis',
                               'ENnhxrOOeKIESS7_Yk7yVkJLm6blSOedACZvKFdMcxg5']

        saids = seeker.find({}).sort(['-a-LEI']).skip(10).limit(5)
        assert list(saids) == ['EDuqEITx0Jx8zZOCdqJU3e-RHvJS0UDZjeeBYPvB-XcK',
                               'ELic0LPsg_J9XietLYJ4MrOgSv3v6WqqBscrJMhZOV-V',
                               'EJ8_Bzr5vYZkaHmB-MW7VFYdgADg_W8MCZwWG7syjsu3',
                               'EPk5vCk-LLOmwityjKBn7HB92w2ViP-vro5_QaK2ueAd',
                               'EF7vDsfikOf_rEX2Lc_LFQoQSSxJxUr1Xkxlj9XeMu_l']

        saids = seeker.find({'-a-LEI': {'$begins': 'Q'}}).sort(['-a-LEI'])
        assert list(saids) == ['EJCprDNJIkHzDkMm__X1zcz65YBMtaBhjugIPXN0R2iC',
                               'EGO5Dh4ADbgDSTj-0X3452s7R6iAjFG2amY1qXlhqVxe',
                               'EOMWNhcIYPuXkh-LDZTc--sVL-cOINWNINfqO9kUhnBG']

        print(f"\nIssued by {issuerHab.pre}")
        saids = seeker.find({'-i': {'$eq': issuerHab.pre}}).sort(['-a-LEI']).skip(25).limit(6)
        for said in saids:
            creder = seeker.reger.creds.get(keys=(said,))
            print(creder.ked['a']['LEI'])


def randomLEI():
    values = "0123456789ABCDEFGHIJKLNMOPQRTUVXZY"
    lei = []
    for _ in range(20):
        lei.append(random.choice(values))

    return "".join(lei)


LEIs = [
    "0TRMLT6GMYU4KR2LF53X",
    "2YYF59AGE86D0414IPXE",
    "4O18CPBR0M98BL0XLKMV",
    "61U5P9O67BU0AJDG09V3",
    "71TPKZZ3BZE76P688I1J",
    "729OF364T863RFDT7U9T",
    "78I9GKEFM361IFY3PIN0",
    "88L360XFZMMQRVOBTOVJ",
    "8BY2XVDFG1KFJN51NHO7",
    "9DTTZO1AZAI3NCR4CDJE",
    "AK0BQ8AMUP83C44V7ROV",
    "ARFTR4V73K611OMR7ERY",
    "CUAJFJD60XF2BGRCXAKG",
    "DIJRO3BFDNCPA69LPEV1",
    "DZZ6D24KM7IM9EPZFV1B",
    "EL55H00R3CZ831I0V9AX",
    "FALI868UXRJ2RMVV3IL1",
    "GIHOVFO3YX15CQ77104O",
    "ICC05EF6YQCT3DNPTM9Y",
    "IP3X8NN44Y95LERBJTV3",
    "IU0QV4FAIVUUDHT76PLQ",
    "JJ2M6KI1UVLR9NMLBQR4",
    "JJFMBB5C56LITKKG0TEJ",
    "K1BC76MZ5JK5G3289MJH",
    "KJJ4LJN00ZHA4VUV8MAO",
    "LEYGGPUNV3LJY3KPFDHP",
    "LRK3QNUZJNJY1VD08MV2",
    "MNUHRN28GQN7VM0G0AKE",
    "N6IBQ8JMQMNOC9RKPR41",
    "NROKZU334DJVEFVZ7G2P",
    "NYCYXM3CRFZJRR6REOAG",
    "O4HPA5M8C3M3791O66VA",
    "OKB9487U4IDOG92KVVFN",
    "OT3VCOMUQUP4BOE2KKG4",
    "OVRCIN9K9I6CGJYHJO2X",
    "P7QQOV1918ONIGJ2XR8R",
    "QA3NXK31GVLM2I6Z93I0",
    "QNA8ZL2DODTF3R87GLX1",
    "QNRDPO6T79ZVRP9C296U",
    "TRM5JMV0G610VJ1102BT",
    "U6452GAE5C4TVRUY9EIX",
    "U6GNXGXNJ1NTV9X7BHO4",
    "U7B3X764DAI54QKIL6NV",
    "V6VXHQ9Y8NB2CGRED7LD",
    "Y0HFPYCR42XB09ODFV07",
    "Y3206FITOG3GRX6QM47Y",
    "YJ6XN9AIRRTR58DZ5I9H",
    "YLBCIFLMZXIDFH96Z66V",
    "ZUCD1UCNH83634ZIM8TC",
    "ZUQA6QTJDNYPF3DLP9NH",
]
