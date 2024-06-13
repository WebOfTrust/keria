# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.delegating module

Testing the Mark II Agent Anchorer
"""
import json
import time
import pytest

from hio.base import doing
from keri import kering
from keri.app import habbing
from keri.core import coring, eventing, parsing, serdering

from keria.app import aiding, delegating
from keria.core import longrunning
from keria.end import ending

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
        
def test_delegator_end(helpers):
    torname = "delegator"
    teename = "delegatee"
    saltb = b"0123456789abcdef"
    
    with habbing.openHby(name="p1", temp=True) as hby, \
        helpers.openKeria() as (toragency, toragent, torapp, torclient):

        # Create Anchorer to test
        anchorer = delegating.Anchorer(hby=hby)
        
        #setup agency endpoints
        ending.loadEnds(app=torapp, agency=toragency)
        end = aiding.IdentifierCollectionEnd()
        resend = aiding.IdentifierResourceEnd()
        torapp.add_route("/identifiers", end)
        torapp.add_route("/identifiers/{name}", resend)
        torapp.add_route("/identifiers/{name}/events", resend)
        torend = delegating.DelegatorEnd(resend)
        torapp.add_route(delegating.DELEGATION_ROUTE, torend)
        
        # Create delegator
        salt = b"0123456789abcdef"
        op = helpers.createAid(torclient, torname, salt)
        aid = op["response"]
        torpre = aid["i"]
        assert torpre == "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY"
        
        # setup delegatee
        fakeproxy = hby.makeHab("proxy")
        teehab = hby.makeHab(teename, delpre=torpre)
        
        # Use valid AID, role and EID
        toroobi = torclient.simulate_get(path=f"/oobi/{torpre}/agent/{toragent.agentHab.pre}")
        assert toroobi.status_code == 200
        assert toroobi.headers['Content-Type'] == "application/json+cesr"

        # Try before knowing delegator key state
        with pytest.raises(kering.ValidationError):
            anchorer.delegation(pre=teehab.pre, proxy=fakeproxy)

        #introduce delegator to delegatee
        teehab.psr.parse(ims=toroobi.content)

        # Doer hierarchy
        doist = doing.Doist(tock=0.03125, real=True)
        deeds = doist.enter(doers=([anchorer, toragent]))

        # Run delegation to escrow inception event
        anchorer.delegation(pre=teehab.pre)
        doist.recur(deeds=deeds)
        
        # normally postman would take care of this but we can do it manually here
        teeser = teehab.kever.serder
        for msg in teehab.db.clonePreIter(pre=teehab.pre):
            parsing.Parser().parse(ims=bytearray(msg), kvy=toragent.kvy, local=True) # Local true otherwise it will be a misfit

        # Delegatee hasn't seen delegator anchor
        prefixer = coring.Prefixer(qb64=teehab.pre)
        seqner = coring.Seqner(sn=0)
        assert anchorer.complete(prefixer=prefixer, seqner=seqner) is False

        # Delegator still hasn't processed the delegatee dip event
        doist.recur(deeds=deeds)
        assert teehab.pre not in toragent.agentHab.kevers

        # Anchor the seal in delegator's KEL and approve the escrowed dip event
        seal = dict(i=prefixer.qb64, s="0", d=prefixer.qb64)
        iserder, isigers = helpers.interact(pre=aid["i"], bran=saltb, pidx=0, ridx=0, dig=aid["d"], sn='1', data=[seal])
        appDelBody = {"ixn": iserder.ked, "sigs": isigers}
        apprDelRes = torclient.simulate_post(path=f"/identifiers/{torname}/delegation", body=json.dumps(appDelBody))
        assert apprDelRes.status_code == 200
        op = apprDelRes.json
        assert op["metadata"]["teepre"] == iserder.ked['a'][0]['i']

        # Delegator still hasn't processed the delegatee dip event
        assert teehab.pre not in toragent.agentHab.kevers

        # Monitor long running operation indicating escrowed delegatee 
        # dip event was successfully processed
        opColEnd = longrunning.OperationCollectionEnd()
        torapp.add_route("/operations", opColEnd)
        opResEnd = longrunning.OperationResourceEnd()
        torapp.add_route("/operations/{name}", opResEnd)
        count=0
        while not op or not "done" in op or not op["done"]:
            doist.recur(deeds=deeds)
            time.sleep(1)
            res = torclient.simulate_get(path=f'/operations/{op["name"]}')
            assert res.status_code == 200
            op = res.json
            count += 1
            if count > 10:
                raise Exception("Delegator never processed the delegatee dip event")
        
        # Delegator escrows completed and now aknowledges the delegatee dip event
        assert teehab.pre in toragent.agentHab.kevers
        
        # Delegatee hasn't seen the anchor yet
        assert anchorer.complete(prefixer=prefixer, seqner=seqner) is False
        
        # update delegatee with delegator KEL w/ interaction event
        toroobi = torclient.simulate_get(path=f"/oobi/{torpre}/agent/{toragent.agentHab.pre}")
        teehab.psr.parse(ims=toroobi.content)
        count = 0
        while anchorer.complete(prefixer=prefixer, seqner=seqner) is False:
            doist.recur(deeds=deeds)
            if count > 10:
                raise Exception("Delegatee never saw the successful anchor")