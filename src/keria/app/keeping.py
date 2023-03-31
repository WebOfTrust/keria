# -*- encoding: utf-8 -*-
"""
KERI
keria.app.keeping module

"""
from dataclasses import dataclass, asdict, field

from keri import kering
from keri.app.keeping import PreSit, Algos, PubLot, PubSet, riKey
from keri.core import coring
from keri.core.coring import Tiers, MtrDex
from keri.db import dbing, subing, koming
from keri.help import helping


@dataclass()
class Prefix:
    pidx: int = 0  # prefix index for this keypair sequence
    algo: str = Algos.salty  # salty default uses indices and salt to create new key pairs


@dataclass()
class SaltyPrm:
    """
    Salty prefix's parameters for creating new key pairs
    """
    pidx: int = 0  # prefix index for this keypair sequence
    algo: str = Algos.salty  # salty default uses indices and salt to create new key pairs
    salt: str = ''  # empty salt  used for salty algo.
    stem: str = ''  # default unique path stem for salty algo
    tier: str = ''  # security tier for stretch index salty algo
    dcode: str = ''  # next digest hasing code
    icodes: list = field(default_factory=list)  # current signing key seed codes
    ncodes: list = field(default_factory=list)  # next key seed codes

    def __iter__(self):
        return iter(asdict(self))


class RemoteKeeper(dbing.LMDBer):
    """
    RemoteKeeper stores data for Salty o rRandy Encrypted edge key generation.

    """

    TailDirPath = "keri/rks"
    AltTailDirPath = ".keri/rks"
    TempPrefix = "keri_rks_"
    MaxNamedDBs = 10

    def __init__(self, headDirPath=None, perm=None, reopen=False, **kwa):
        """
        Setup named sub databases.

        Inherited Parameters:
            name is str directory path name differentiator for main database
                When system employs more than one keri database, name allows
                differentiating each instance by name
                default name='main'
            temp is boolean, assign to .temp
                True then open in temporary directory, clear on close
                Othewise then open persistent directory, do not clear on close
                default temp=False
            headDirPath is optional str head directory pathname for main database
                If not provided use default .HeadDirpath
                default headDirPath=None so uses self.HeadDirPath
            perm is numeric optional os dir permissions mode
                default perm=None so do not set mode
            reopen is boolean, IF True then database will be reopened by this init
                default reopen=True

        Notes:

        dupsort=True for sub DB means allow unique (key,pair) duplicates at a key.
        Duplicate means that is more than one value at a key but not a redundant
        copies a (key,value) pair per key. In other words the pair (key,value)
        must be unique both key and value in combination.
        Attempting to put the same (key,value) pair a second time does
        not add another copy.

        Duplicates are inserted in lexocographic order by value, insertion order.

        """
        self.pubs = None
        self.sits = None
        self.sprms = None
        self.pres = None
        self.mhabs = None
        self.nxts = None
        self.prxs = None
        self.gbls = None
        if perm is None:
            perm = self.Perm  # defaults to restricted permissions for non temp

        super(RemoteKeeper, self).__init__(headDirPath=headDirPath, perm=perm,
                                           reopen=reopen, **kwa)

    def reopen(self, **kwa):
        """
        Open sub databases
        """
        self.opened = super(RemoteKeeper, self).reopen(**kwa)

        # Create by opening first time named sub DBs within main DB instance
        # Names end with "." as sub DB name must include a non Base64 character
        # to avoid namespace collisions with Base64 identifier prefixes.

        self.gbls = subing.Suber(db=self, subkey='gbls.')
        self.prxs = subing.CesrSuber(db=self,
                                     subkey='prxs.',
                                     klas=coring.Cipher)
        self.nxts = subing.CesrSuber(db=self,
                                     subkey='nxts.',
                                     klas=coring.Cipher)
        self.mhabs = subing.CesrSuber(db=self,
                                      subkey='mhabs.',
                                      klas=coring.Prefixer)
        self.pres = koming.Komer(db=self,
                                 subkey='pres.',
                                 schema=Prefix, )  # New Prefix
        self.sprms = koming.Komer(db=self,
                                  subkey='sprms.',
                                  schema=SaltyPrm, )  # New Salty Parameters
        self.sits = koming.Komer(db=self,
                                 subkey='sits.',
                                 schema=PreSit, )  # Prefix Situation
        self.pubs = koming.Komer(db=self,
                                 subkey='pubs.',
                                 schema=PubSet, )  # public key set at pre.ridx
        return self.opened


