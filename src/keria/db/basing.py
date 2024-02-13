# -*- encoding: utf-8 -*-
"""
KERIA
keria.db.basing module

"""
from dataclasses import dataclass
from ordered_set import OrderedSet as oset

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

        # Sub-database keyed by qb64 controller AID mapping to the Prefixer object of the AID of an agent
        self.agnt = subing.CesrSuber(db=self, subkey='agnt.', klas=coring.Prefixer)

        # Sub-database keyed by qb64 agent AID mapping to the Prefixer object of the AID of an controller
        self.ctrl = subing.CesrSuber(db=self, subkey='ctrl.', klas=coring.Prefixer)

        # Sub-database keyed by qb64 AID mapping to the Prefixer object of the AID of its Agent
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
    MaxNamedDBs = 500

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
            key = ".".join(name)
            self.indexes[key] = subing.CesrDupSuber(db=self, subkey=idx.subkey, klas=coring.Saider)

        # Create persistent Indexes if they don't already exist
        self.createIndex(SCHEMA_FIELD.qb64)
        self.createIndex(REGISTRY_FIELD.qb64)

        # Index of credentials by issuer/issuee.
        for field in (ISSUER_FIELD, ISSUEE_FIELD):
            self.createIndex(field.qb64)
            subkey = f"{field.qb64}.{SCHEMA_FIELD.qb64}"
            self.createIndex(subkey)

    @property
    def table(self):
        return self.reger.saved

    def value(self, said):
        saider = self.reger.saved.get(keys=(said,))
        creder = self.reger.creds.get(keys=(saider.qb64,))
        return creder.sad

    def saidIter(self):
        return self.reger.saved.getItemIter()

    def createIndex(self, key):
        if self.dynIdx.get(keys=(key,)) is None:
            self.indexes[key] = subing.CesrDupSuber(db=self, subkey=key, klas=coring.Saider)
            self.dynIdx.pin(keys=(key,), val=IndexRecord(subkey=key, paths=[key]))

    def index(self, said):
        if (saider := self.reger.saved.get(keys=(said,))) is None:
            raise ValueError(f"{said} is not a verified credential")

        creder = self.reger.creds.get(keys=(saider.qb64,))
        saider = coring.Saider(qb64b=creder.saidb)

        # Load schema index and if not indexed in schIdx, index it.
        schemaSaid = creder.schema
        if not (indexes := self.schIdx.get(keys=(schemaSaid,))):
            indexes = self.generateIndexes(schemaSaid)

        for index in indexes:
            db = self.indexes[index]
            idx = self.dynIdx.get(keys=(index,))
            values = []
            for path in idx.paths:
                pather = coring.Pather(qb64=path)
                values.append(pather.resolve(creder.sad))

            value = "".join(values)
            db.add(keys=(value,), val=saider)

    def generateIndexes(self, said):
        """ Parse schema of said, create schIdx entry keyed to said of schema and the subkey indexes in
        self.indexes

        """
        if (schemer := self.db.schema.get(keys=(said,))) is None:
            raise ValueError(f"{said} is not a valid schema SAID to index")

        properties = schemer.sed["properties"]
        payload = properties['a']
        if "oneOf" in payload:
            oo = payload["oneOf"]
            for p in oo:
                if p["type"] == "object":
                    payload = p
                    break

        if not isinstance(payload, dict):
            raise ValueError(f"schema with SAID={said} is not value, no payload of values")

        properties = payload["properties"]

        attestation = 'i' not in properties

        # Assign single field Schema and ISSUER index and ISSUER/SCHEMA:
        self.schIdx.add(keys=(said,), val=SCHEMA_FIELD.qb64b)
        self.schIdx.add(keys=(said,), val=ISSUER_FIELD.qb64b)
        self.schIdx.add(keys=(said,), val=REGISTRY_FIELD.qb64b)
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

            subkey = f"{SCHEMA_FIELD.qb64}.{pather.qb64}"
            if subkey not in self.indexes:
                self.indexes[subkey] = subing.CesrDupSuber(db=self, subkey=subkey, klas=coring.Saider)
                idx = IndexRecord(subkey=subkey, paths=[SCHEMA_FIELD.qb64, pather.qb64])
                self.dynIdx.pin(keys=(subkey,), val=idx)
            self.schIdx.add(keys=(said,), val=subkey)

            for field in (ISSUER_FIELD, ISSUEE_FIELD):
                subkey = f"{field.qb64}.{pather.qb64}"
                if subkey not in self.indexes:
                    self.indexes[subkey] = subing.CesrDupSuber(db=self, subkey=subkey, klas=coring.Saider)
                    idx = IndexRecord(subkey=subkey, paths=[field.qb64, pather.qb64])
                    self.dynIdx.pin(keys=(subkey,), val=idx)

                self.schIdx.add(keys=(said,), val=subkey)

                subkey = f"{field.qb64}.{SCHEMA_FIELD.qb64}.{pather.qb64}"
                if subkey not in self.indexes:
                    self.indexes[subkey] = subing.CesrDupSuber(db=self, subkey=subkey, klas=coring.Saider)
                    idx = IndexRecord(subkey=subkey, paths=[field.qb64, SCHEMA_FIELD.qb64, pather.qb64])
                    self.dynIdx.pin(keys=(subkey,), val=idx)

                self.schIdx.add(keys=(said,), val=subkey)

        return [index for index in self.schIdx.get(keys=(said,))]

    def find(self, filtr, sort=None, skip=None, limit=None):
        return Cursor(seeker=self, filtr=filtr, sort=sort, skip=skip, limit=limit)


