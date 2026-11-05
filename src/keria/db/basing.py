# -*- encoding: utf-8 -*-
"""Agency database storage, search indexes, key codecs, and query execution."""

import hashlib
import math
import struct
from dataclasses import dataclass
from itertools import islice
from ordered_set import OrderedSet as oset
from keri.core import coring
from keri.db import dbing, subing, koming
from keria import keriaing

# JSON Schema payload types eligible for scalar search indexes.
SCALAR_TYPES = ("string", "number", "integer")

# Top-level credential issuer AID (distinct from the payload issuee).
ISSUER_FIELD = coring.Pather(path=["i"])
# Optional credential recipient AID in the attribute block.
ISSUEE_FIELD = coring.Pather(path=["a", "i"])
# Credential schema SAID used to scope schema-specific searches.
SCHEMA_FIELD = coring.Pather(path=["s"])
# Credential registry identifier used for registry searches.
REGISTRY_FIELD = coring.Pather(path=["ri"])


def tupleKey(values):
    """Hash a typed, length-framed tuple into a fixed-size equality key.

    Strings use UTF-8, integers decimal bytes, and finite floats binary64 bytes.
    Signed zero is normalized; other types are rejected. SHA-256 keeps even
    long compound strings below LMDB's key limit. Keys carry no sort order;
    prefix matching and ordering resolve the original credential values.
    """
    key = bytearray()
    for value in values:
        if type(value) is str:
            tag, raw = b"s", value.encode("utf-8")
        elif type(value) is int:
            tag, raw = b"i", str(value).encode("ascii")
        elif type(value) is float and math.isfinite(value):
            tag, raw = b"f", struct.pack(">d", 0.0 if value == 0.0 else value)
        else:
            raise ValueError(f"Unsupported index scalar: {type(value).__name__}")
        key.extend(tag + len(raw).to_bytes(4, "big") + raw)
    return hashlib.sha256(key).hexdigest()


@dataclass
class IndexRecord:
    """Persist a named index's LMDB subkey and ordered qb64 field paths.

    Path order determines the field order in compound equality keys.
    """

    subkey: str
    paths: list


class AgencyBaser(dbing.LMDBer):
    """
    Agency database for tracking Agent tenants and their managed identifiers in this KERIA instance.

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
                Otherwise then open persistent directory, do not clear on close
                default temp=False
            headDirPath is optional str head directory pathname for main database
                If not provided use default .HeadDirpath
                default headDirPath=None so uses self.HeadDirPath
            perm is numeric optional os dir permissions mode
                default perm=None so do not set mode
            reopen is boolean, IF True then database will be reopened by this init
                default reopen=True

        Attributes:
            .agnt values are Prefixer of Agent AID
                keyed by controller AID (caid).
                Maps Controller AIDs to their Signify Agent AID (agent.pre).
            .ctrl values are Prefixer of Controller AID (caid)
                keyed by Agent AID.
                Maps Agent AIDs to their Signify Controller AID (caid).
            .aids values are Prefixer of Controller AID (caid)
                keyed by managed AID.
                Maps managed AIDs to their Signify Controller AID (caid).

        Notes:
            dupsort=True for sub DB means allow unique (key,pair) duplicates at a key.
            Duplicate means that is more than one value at a key but not a redundant
            copies a (key,value) pair per key. In other words the pair (key,value)
            must be unique both key and value in combination.
            Attempting to put the same (key,value) pair a second time does
            not add another copy.

            Duplicates are inserted in lexicographic order by value, insertion order.
        """
        if perm is None:
            perm = self.Perm  # defaults to restricted permissions for non temp

        self.agnt = None
        self.ctrl = None
        self.aids = None

        super(AgencyBaser, self).__init__(
            headDirPath=headDirPath, perm=perm, reopen=reopen, **kwa
        )

    def reopen(self, **kwa):
        """
        Open sub databases
        """
        self.opened = super(AgencyBaser, self).reopen(**kwa)

        # Create by opening first time named sub DBs within main DB instance
        # Names end with "." as sub DB name must include a non Base64 character
        # to avoid namespace collisions with Base64 identifier prefixes.

        # Sub-database keyed by qb64 controller AID mapping to the Prefixer object of the AID of an agent
        self.agnt = subing.CesrSuber(db=self, subkey="agnt.", klas=coring.Prefixer)

        # Sub-database keyed by qb64 agent AID mapping to the Prefixer object of the AID of an controller
        self.ctrl = subing.CesrSuber(db=self, subkey="ctrl.", klas=coring.Prefixer)

        # Sub-database keyed by qb64 AID mapping to the Prefixer object of the AID of its Agent
        self.aids = subing.CesrSuber(db=self, subkey="aids.", klas=coring.Prefixer)


