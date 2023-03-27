# -*- encoding: utf-8 -*-
"""
KERI
keria.app.keeping module

"""
from keri import kering
from keri.app.keeping import PrePrm, PreSit, Algos, PubLot, PubSet, riKey
from keri.core import coring
from keri.core.coring import Tiers
from keri.help import helping


class RemoteManager:
    def __init__(self, hby, ks=None):
        self.hby = hby
        self.ks = ks

    def incept(self, pre, verfers, digers, *, algo=Algos.salty, pidx=0, ridx=0, kidx=0, stem="",
               tier=Tiers.low, prxs=None, nxts=None, smids=None, rmids=None):

        smids = smids if smids is not None else []
        rmids = rmids if rmids is not None else []

        # Secret to encrypt here
        pp = PrePrm(pidx=pidx,
                    algo=algo,
                    salt='',
                    stem=stem,
                    tier=tier)

        dt = helping.nowIso8601()
        ps = PreSit(
            new=PubLot(pubs=[verfer.qb64 for verfer in verfers],
                       ridx=ridx, kidx=kidx, dt=dt),
            nxt=PubLot(pubs=[diger.qb64 for diger in digers],
                       ridx=ridx + 1, kidx=kidx + len(verfers), dt=dt))

        if not self.ks.pres.put(pre, val=coring.Prefixer(qb64=pre)):
            raise ValueError("Already incepted pre={}.".format(pre.decode("utf-8")))

        if not self.ks.prms.put(pre, val=pp):
            raise ValueError("Already incepted prm for pre={}.".format(pre.decode("utf-8")))

        if not self.ks.sits.put(pre, val=ps):
            raise ValueError("Already incepted sit for pre={}.".format(pre.decode("utf-8")))

        self.ks.pubs.put(riKey(pre, ri=ridx), val=PubSet(pubs=ps.new.pubs))
        self.ks.pubs.put(riKey(pre, ri=ridx+1), val=PubSet(pubs=ps.nxt.pubs))

        if prxs is not None:
            if len(prxs) != len(verfers):
                raise ValueError("If encrypted private keys are provided, must match verfers")

            for idx, prx in enumerate(prxs):
                cipher = coring.Cipher(qb64=prx)
                self.ks.prxs.put(keys=verfers[idx].qb64b, val=cipher)

        if nxts is not None:
            if len(nxts) != len(digers):
                raise ValueError("If encrypted private keys are provided, must match verfers")

            for idx, prx in enumerate(nxts):
                cipher = coring.Cipher(qb64=prx)
                self.ks.nxts.put(keys=digers[idx].qb64b, val=cipher)

        self.saveMids(pre, smids, self.ks.smids)
        self.saveMids(pre, rmids, self.ks.rmids)

    def saveMids(self, pre, mids, db):
        for smid in mids:
            mid = smid['i']
            if mid not in self.hby.kevers:
                raise kering.ConfigurationError(f"unknown group member {mid}")

            mkever = self.hby.kevers[mid]  # get key state for given member

            sn = smid['s'] if 's' in smid else mkever.sn
            prefixer = coring.Prefixer(qb64=mid)
            seqner = coring.Seqner(sn=sn)

            db.add(pre, val=(prefixer, seqner))

    def keyParams(self, pre):
        if (pp := self.ks.prms.get(pre)) is None:
            return {}

        if (ps := self.ks.sits.get(pre)) is None:
            raise ValueError("Attempt to load nonexistent pre={}.".format(pre))

        prxs = []
        for pub in ps.new.pubs:
            if (prx := self.ks.prxs.get(keys=pub)) is not None:
                prxs.append(prx)

        nxts = []
        for pub in ps.nxt.pubs:
            if (nxt := self.ks.nxts.get(keys=pub)) is not None:
                nxts.append(nxt)

        smids = self.ks.smids.get(pre)
        rmids = self.ks.rmids.get(pre)

        return dict(
            salt=dict(
                algo=pp.algo,
                stem=pp.stem,
                pidx=pp.pidx,
                tier=pp.tier
            ),
            rand=dict(
                prxs=[prx.qb64 for prx in prxs],
                nxts=[nxt.qb64 for nxt in nxts],
            ),
            group=dict(
                smids=[dict(i=prefixer.qb64, s=seqner.sn) for (prefixer, seqner) in smids],
                rmids=[dict(i=prefixer.qb64, s=seqner.sn) for (prefixer, seqner) in rmids],
            )
        )


def loadEnds(app):
    pass


class KeeperEnd:

    def __init__(self, ks):
        self.ks = ks