class RemoteManager:
    def __init__(self, hby, ks: RemoteKeeper = None):
        self.hby = hby
        self.ks = ks if ks is not None else RemoteKeeper(name=hby.name,
                                                         base=hby.base,
                                                         temp=hby.temp,
                                                         reopen=True,
                                                         clear=False,
                                                         headDirPath=hby.ks.headDirPath)

    def salty(self, pre, *, icodes, ncodes, dcode=MtrDex.Blake3_256, pidx=0, stem="", tier=Tiers.low):

        pp = Prefix(
            pidx=pidx,
            algo=Algos.salty
        )

        # Secret to encrypt here
        sp = SaltyPrm(pidx=pidx,
                      salt='',
                      stem=stem,
                      tier=tier,
                      icodes=icodes,
                      ncodes=ncodes,
                      dcode=dcode
                      )

        if not self.ks.pres.put(pre, val=pp):
            raise ValueError("Already incepted pre={}.".format(pre))

        if not self.ks.sprms.put(pre, val=sp):
            raise ValueError("Already incepted prm for pre={}.".format(pre))

    def randy(self, pre, verfers, digers, pidx, prxs, nxts):

        pp = Prefix(
            pidx=pidx,
            algo=Algos.randy
        )

        if not self.ks.pres.put(pre, val=pp):
            raise ValueError("Already incepted pre={}.".format(pre))

        dt = helping.nowIso8601()
        ps = PreSit(
            new=PubLot(pubs=[verfer.qb64 for verfer in verfers],
                       dt=dt),
            nxt=PubLot(pubs=[diger.qb64 for diger in digers],
                       dt=dt))

        if not self.ks.sits.put(pre, val=ps):
            raise ValueError("Already incepted sit for pre={}.".format(pre))

        # Secret to encrypt here
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

    def group(self, pre, mpre, verfers, digers):
        pp = Prefix(
            pidx=0,
            algo=Algos.group
        )

        if not self.ks.pres.put(pre, val=pp):
            raise ValueError("Already incepted pre={}.".format(pre))

        if not self.ks.mhabs.put(pre, val=coring.Prefixer(qb64=mpre)):
            raise ValueError("Already incepted pre={}.".format(pre))

        dt = helping.nowIso8601()
        ps = PreSit(
            new=PubLot(pubs=[verfer.qb64 for verfer in verfers],
                       dt=dt),
            nxt=PubLot(pubs=[diger.qb64 for diger in digers],
                       dt=dt))

        if not self.ks.sits.put(pre, val=ps):
            raise ValueError("Already incepted sit for pre={}.".format(pre))

    def update(self, **kwargs):
        pass

    def keyParams(self, pre):
        if (pp := self.ks.pres.get(pre)) is None:
            raise ValueError("Attempt to load nonexistent pre={}.".format(pre))

        match pp.algo:
            case Algos.salty:
                if (pp := self.ks.sprms.get(pre)) is None:
                    raise ValueError("Attempt to load nonexistent pre={}.".format(pre))

                prms = dict(
                    salty=asdict(pp)
                )

            case Algos.randy:
                prxs = []
                if (ps := self.ks.sits.get(pre)) is None:
                    raise ValueError("Attempt to load nonexistent pre={}.".format(pre))

                for pub in ps.new.pubs:
                    if (prx := self.ks.prxs.get(keys=pub)) is not None:
                        prxs.append(prx)

                nxts = []
                for pub in ps.nxt.pubs:
                    if (nxt := self.ks.nxts.get(keys=pub)) is not None:
                        nxts.append(nxt)

                prms = dict(
                    randy=dict(
                        prxs=[prx.qb64 for prx in prxs],
                        nxts=[nxt.qb64 for nxt in nxts],
                    ),
                )
            case Algos.group:
                if (mpre := self.ks.mhabs.get(pre)) is None:
                    raise ValueError("Attempt to load nonexistent pre={}.".format(pre))

                if (ps := self.ks.sits.get(pre)) is None:
                    raise ValueError("Attempt to load invalid sit for pre={}.".format(pre))

                prms = dict(
                    group=dict(
                        keys=[verfer.qb64 for verfer in ps.new.pubs],
                        rmids=[diger.qb64 for diger in ps.nxt.pubs],
                    )
                )

                prms['mhab'] = self.keyParams(mpre.qb64)

            case _:
                raise ValueError(f"Invalid algo type for key={pre}: {pp.algo}")

        return prms


def loadEnds(app):
    pass


class KeeperEnd:

    def __init__(self, ks):
        self.ks = ks