class Seeker(dbing.LMDBer):
    """Seeker indexes all credentials in the KERIpy `saved` Creder database.

    Static indexes are created for issued by/schema and issued to/schema and dynamic indexes are
    created for all top level scalar valued fields in the credential payload ('a' field).  The Seeker
    uses the schema of each credential to determine the payload fields to index by.

    Schema definitions select scalar payload indexes; entries map typed keys to
    credential SAIDs. SeekerDoer drives startup reconciliation and recovery.
    Queries fail while reconciliation or recorded indexing failures remain.
    """

    # LMDB storage paths, temporary-directory prefix, and named-index capacity.
    TailDirPath = "keri/seekdb"
    AltTailDirPath = ".keri/seekdb"
    TempPrefix = "keri_seekdb_"
    MaxNamedDBs = 500

    def __init__(self, db, reger, headDirPath=None, perm=None, reopen=False, **kwa):
        """Bind schema storage (db) and credential storage (reger).

        Pass reopen=True to open immediately; LMDBer kwargs such as name/temp
        select persistent or test storage. Construction does not run repair.

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

        self.failures = {}
        self.pending = {}
        self.reconciling = False
        self.schIdx = None
        self.dynIdx = None

        super(Seeker, self).__init__(
            headDirPath=headDirPath, perm=perm, reopen=reopen, **kwa
        )

    def reopen(self, **kwa):
        """Open stored index definitions and base tables without rebuilding entries."""
        super(Seeker, self).reopen(**kwa)

        # List of indexs for a given schema
        self.schIdx = subing.IoSetSuber(db=self, subkey="schIdx.")
        # List of dynamically created indexes to be recreated at load
        self.dynIdx = koming.Komer(
            db=self,
            subkey="dynIdx.",
            schema=IndexRecord,
        )

        for name, idx in self.dynIdx.getItemIter():
            key = ".".join(name)
            self.indexes[key] = subing.CesrDupSuber(
                db=self, subkey=idx.subkey, klas=coring.Saider
            )

        for key in self._baseIndexes():
            self.createIndex(key)

    @property
    def table(self):
        """Expose accepted credential SAIDs as the query candidate table."""
        return self.reger.saved

    def value(self, said):
        """Resolve an accepted credential SAID to its SAD for query evaluation."""
        saider = self.reger.saved.get(keys=(said,))
        creder = self.reger.creds.get(keys=(saider.qb64,))
        return creder.sad

    def saidIter(self):
        """Yield accepted (key tuple, Saider) pairs for fallback searches."""
        return self.reger.saved.getItemIter()

    def createIndex(self, key):
        """Install the canonical paths for a named single or compound index."""
        record = IndexRecord(subkey=key, paths=key.split("."))
        old = self.dynIdx.get(keys=(key,))
        if key not in self.indexes or (old and old.subkey != key):
            self.indexes[key] = subing.CesrDupSuber(
                db=self, subkey=key, klas=coring.Saider
            )
        if old != record:
            self.dynIdx.pin(keys=(key,), val=record)

    def _payload(self, said):
        """Resolve the schema's attribute object, including the ACDC oneOf form."""
        schemer = self.db.schema.get(keys=(said,))
        if schemer is None:
            raise keriaing.MissingSchemaError(f"Missing credential schema {said}")
        payload = schemer.sed["properties"]["a"]
        if "oneOf" in payload:
            payload = next(
                (item for item in payload["oneOf"] if item.get("type") == "object"),
                None,
            )
        if not isinstance(payload, dict) or "properties" not in payload:
            raise ValueError(f"Schema {said} has no supported attribute object")
        return payload

    @staticmethod
    def _baseIndexes(issuee=True):
        """Return canonical base names, omitting recipient indexes for attestations."""
        issuer, schema = ISSUER_FIELD.qb64, SCHEMA_FIELD.qb64
        names = [schema, issuer, REGISTRY_FIELD.qb64, f"{issuer}.{schema}"]
        if issuee:
            names.extend([ISSUEE_FIELD.qb64, f"{ISSUEE_FIELD.qb64}.{schema}"])
        return names

    @classmethod
    def _definitions(cls, payload):
        """Derive the complete ordered index names without changing persistent state."""
        issuer, issuee = ISSUER_FIELD.qb64, ISSUEE_FIELD.qb64
        schema = SCHEMA_FIELD.qb64
        fields = [issuer] if "i" not in payload["properties"] else [issuer, issuee]
        names = cls._baseIndexes(issuee=issuee in fields)
        for name, definition in payload["properties"].items():
            if "type" not in definition:
                raise ValueError(
                    f"Unsupported attribute schema for {name}: missing type"
                )
            if not isinstance(definition["type"], str):
                raise ValueError(f"Unsupported attribute type declaration for {name}")
            if definition["type"] not in SCALAR_TYPES:
                continue
            path = coring.Pather(path=["a", name]).qb64
            names.extend([path, f"{schema}.{path}"])
            for field in fields:
                names.extend([f"{field}.{path}", f"{field}.{schema}.{path}"])
        return list(dict.fromkeys(names))

    def generateIndexes(self, said):
        """Validate all definitions before installing canonical records and schema refs.

        Always derive from the schema: a nonempty stored list is not evidence of
        completeness after a crash or failed generation. Repeated calls repair
        retained definitions as well as missing ones.
        """
        names = self._definitions(self._payload(said))
        for name in names:
            self.createIndex(name)
        if self.schIdx.get(keys=(said,)) != names:
            self.schIdx.pin(keys=(said,), vals=names)
        return names

    def _entries(self, said):
        """Prepare all keys before writing; omit indexes with absent optional fields."""
        saider = self.reger.saved.get(keys=(said,))
        if saider is None:
            raise ValueError(f"{said} is not a verified credential")
        creder = self.reger.creds.get(keys=(said,))
        if creder is None:
            raise ValueError(f"Accepted credential {said} is missing")
        payload = self._payload(creder.schema)
        names = self.generateIndexes(creder.schema)
        entries = []
        for name in names:
            values = []
            for path in name.split("."):
                pather = coring.Pather(qb64=path)
                try:
                    values.append(pather.resolve(creder.sad))
                except KeyError:
                    if (
                        len(pather.path) == 2
                        and pather.path[0] == "a"
                        and pather.path[1] not in payload.get("required", [])
                    ):
                        break
                    raise
            else:
                entries.append((self.indexes[name], tupleKey(values), saider))
        return entries

    def index(self, said):
        """Index a saved credential after full validation, then retire its failure.

        Entry writes use separate transactions. Startup reconciliation removes
        partial writes after interruption; schema references never prove success.
        """
        for db, key, saider in self._entries(said):
            db.add(keys=(key,), val=saider)
        self._forget(said)

    def _forget(self, said):
        """Retire recovery state after successful indexing or intentional deletion."""
        self.failures.pop(said, None)
        self.pending.pop(said, None)

    def unindex(self, said):
        """Remove a saved credential's entries and retire its recovery state.

        Healthy indexes use the same tuple keys as writes. Failed or reconciling
        indexes fall back to a SAID scan so missing schemas and partial/legacy
        entries cannot prevent deletion. The caller deletes the Reger data.
        """
        if self.reger.saved.get(keys=(said,)) is None:
            raise ValueError(f"{said} is not a verified credential")
        entries = None
        if not self.reconciling and said not in self.failures:
            try:
                entries = self._entries(said)
            except Exception:
                # Cleanup must work even when definitions or values cannot be rebuilt.
                pass
        try:
            if entries is not None:
                for db, key, saider in entries:
                    db.rem(keys=(key,), val=saider)
            else:
                for db in self.indexes.values():
                    for keys, val in db.getItemIter():
                        if val.qb64 == said:
                            db.rem(keys=keys, val=val)
        except Exception as ex:
            self.failures[said] = ex
            raise
        self._forget(said)

    def process(self, said):
        """Attempt queued indexing; retain errors and retry only missing schemas.

        Return the failure for logging, or None on success/deletion. A stale cue
        for a credential no longer accepted has no projection to rebuild.
        """
        if self.reger.saved.get(keys=(said,)) is None:
            self._forget(said)
            return None
        try:
            self.index(said)
        except Exception as ex:
            self.pending.pop(said, None)
            self.failures[said] = ex
            if isinstance(ex, keriaing.MissingSchemaError):
                self.pending[said] = self.reger.creds.get(keys=(said,)).schema
            return ex
        return None

    def retry(self):
        """Check one pending schema round-robin; return an attempted SAID/error pair."""
        if not self.pending:
            return None
        said = next(iter(self.pending))
        schema = self.pending.pop(said)
        if self.reger.saved.get(keys=(said,)) is None:
            self._forget(said)
        elif self.reger.creds.get(keys=(said,)) is None:
            return said, self.process(said)
        elif self.db.schema.get(keys=(schema,)) is None:
            self.pending[said] = schema
        else:
            return said, self.process(said)
        return None

    def startRepair(self):
        """Gate queries immediately and return the startup iterator when work exists."""
        if next(self.reger.schms.getItemIter(), None) is not None:
            self.reconciling = True
            return self.reconcile()
        return None

    def failRepair(self, error):
        """Keep an interrupted startup visibly failed until a successful full repair."""
        self.reconciling = False
        self.failures["startup"] = error

    def reconcile(self):
        """Yield during discovery, cleanup and rebuilding of accepted schms entries.

        Clean the union of old and canonical index handles before rebuilding.
        Recheck acceptance after yields so concurrent deletions are not failures.
        Unused definition metadata is removed; physical named databases remain.
        """
        self.reconciling = True
        completed = False
        try:
            accepted, schemas = set(), set()
            for keys, saider in self.reger.schms.getItemIter():
                if self.reger.saved.get(keys=(saider.qb64,)) is not None:
                    schemas.add(keys[0])
                    accepted.add(saider.qb64)
                yield None
            old = list(self.indexes.values())
            for schema in schemas:
                try:
                    self.generateIndexes(schema)
                except Exception:
                    # Rebuilding each credential below retains/classifies the error.
                    pass
                yield None
            indexes = list(dict.fromkeys(old + list(self.indexes.values())))
            for db in indexes:
                for keys, val in db.getItemIter():
                    if val.qb64 in accepted:
                        db.rem(keys=keys, val=val)
                    yield None
            for said in accepted:
                self.process(said)
                yield said
            used = {name for _, name in self.schIdx.getItemIter()}
            base = set(self._baseIndexes())
            for keys, record in list(self.dynIdx.getItemIter()):
                name = ".".join(keys)
                if name not in used and name not in base:
                    self.dynIdx.rem(keys=keys)
                    self.indexes.pop(name, None)
            self.failures.pop("startup", None)
            completed = True
        finally:
            if not completed:
                self.failRepair(
                    keriaing.IndexNotReadyError("Reconciliation interrupted")
                )
            self.reconciling = False

    def find(self, filtr, sort=None, skip=None, limit=None):
        """Return a lazy SAID cursor for filters, sort fields, and pagination.

        Raise IndexNotReadyError during repair or unresolved failures. Query
        operators and unsupported ordering are checked at creation/iteration.
        """
        if self.reconciling:
            raise keriaing.IndexNotReadyError("Credential indexes are reconciling")
        if self.failures:
            details = ", ".join(
                f"{said} ({type(error).__name__})"
                for said, error in islice(self.failures.items(), 3)
            )
            raise keriaing.IndexNotReadyError(
                f"Credential indexes have {len(self.failures)} unresolved failures: {details}"
            )
        return CredentialCursor(
            seeker=self, filtr=filtr, sort=sort, skip=skip, limit=limit
        )