class ExnSeeker(dbing.LMDBer):
    """
    Seeker indexes all credentials in the KERIpy `saved` Creder database.

    Static indexes are created for issued by/schema and issued to/schema and dynamic indexes are
    created for all top level scalar valued fields in the credential payload ('a' field).  The Seeker
    uses the schema of each credential to determine the payload fields to index by.

    """

    TailDirPath = "keri/exndb"
    AltTailDirPath = ".keri/exndb"
    TempPrefix = "keri_exndb_"
    MaxNamedDBs = 36

    DATE_FIELD = coring.Pather(path=['dt'])
    SENDER_FIELD = coring.Pather(path=['i'])
    RECIPIENT_FIELD = coring.Pather(path=['a', 'i'])
    ROUTE_FIELD = coring.Pather(path=['r'])

    # Special field for IPEX messages... consider moving to IpexSeeker if needed
    SCHEMA = coring.Pather(path=['e', 'acdc', 's'])

    def __init__(self, db, headDirPath=None, perm=None, reopen=False, **kwa):
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
        self.indexes = dict()

        super(ExnSeeker, self).__init__(headDirPath=headDirPath, perm=perm,
                                        reopen=reopen, **kwa)

    def reopen(self, **kwa):
        super(ExnSeeker, self).reopen(**kwa)

        # List of dynamically created indexes to be recreated at load
        # Create persistent Indexes if they don't already exist
        fields = (self.ROUTE_FIELD, self.SENDER_FIELD, self.RECIPIENT_FIELD, self.DATE_FIELD, self.SCHEMA)
        # Index of credentials by issuer/issuee.
        for field in fields:
            self.createIndex(field.qb64)
            for subfield in fields:
                if field == subfield:
                    continue
                subkey = f"{field.qb64}.{subfield.qb64}"
                self.createIndex(subkey)

    @property
    def table(self):
        return self.db.exns

    def value(self, said):
        serder = self.db.exns.get(keys=(said,))
        return serder.ked

    def saidIter(self):
        for (said,), _ in self.db.exns.getItemIter():
            yield said

    def createIndex(self, key):
        self.indexes[key] = subing.CesrDupSuber(db=self, subkey=key, klas=coring.Saider)

    def index(self, said):
        if (serder := self.db.exns.get(keys=(said,))) is None:
            raise ValueError(f"{said} is not a valid exn")

        saider = coring.Saider(qb64b=serder.saidb)

        # Load schema index and if not indexed in schIdx, index it.
        for index, db in self.indexes.items():
            pathers = [coring.Pather(qb64=path) for path in index.split(".")]
            values = []
            for pather in pathers:
                try:
                    values.append(pather.resolve(serder.ked))
                except KeyError:
                    pass

            value = "".join(values)
            if not value:
                continue

            db.add(keys=(value,), val=saider)

    def find(self, filtr, sort=None, skip=None, limit=None):
        return Cursor(seeker=self, filtr=filtr, sort=sort, skip=skip, limit=limit)


