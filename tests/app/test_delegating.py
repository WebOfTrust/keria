# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.delegating module

Testing the Mark II Agent Anchorer
"""
import pytest
from hio.base import doing
from keri import kering
from keri.app import habbing
from keri.core import coring, eventing

from keria.app import delegating


def test_sealer():
    with habbing.openHby(name="p1", temp=True) as hby:
        # Create Anchorer to test
        anchorer = delegating.Anchorer(hby=hby)

        # Doer hierarchy
        doist = doing.Doist(tock=0.03125, real=True)
        deeds = doist.enter(doers=[anchorer])

        # Create delegator and delegate Habs
        delegator = hby.makeHab("delegator")
        proxy = hby.makeHab("proxy")
        delegate = hby.makeHab("delegate", delpre=delegator.pre)

        # Try with a bad AID
        with pytest.raises(kering.ValidationError):
            anchorer.delegation(pre="EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY")

        # Needs a proxy
        with pytest.raises(kering.ValidationError):
            anchorer.delegation(pre=delegate.pre)

        # Run delegation to escrow inception event
        anchorer.delegation(pre=delegate.pre, proxy=proxy)
        doist.recur(deeds=deeds)

        prefixer = coring.Prefixer(qb64=delegate.pre)
        seqner = coring.Seqner(sn=0)
        assert anchorer.complete(prefixer=prefixer, seqner=seqner) is False

        # Anchor the seal in delegator's KEL, approving the delegation
        seal = eventing.SealEvent(prefixer.qb64, "0", prefixer.qb64)
        delegator.interact(data=[seal._asdict()])

        while anchorer.complete(prefixer=prefixer, seqner=seqner) is False:
            doist.recur(deeds=deeds)

        # Will raise with a bad digest
        with pytest.raises(kering.ValidationError):
            # Create saider for the wrong event
            saider = coring.Saider(qb64=delegator.kever.serder.said)
            anchorer.complete(prefixer=prefixer, seqner=seqner, saider=saider)

        assert anchorer.complete(prefixer=prefixer, seqner=seqner) is True