class ExnSeeker(dbing.LMDBer):
    """Maintain fixed search indexes over saved exchange messages in db.exns.

    Preserve legacy string-concatenated keys, distinct from Seeker's typed
    credential keys. Optional message paths are indexed when present.
    """

    # LMDB storage paths, temporary-directory prefix, and named-index capacity.
    TailDirPath = "keri/exndb"
    AltTailDirPath = ".keri/exndb"
    TempPrefix = "keri_exndb_"
    MaxNamedDBs = 36

    # Exchange timestamp for date filtering and legacy string ordering.
    DATE_FIELD = coring.Pather(path=["dt"])
    # Exchange sender AID.
    SENDER_FIELD = coring.Pather(path=["i"])
    # Optional recipient AID in the exchange payload.
    RECIPIENT_FIELD = coring.Pather(path=["a", "i"])
    # Exchange route used to select message families.
    ROUTE_FIELD = coring.Pather(path=["r"])

    # Schema SAID of an ACDC embedded in an IPEX exchange.
    SCHEMA = coring.Pather(path=["e", "acdc", "s"])

    def __init__(self, db, headDirPath=None, perm=None, reopen=False, **kwa):
        """Bind exchange storage and configure a separate LMDB search database.

        Pass reopen=True to open fixed indexes immediately; name/temp and other
        LMDBer kwargs select the storage location and lifetime.
        """
        self.db = db
        self.indexes = dict()

        super(ExnSeeker, self).__init__(
            headDirPath=headDirPath, perm=perm, reopen=reopen, **kwa
        )

    def reopen(self, **kwa):
        """Open fixed single-field and ordered two-field exchange indexes."""
        super(ExnSeeker, self).reopen(**kwa)

        # Reopen the fixed set of exchange search indexes.
        fields = (
            self.ROUTE_FIELD,
            self.SENDER_FIELD,
            self.RECIPIENT_FIELD,
            self.DATE_FIELD,
            self.SCHEMA,
        )
        # Open each field and each ordered pair for compound searches.
        for field in fields:
            self.createIndex(field.qb64)
            for subfield in fields:
                if field == subfield:
                    continue
                subkey = f"{field.qb64}.{subfield.qb64}"
                self.createIndex(subkey)

    @property
    def table(self):
        """Expose saved exchanges as the query candidate table."""
        return self.db.exns

    def value(self, said):
        """Resolve a saved exchange SAID to its event dictionary."""
        serder = self.db.exns.get(keys=(said,))
        return serder.ked

    def saidIter(self):
        """Yield SAID strings from saved exchanges."""
        for (said,), _ in self.db.exns.getItemIter():
            yield said

    def createIndex(self, key):
        """Open a named exchange index mapping legacy keys to duplicate SAIDs."""
        self.indexes[key] = subing.CesrDupSuber(db=self, subkey=key, klas=coring.Saider)

    def index(self, said):
        """Add a saved exchange to fixed indexes, ignoring absent optional paths.

        Concatenate available string values in path order; skip empty keys and
        raise ValueError when the exchange SAID is not saved.
        """
        if (serder := self.db.exns.get(keys=(said,))) is None:
            raise ValueError(f"{said} is not a valid exn")

        saider = coring.Saider(qb64b=serder.saidb)

        # Missing optional paths contribute no value to the legacy key.
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
        """Return a lazy cursor using legacy exchange filter and ordering semantics."""
        return Cursor(seeker=self, filtr=filtr, sort=sort, skip=skip, limit=limit)


