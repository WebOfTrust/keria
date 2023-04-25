# -*- encoding: utf-8 -*-
"""
SIGNIFY
keria.core.eventing module

Testing eventing
"""
from keri.app import habbing

from keria.core import eventing


def test_clondAid():
    salt = b'0123456789abcdef'
    with habbing.openHab(name="clone", salt=salt, temp=True) as (hby, hab):
        kel = eventing.cloneAid(db=hby.db, pre=hab.pre)
        assert len(kel) == 1
        evt = kel[0]

        assert evt['sig'] == 'AAD4riu0WEql_sUH26eJSNM6InJ6z6RUv2ZeR_e6YfnydnDKXnRHysmI9J0ZJ83-vjitQmuwYXsDti8BPLb8yNIF'
        assert evt['ked'] == hab.kever.serder.ked

        hab.rotate()
        hab.interact()
        hab.rotate()

        kel = eventing.cloneAid(db=hby.db, pre=hab.pre)
        assert len(kel) == 4

        evt = kel[3]

        assert evt['sig'] == 'AACA-Xjwk2CfSA1MB4KE-ff7SNdF4irBum5a9B1IJo1g3IKguDalMMRdPF4J6on3lRhhvO8AgpxmBJuCoIcmR-AI'
        assert evt['ked'] == hab.kever.serder.ked

        kel = eventing.cloneAid(db=hby.db, pre=hab.kever.serder.preb, fn=2)
        assert len(kel) == 2

        evt = kel[1]

        assert evt['sig'] == 'AACA-Xjwk2CfSA1MB4KE-ff7SNdF4irBum5a9B1IJo1g3IKguDalMMRdPF4J6on3lRhhvO8AgpxmBJuCoIcmR-AI'
        assert evt['ked'] == hab.kever.serder.ked




