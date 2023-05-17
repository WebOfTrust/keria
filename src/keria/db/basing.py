# -*- encoding: utf-8 -*-
"""
KERIA
keria.db.basing module

"""
from keri.core import coring
from keri.db import dbing, subing


class AgencyBaser(dbing.LMDBer):
    """
    Agency database for tracking Agent tenants in this KERIA instance.

    """

    TailDirPath = "keri/adb"
    AltTailDirPath = ".keri/adb"
    TempPrefix = "keri_adb_"
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
        if perm is None:
            perm = self.Perm  # defaults to restricted permissions for non temp

        self.agnt = None
        self.ctrl = None
        self.aids = None

        super(AgencyBaser, self).__init__(headDirPath=headDirPath, perm=perm,
                                          reopen=reopen, **kwa)

    def reopen(self, **kwa):
        """
        Open sub databases
        """
        self.opened = super(AgencyBaser, self).reopen(**kwa)

        # Create by opening first time named sub DBs within main DB instance
        # Names end with "." as sub DB name must include a non Base64 character
        # to avoid namespace collisions with Base64 identifier prefixes.

        self.agnt = subing.CesrSuber(db=self, subkey='agnt.', klas=coring.Prefixer)
        self.ctrl = subing.CesrSuber(db=self, subkey='ctrl.', klas=coring.Prefixer)
        self.aids = subing.CesrSuber(db=self,
                                     subkey='aids.',
                                     klas=coring.Prefixer)