class Cursor:
    """Lazily select SAIDs through index lookups, scans, and pagination.

    Filters use CESR path strings (for example -a-LEI), literal equality or
    $eq/$begins objects. Credential equality is typed; exchange keys retain
    legacy semantics. Configure sort/skip/limit before starting iteration.
    """

    def __init__(self, seeker, filtr=None, sort=None, skip=None, limit=None):
        """Bind the seeker and compile filters; defer database reads until iteration.

        Default to no filter, zero skip and a limit of 25. Credential filters
        reject unsupported operators; exchange filters retain legacy parsing.
        """
        self.filtr = filtr if filtr is not None else {}
        self.operators = self.compile(self.filtr)
        self.names = [op.name for op in self.operators]
        self.indexable = next(
            (False for op in self.operators if not isinstance(op, Eq)), True
        )
        self.values = [op.value for op in self.operators]

        self.seeker = seeker
        self._sort = sort
        self._skip = skip if skip is not None else 0
        self._limit = limit if limit is not None else 25

        self.cur = None
        self.saids = None

    def __iter__(self):
        """Return this stateful iterator; iteration does not reset its position."""
        return self

    def __next__(self):
        """Execute the query once, then yield SAIDs until the selected page is exhausted."""
        if self.saids is None:
            self._query()

        if self.cur >= len(self.saids):
            raise StopIteration

        said = self.saids[self.cur]
        self.cur += 1
        return said

    def sort(self, sort):
        """Set ordered CESR sort paths and return self; configure before iteration."""
        self._sort = sort
        return self

    def skip(self, skip):
        """Set the result offset and return self; configure before iteration."""
        self._skip = skip
        return self

    def limit(self, limit):
        """Set the page size and return self; configure before iteration."""
        self._limit = limit
        return self

    def _query(self):
        """Materialize the selected page using direct lookup or fallback scans.

        Validate credential equality values and evaluate prefixes independently
        of the tuple encoding; ordering and slicing occur after selection.
        """
        self.cur = 0
        if len(self.filtr) == 0:
            self.saids = self.order(
                [said for (said,), _ in self.seeker.table.getItemIter()]
            )
        elif (saids := self.indexSearch()) is not None:
            self.saids = self.order(saids)
        elif (saids := self.indexScan()) is not None:
            self.saids = self.order(saids)
        else:
            saids = self.fullTableScan()
            self.saids = self.order(saids)

    def indexSearch(self):
        """Return SAIDs from a matching single/compound index, or None if unavailable."""
        if len(self.operators) == 1 and self.operators[0].name in self.seeker.indexes:
            op = self.operators[0]
            idx = self.seeker.indexes[op.name]
            return self._indexOperator(op, idx)

        index = ".".join(self.names)
        if not (self.indexable and index in self.seeker.indexes):
            return None

        idx = self.seeker.indexes[index]
        val = self.encodeKey(self.values)
        return [val.qb64 for val in idx.getIter(keys=(val,))]

    def indexScan(self):
        """Intersect indexed predicates, then evaluate remaining predicates on candidates."""
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
        saids = oset(self._indexOperator(use[0], idx))
        if len(saids) == 0:
            return list()

        for i, op in enumerate(use[1:]):
            idx = self.seeker.indexes[op.name]
            nxt = oset(self._indexOperator(op, idx))
            saids &= nxt

        if len(scan) == 0:
            return list(saids)
        else:
            return self.tableScan(list(saids), scan)

    @staticmethod
    def compile(filtr):
        """Compile filters using the legacy exchange operator contract."""
        return operators(filtr)

    @staticmethod
    def encodeKey(values):
        """Encode compound exchange keys with their existing concatenation format."""
        return "".join(values)

    def _indexOperator(self, op, idx):
        """Delegate legacy indexed matching to the operator."""
        return op.index(idx)

    def fullTableScan(self):
        """Evaluate filters over candidates from the seeker iterator instead of an index."""
        saids = [saider.qb64 for _, saider in self.seeker.saidIter()]
        return self.tableScan(saids, ops=self.operators)

    def tableScan(self, saids, ops):
        """Retain legacy exchange per-operator accumulation semantics."""
        res = []
        for said in saids:
            val = self.seeker.value(said)
            for op in ops:
                if op(val):
                    res.append(said)
        return res

    def order(self, saids):
        """Order exchanges using an existing index, or preserve candidate order."""
        if not self._sort:
            return self.slice(saids)
        if (res := self.indexOrder(saids)) is not None:
            return res
        return self.tableScanOrder(saids)

    def indexOrder(self, saids):
        """Read a matching legacy sort index, retaining candidates and applying skip/limit."""
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
        """Return the configured page from an already selected/ordered SAID list."""
        if self._skip >= len(saids):
            return []

        end = self._skip + self._limit
        return saids[self._skip : end]

    def tableScanOrder(self, saids):
        """Apply pagination without sorting when no legacy compound sort index exists."""
        return self.slice(saids)


