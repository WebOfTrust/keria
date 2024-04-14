# -*- encoding: utf-8 -*-
"""
KERI
keria.core.keeping module

"""
from dataclasses import dataclass, asdict, field

from keri.app.keeping import PreSit, Algos, PubLot, PubSet
from keri import core
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
    sxlt: str = ''  # qualified b64 encoded AID salt
    pidx: int = 0  # prefix index for this keypair sequence
    kidx: int = 0  # key index for this keypair sequence
    stem: str = ''  # default unique path stem for salty algo
    tier: str = ''  # security tier for stretch index salty algo
    dcode: str = ''  # next digest hasing code
    icodes: list = field(default_factory=list)  # current signing key seed codes
    ncodes: list = field(default_factory=list)  # next key seed codes
    transferable: bool = False

    def __iter__(self):
        return iter(asdict(self))


class RemoteKeeper(dbing.LMDBer):
    """
    RemoteKeeper stores data for Salty or Randy Encrypted edge key generation.

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
                                     klas=core.Cipher)
        self.nxts = subing.CesrSuber(db=self,
                                     subkey='nxts.',
                                     klas=core.Cipher)
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
    def __init__(self, hby, rb: RemoteKeeper = None):
        self.hby = hby
        self.rb = rb if rb is not None else RemoteKeeper(name=hby.name,
                                                         base=hby.base,
                                                         temp=hby.temp,
                                                         reopen=True,
                                                         clear=False,
                                                         headDirPath=hby.db.headDirPath)

    def get(self, algo: Algos = None, pre=None):
        if pre is not None:
            if (pp := self.rb.pres.get(pre)) is None:
                raise ValueError("Attempt to load nonexistent pre={}.".format(pre))
            algo = pp.algo

        match algo:
            case Algos.salty:
                return SaltyManager(rb=self.rb)
            case Algos.randy:
                return RandyManager(rb=self.rb)
            case Algos.group:
                return GroupManager(rb=self.rb, rm=self)
            case _:
                return ExternKeeper(rb=self.rb)

    @property
    def sxlt(self):
        return self.rb.gbls.get("sxlt")

    @sxlt.setter
    def sxlt(self, sxlt):
        self.rb.gbls.pin("sxlt", sxlt)

    def delete_sxlt(self):
        return self.rb.gbls.rem("sxlt")


class SaltyManager:

    def __init__(self, rb: RemoteKeeper):
        self.rb = rb

    def incept(self, pre, *, icodes, ncodes, sxlt, dcode=MtrDex.Blake3_256, pidx=0, kidx=0, stem="", tier=Tiers.low,
               transferable=False):

        pp = Prefix(
            pidx=pidx,
            algo=Algos.salty
        )

        sp = SaltyPrm(sxlt=sxlt,
                      pidx=pidx,
                      kidx=kidx,
                      stem=stem,
                      tier=tier,
                      icodes=icodes,
                      ncodes=ncodes,
                      dcode=dcode,
                      transferable=transferable
                      )

        if not self.rb.pres.put(pre, val=pp):
            raise ValueError("Already incepted pre={}.".format(pre))

        if not self.rb.sprms.put(pre, val=sp):
            raise ValueError("Already incepted prm for pre={}.".format(pre))

    def rotate(self, pre, ncodes, pidx, kidx, stem, sxlt, icodes, tier, transferable, dcode=MtrDex.Blake3_256):
        if (pp := self.rb.pres.get(pre)) is None or pp.algo != Algos.salty:
            raise ValueError("Attempt to rotate nonexistent or invalid pre={}.".format(pre))

        if (sp := self.rb.sprms.get(pre)) is None:
            raise ValueError("Attempt to rotate nonexistent or invalid pre={}.".format(pre))

        sp = SaltyPrm(pidx=pidx,
                      sxlt=sxlt,
                      kidx=kidx,
                      stem=stem,
                      tier=sp.tier,
                      icodes=sp.icodes,
                      ncodes=ncodes,
                      dcode=dcode,
                      transferable=transferable
                      )

        if not self.rb.sprms.pin(pre, val=sp):
            raise ValueError("Unable to rotate salty prms for pre={}.".format(pre))

    def params(self, pre):
        if (pp := self.rb.pres.get(pre)) is None or pp.algo != Algos.salty:
            raise ValueError("Attempt to load nonexistent or invalid pre={}.".format(pre))

        if (pp := self.rb.sprms.get(pre)) is None:
            raise ValueError("Attempt to load nonexistent pre={}.".format(pre))

        prms = dict(
            salty=asdict(pp)
        )

        return prms


class RandyManager:

    def __init__(self, rb: RemoteKeeper):
        self.rb = rb

    def incept(self, pre, verfers, digers, prxs, nxts, transferable):

        pp = Prefix(
            algo=Algos.randy
        )

        if not self.rb.pres.put(pre, val=pp):
            raise ValueError("Already incepted pre={}.".format(pre))

        dt = helping.nowIso8601()
        ps = PreSit(
            new=PubLot(pubs=[verfer.qb64 for verfer in verfers],
                       dt=dt),
            nxt=PubLot(pubs=[diger.qb64 for diger in digers],
                       dt=dt))

        if not self.rb.sits.put(pre, val=ps):
            raise ValueError("Already incepted sit for pre={}.".format(pre))

        # Secret to encrypt here
        if len(prxs) != len(verfers):
            raise ValueError("If encrypted private keys are provided, must match verfers")

        for idx, prx in enumerate(prxs):
            cipher = core.Cipher(qb64=prx)
            self.rb.prxs.put(keys=verfers[idx].qb64b, val=cipher)

        if nxts is not None:
            if len(nxts) != len(digers):
                raise ValueError("If encrypted private next keys are provided, must match digers")

            for idx, prx in enumerate(nxts):
                cipher = core.Cipher(qb64=prx)
                self.rb.nxts.put(keys=digers[idx].qb64b, val=cipher)

    def rotate(self, pre, verfers, digers, prxs, nxts, transferable):
        if (pp := self.rb.pres.get(pre)) is None or pp.algo != Algos.randy:
            raise ValueError("Attempt to rotate non-existant or invalid pre={}.".format(pre))

        dt = helping.nowIso8601()
        ps = PreSit(
            new=PubLot(pubs=[verfer.qb64 for verfer in verfers],
                       dt=dt),
            nxt=PubLot(pubs=[diger.qb64 for diger in digers],
                       dt=dt))

        if not self.rb.sits.pin(pre, val=ps):
            raise ValueError("Already incepted sit for pre={}.".format(pre))

        # Secret to encrypt here
        if len(prxs) != len(verfers):
            raise ValueError("If encrypted private keys are provided, must match verfers")

        for idx, prx in enumerate(prxs):
            cipher = core.Cipher(qb64=prx)
            self.rb.prxs.put(keys=verfers[idx].qb64b, val=cipher)

        if nxts is not None:
            if len(nxts) != len(digers):
                raise ValueError("If encrypted private keys are provided, must match verfers")

            for idx, prx in enumerate(nxts):
                cipher = core.Cipher(qb64=prx)
                self.rb.nxts.put(keys=digers[idx].qb64b, val=cipher)

    def params(self, pre):
        if (pp := self.rb.pres.get(pre)) is None or pp.algo != Algos.randy:
            raise ValueError("Attempt to load nonexistent or invalid pre={}.".format(pre))

        prxs = []
        if (ps := self.rb.sits.get(pre)) is None:
            raise ValueError("Attempt to load nonexistent pre={}.".format(pre))

        for pub in ps.new.pubs:
            if (prx := self.rb.prxs.get(keys=pub)) is not None:
                prxs.append(prx)

        nxts = []
        for pub in ps.nxt.pubs:
            if (nxt := self.rb.nxts.get(keys=pub)) is not None:
                nxts.append(nxt)

        prms = dict(
            randy=dict(
                prxs=[prx.qb64 for prx in prxs],
                nxts=[nxt.qb64 for nxt in nxts],
            ),
        )

        return prms


class GroupManager:

    def __init__(self, rb: RemoteKeeper, rm: RemoteManager):
        self.rb = rb
        self.rm = rm

    def incept(self, pre, mpre, verfers, digers):
        pp = Prefix(
            algo=Algos.group
        )

        if not self.rb.pres.put(pre, val=pp):
            raise ValueError("Already incepted pre={}.".format(pre))

        if not self.rb.mhabs.put(pre, val=coring.Prefixer(qb64=mpre)):
            raise ValueError("Already incepted pre={}.".format(pre))

        dt = helping.nowIso8601()
        ps = PreSit(
            new=PubLot(pubs=[verfer.qb64 for verfer in verfers],
                       dt=dt),
            nxt=PubLot(pubs=[diger.qb64 for diger in digers],
                       dt=dt))

        if not self.rb.sits.put(pre, val=ps):
            raise ValueError("Already incepted sit for pre={}.".format(pre))

    def rotate(self, pre, verfers, digers):
        if (pp := self.rb.pres.get(pre)) is None or pp.algo != Algos.group:
            raise ValueError(f"Attempt to rotate nonexistant or invalid  pre={pre}, algo={pp.algo}.")

        dt = helping.nowIso8601()
        ps = PreSit(
            new=PubLot(pubs=[verfer.qb64 for verfer in verfers],
                       dt=dt),
            nxt=PubLot(pubs=[diger.qb64 for diger in digers],
                       dt=dt))

        if not self.rb.sits.pin(pre, val=ps):
            raise ValueError(f"Error saving sit rotating pre={pre}.")

    def params(self, pre):
        if (pp := self.rb.pres.get(pre)) is None or pp.algo != Algos.group:
            raise ValueError(f"Attempt to load nonexistent or invalid pre={pre}.")

        if (mpre := self.rb.mhabs.get(pre)) is None:
            raise ValueError("Attempt to load nonexistent pre={}.".format(pre))

        if (ps := self.rb.sits.get(pre)) is None:
            raise ValueError(f"Attempt to load invalid sit for pre={pre}.")

        prms = dict(
            group=dict(
                mhab=self.rm.get(pre=mpre.qb64).params(mpre.qb64),
                keys=[verfer for verfer in ps.new.pubs],
                ndigs=[diger for diger in ps.nxt.pubs]
            )
        )

        return prms


class ExternKeeper:

    def __init__(self, rb: RemoteKeeper):
        self.rb = rb

    def incept(self, **kwargs):
        pass
