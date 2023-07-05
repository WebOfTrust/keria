# -*- encoding: utf-8 -*-
"""
KERIA
keria.db.basing module

"""
from dataclasses import dataclass

from keri.core import coring
from keri.db import dbing, subing, koming


SCALAR_TYPES = ("string", "number")

ISSUER_FIELD = coring.Pather(path=['i'])
ISSUEE_FIELD = coring.Pather(path=['a', 'i'])
SCHEMA_FIELD = coring.Pather(path=['s'])
REGISTRY_FIELD = coring.Pather(path=['ri'])


@dataclass
class IndexRecord:
    """ Registry Key keyed by Registry name
    """
    subkey: str
    paths: list


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


class Seeker(dbing.LMDBer):
    """
    Seeker indexes all credentials in the KERIpy `saved` Creder database.

    Static indexes are created for issued by/schema and issued to/schema and dynamic indexes are
    created for all top level scalar valued fields in the credential payload ('a' field).  The Seeker
    uses the schema of each credential to determine the payload fields to index by.

    """

    TailDirPath = "keri/seekdb"
    AltTailDirPath = ".keri/seekdb"
    TempPrefix = "keri_seekdb_"
    MaxNamedDBs = 50

    def __init__(self, db, reger, headDirPath=None, perm=None, reopen=False, **kwa):
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


        """
        self.db = db
        self.reger = reger
        self.indexes = dict()

        self.schIdx = None
        self.dynIdx = None

        super(Seeker, self).__init__(headDirPath=headDirPath, perm=perm,
                                     reopen=reopen, **kwa)

    def reopen(self, **kwa):
        super(Seeker, self).reopen(**kwa)

        # List of indexs for a given schema
        self.schIdx = subing.IoSetSuber(db=self, subkey="schIdx.")
        # List of dynamically created indexes to be recreated at load
        self.dynIdx = koming.Komer(db=self,
                                   subkey='dynIdx.',
                                   schema=IndexRecord, )

        for name, idx in self.dynIdx.getItemIter():
            self.indexes[name] = subing.CesrDupSuber(db=self, subkey=idx.subkey, klas=coring.Saider)

        # Create persistent Indexes if they don't already exist
        self.createIndex(SCHEMA_FIELD.qb64)
        self.createIndex(REGISTRY_FIELD.qb64)

        # Index of credentials by issuer/issuee.
        for field in (ISSUER_FIELD, ISSUEE_FIELD):
            self.createIndex(field.qb64)
            subkey = f"{field.qb64}.{SCHEMA_FIELD.qb64}"
            self.createIndex(subkey)

    def createIndex(self, key):
        if self.dynIdx.get(keys=(key,)) is None:
            self.indexes[key] = subing.CesrDupSuber(db=self, subkey=key, klas=coring.Saider)
            self.dynIdx.pin(keys=(key,), val=IndexRecord(subkey=key, paths=[key]))

    def index(self, said):

        if (saider := self.reger.saved.get(keys=(said,))) is None:
            raise ValueError(f"{said} is not a verified credential")

        creder = self.reger.creds.get(keys=(saider.qb64, ))
        saider = coring.Saider(qb64b=creder.saidb)

        # Load schema index and if not indexed in schIdx, index it.
        schemaSaid = creder.schema
        if (indexes := self.schIdx.get(keys=(schemaSaid,))) is None:
            indexes = self.generateIndexes(schemaSaid)

        for index in indexes:
            db = self.indexes[index]
            idx = self.dynIdx.get(keys=(index,))
            values = []
            for path in idx.paths:
                pather = coring.Pather(qb64=path)
                values.append(pather.resolve(creder.crd))

            value = "".join(values)
            print(f"for {idx.paths}, {value} -> {saider}")
            db.add(keys=(value,), val=saider)

    def generateIndexes(self, said):
        """ Parse schema of said, create schIdx entry keyed to said of schema and the subkey indexes in
        self.indexes

        """
        if (schemer := self.db.schema.get(keys=(said,))) is None:
            raise ValueError(f"{said} is not a valid schema SAID to index")

        properties = schemer.sed["properties"]
        payload = properties['a']
        if isinstance(payload, list):
            for p in payload:
                if p["type"] == "object":
                    payload = p
                    break

        if not isinstance(payload, dict):
            raise ValueError(f"schema with SAID={said} is not value, no payload of values")

        properties = payload["properties"]

        attestation = 'i' not in payload

        # Assign single field ISSUER index and ISSUER/SCHEMA:
        self.schIdx.add(keys=(said,), val=ISSUER_FIELD.qb64b)
        subkey = f"{ISSUER_FIELD.qb64}.{SCHEMA_FIELD.qb64}"
        self.schIdx.add(keys=(said,), val=subkey.encode("UTF-8"))

        # Assign single field ISSUEE index and ISSUEE/SCHEMA if needed
        if not attestation:
            self.schIdx.add(keys=(said,), val=ISSUEE_FIELD.qb64b)
            subkey = f"{ISSUEE_FIELD.qb64}.{SCHEMA_FIELD.qb64}"
            self.schIdx.add(keys=(said,), val=subkey.encode("UTF-8"))

        for p, val in properties.items():
            if val["type"] not in SCALAR_TYPES:
                continue

            pather = coring.Pather(path=['a', p])
            if pather.qb64 not in self.indexes:
                self.indexes[pather.qb64] = subing.CesrDupSuber(db=self, subkey=pather.qb64, klas=coring.Saider)
                idx = IndexRecord(subkey=pather.qb64, paths=[pather.qb64])
                self.dynIdx.pin(keys=(pather.qb64,), val=idx)
            self.schIdx.add(keys=(said,), val=pather.qb64b)

            for field in (ISSUER_FIELD, ISSUEE_FIELD, SCHEMA_FIELD):
                subkey = f"{field.qb64}.{pather.qb64}"
                if subkey not in self.indexes:
                    self.indexes[subkey] = subing.CesrDupSuber(db=self, subkey=subkey, klas=coring.Saider)
                    idx = IndexRecord(subkey=subkey, paths=[field.qb64, pather.qb64])
                    self.dynIdx.pin(keys=(subkey,), val=idx)

                self.schIdx.add(keys=(said,), val=subkey)

        return [index for index in self.schIdx.get(keys=(said,))]