class CredentialCursor(Cursor):
    """Specialize the existing cursor's encoding, matching and ordering boundaries.

    The shared planner never inspects the concrete seeker type. Credential
    semantics stay here; exchange cursors retain their existing behavior.
    """

    @staticmethod
    def compile(filtr):
        """Reject unsupported operators and equality values before database reads."""
        ops = operators(filtr, strict=True)
        for op in ops:
            if isinstance(op, Eq):
                try:
                    tupleKey([op.value])
                except ValueError as ex:
                    raise keriaing.UnsupportedQueryError(str(ex)) from ex
        return ops

    @staticmethod
    def encodeKey(values):
        """Use the same typed tuple codec as credential writes and removals."""
        return tupleKey(values)

    @staticmethod
    def matches(op, sad):
        """Match supported scalars; missing paths and non-scalar actuals do not match."""
        try:
            actual = op.pather.resolve(sad)
            if isinstance(op, Eq):
                return tupleKey([actual]) == tupleKey([op.value])
            return isinstance(actual, str) and actual.startswith(op.value)
        except (KeyError, TypeError, ValueError):
            return False

    def _indexOperator(self, op, idx):
        """Use equality keys directly; evaluate string prefixes on original values."""
        if isinstance(op, Eq):
            return [val.qb64 for val in idx.getIter(keys=(tupleKey([op.value]),))]
        return [
            val.qb64
            for _, val in idx.getItemIter()
            if self.matches(op, self.seeker.value(val.qb64))
        ]

    def tableScan(self, saids, ops):
        """Require every predicate to match each candidate credential."""
        res = []
        for said in saids:
            sad = self.seeker.value(said)
            if all(self.matches(op, sad) for op in ops):
                res.append(said)
        return res

    def order(self, saids):
        """Sort string tuples; omit missing fields and reject non-string sorting.

        Equal tuples use SAID order for stable pagination across query plans.
        Index membership is honored when a matching sort index exists.
        """
        if not self._sort:
            return self.slice(saids)
        paths = [coring.Pather(bext=field) for field in self._sort]
        name = ".".join(path.qb64 for path in paths)
        if name in self.seeker.indexes:
            indexed = {val.qb64 for _, val in self.seeker.indexes[name].getItemIter()}
            saids = [said for said in saids if said in indexed]
        values = {}
        for said in saids:
            sad = self.seeker.value(said)
            try:
                row = tuple(path.resolve(sad) for path in paths)
            except (KeyError, TypeError):
                continue
            if any(type(value) is not str for value in row):
                raise keriaing.UnsupportedQueryError("Numeric sorting is not supported")
            values[said] = row
        return self.slice(sorted(values, key=lambda said: (values[said], said)))