class Cursor:

    def __init__(self, seeker, filtr=None, sort=None, skip=None, limit=None):
        self.filtr = filtr
        self.operators = operators(self.filtr)
        self.names = [op.name for op in self.operators]
        self.indexable = next((False for op in self.operators if not isinstance(op, Eq)), True)
        self.values = [op.value for op in self.operators]

        self.seeker = seeker
        self._sort = sort
        self._skip = skip if skip is not None else 0
        self._limit = limit if limit is not None else 25

        self.cur = None
        self.saids = None

    def __iter__(self):
        return self

    def __next__(self):
        if self.saids is None:
            self._query()

        if self.cur >= len(self.saids):
            raise StopIteration

        said = self.saids[self.cur]
        self.cur += 1
        return said

    def sort(self, sort):
        self._sort = sort
        return self

    def skip(self, skip):
        self._skip = skip
        return self

    def limit(self, limit):
        self._limit = limit
        return self

    def _query(self):
        self.cur = 0
        if len(self.filtr) == 0:
            self.saids = self.order([said for (said,), _ in self.seeker.table.getItemIter()])
        elif (saids := self.indexSearch()) is not None:
            self.saids = self.order(saids)
        elif (saids := self.indexScan()) is not None:
            self.saids = self.order(saids)
        else:
            saids = self.fullTableScan()
            self.saids = self.order(saids)

    def indexSearch(self):
        if len(self.operators) == 1 and self.operators[0].name in self.seeker.indexes:
            op = self.operators[0]
            idx = self.seeker.indexes[op.name]
            return op.index(idx)

        index = ".".join(self.names)
        if not (self.indexable and index in self.seeker.indexes):
            return None

        idx = self.seeker.indexes[index]
        val = "".join(self.values)
        return [val.qb64 for val in idx.getIter(keys=(val,))]

    def indexScan(self):
        use = []
        scan = []

        for idx, op in enumerate(self.operators):
            if op.name in self.seeker.indexes:
                use.append(op)
            else:
                scan.append(op)

        if len(use) == 0:
            return self.fullTableScan()

        idx = self.seeker.indexes[use[0].name]
        saids = oset(use[0].index(idx))
        if len(saids) == 0:
            return list()

        for i, op in enumerate(use[1:]):
            idx = self.seeker.indexes[op.name]
            nxt = oset(op.index(idx))
            saids &= nxt

        if len(scan) == 0:
            return list(saids)
        else:
            return self.tableScan(list(saids), scan)

    def fullTableScan(self):
        saids = [saider.qb64 for _, saider in self.seeker.saidIter()]
        return self.tableScan(saids, ops=self.operators)

    def tableScan(self, saids, ops):
        res = []
        for said in saids:
            val = self.seeker.value(said)
            for op in ops:
                if op(val):
                    res.append(said)

        return res

    def order(self, saids):
        if not self._sort:
            return self.slice(saids)

        if (res := self.indexOrder(saids)) is not None:
            return res
        else:
            return self.tableScanOrder(saids)

    def indexOrder(self, saids):
        index = ".".join([coring.Pather(bext=s).qb64 for s in self._sort])
        if index not in self.seeker.indexes:
            return None

        idx = self.seeker.indexes[index]
        ctx = idx.getItemIter()

        # Run off the values before start
        cur = 0
        while cur < self._skip:
            _, saider = next(ctx)
            if saider.qb64 in saids:
                cur += 1

        # Load values in order until we get enough (based on limit)
        res = []
        for _, saider in ctx:
            if saider.qb64 in saids:
                res.append(saider.qb64)

            if len(res) == self._limit:
                break

        return res

    def slice(self, saids):
        if self._skip >= len(saids):
            return []

        end = self._skip + self._limit
        return saids[self._skip:end]

    def tableScanOrder(self, saids):
        """ Should we bother implementing table scan sort order

        We have single field indexes for all fields in credentials so this situation will
        only occur if multiple fields are selected for which we don't have a multi-column
        index.  In that case, perhaps we raise an exception.

        For now, we'll just slice the results to honor skip and limit.

        """
        return self.slice(saids)


def operators(filtr):
    """ Executable operator factory method

     An factory for processing a filter dict and generating an array of
     executable operators to apply to a given credential search

    """
    # filtr = {"-a-i": {"$begins": "984"}}
    ops = []
    for f, v in filtr.items():
        if isinstance(v, dict):
            for op, val in v.items():
                match op:
                    case "$eq":
                        ops.append(Eq(field=f, value=val))
                    case "$begins":
                        ops.append(Begins(field=f, value=val))
            pass
        else:
            ops.append(Eq(field=f, value=v))

    return ops


class Eq:
    def __init__(self, field, value):
        self.field = field
        self.pather = coring.Pather(bext=self.field)
        self.value = value

    def __call__(self, *args, **kwargs):
        if len(args) != 1:
            raise ValueError(f"invalid argument length={len(args)} for equals operator, must be 2")

        val = self.pather.resolve(args[0])
        return val == self.value

    @property
    def name(self) -> str:
        return self.pather.qb64

    def index(self, idx):
        return [val.qb64 for val in idx.getIter(keys=(self.value,))]


class Begins:
    def __init__(self, field, value):
        self.field = field
        self.pather = coring.Pather(bext=self.field)

        if not isinstance(value, str):
            raise ValueError(f"invalid type={type(value)} for begins, must be `str`")
        self.value = value

    def __call__(self, *args, **kwargs):
        if len(args) != 1:
            raise ValueError(f"invalid argument length={len(args)} for begins operator, must be 2")

        val = self.pather.resolve(args[0])
        if not isinstance(val, str):
            raise ValueError(f"invalid type={type(args[0])} for begins, must be `str`")

        return val.startswith(self.value)

    def index(self, idx):
        return [val.qb64 for _, val in idx.getItemIter(keys=(self.value,))]

    @property
    def name(self) -> str:
        return self.pather.qb64