def operators(filtr, strict=False):
    """Compile CESR-path filters into Eq and Begins predicates in input order.

    Literal values mean equality. Strict credential mode rejects unsupported
    operators; non-strict exchange mode ignores unknown operators.
    """
    # filtr = {"-a-i": {"$begins": "984"}}
    ops = []
    for f, v in filtr.items():
        if isinstance(v, dict):
            if strict and not v:
                raise keriaing.UnsupportedQueryError("Empty query operator object")
            for op, val in v.items():
                match op:
                    case "$eq":
                        ops.append(Eq(field=f, value=val))
                    case "$begins":
                        if strict and not isinstance(val, str):
                            raise keriaing.UnsupportedQueryError(
                                "Prefix queries require a string"
                            )
                        ops.append(Begins(field=f, value=val))
                    case _:
                        if strict:
                            raise keriaing.UnsupportedQueryError(
                                f"Unsupported query operator: {op}"
                            )
            pass
        else:
            ops.append(Eq(field=f, value=v))

    return ops


class Eq:
    """Represent path equality; Cursor supplies typed credential semantics.

    Direct calls and index lookups retain legacy Python/string-key behavior.
    """

    def __init__(self, field, value):
        """Bind a CESR path expression and the equality value."""
        self.field = field
        self.pather = coring.Pather(bext=self.field)
        self.value = value

    def __call__(self, *args, **kwargs):
        """Compare the resolved field using Python equality; require one document argument."""
        if len(args) != 1:
            raise ValueError(
                f"invalid argument length={len(args)} for equals operator, must be 2"
            )

        val = self.pather.resolve(args[0])
        return val == self.value

    @property
    def name(self) -> str:
        """Return the qb64 path used to identify a single-field index."""
        return self.pather.qb64

    def index(self, idx):
        """Return SAIDs matching the raw legacy key; credential cursors encode keys separately."""
        return [val.qb64 for val in idx.getIter(keys=(self.value,))]


class Begins:
    """Represent a string-prefix predicate on a CESR document path."""

    def __init__(self, field, value):
        """Bind a CESR path and string prefix; reject non-string prefixes."""
        self.field = field
        self.pather = coring.Pather(bext=self.field)

        if not isinstance(value, str):
            raise ValueError(f"invalid type={type(value)} for begins, must be `str`")
        self.value = value

    def __call__(self, *args, **kwargs):
        """Test the resolved string prefix; require one document with a string field."""
        if len(args) != 1:
            raise ValueError(
                f"invalid argument length={len(args)} for begins operator, must be 2"
            )

        val = self.pather.resolve(args[0])
        if not isinstance(val, str):
            raise ValueError(f"invalid type={type(args[0])} for begins, must be `str`")

        return val.startswith(self.value)

    def index(self, idx):
        """Read a raw legacy key prefix; credential cursors scan resolved string values."""
        return [val.qb64 for _, val in idx.getItemIter(keys=(self.value,))]

    @property
    def name(self) -> str:
        """Return the qb64 path used to identify a single-field index."""
        return self.pather.qb64
