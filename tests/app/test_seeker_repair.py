"""Real LMDB regressions for credential indexing and startup recovery."""

import math

import pytest
from hio.help import decking
from keri.app import habbing
from keri.core import coring, scheming
from keri.vc import proving
from keri.vdr import viring

from keria.app import agenting
from keria import keriaing
from keria.db import basing


@pytest.fixture
def stores(tmp_path):
    with habbing.openHab(name="seeker-repair", temp=True) as (hby, hab):
        reger = viring.Reger(name="repair", temp=True)
        seeker = basing.Seeker(
            name="repair",
            headDirPath=str(tmp_path),
            temp=False,
            reopen=True,
            db=hby.db,
            reger=reger,
        )
        try:
            yield hby, hab, reger, seeker
        finally:
            seeker.close(clear=True)
            reger.close(clear=True)


def schema(hby, issuee=False, x_type="number", extra=None, optional=(), oneof=False):
    properties = {
        "d": {"type": "string"},
        "x": {"type": x_type},
        "y": {"type": "string"},
    }
    properties.update(extra or {})
    if issuee:
        properties["i"] = {"type": "string"}
    payload = {
        "type": "object",
        "properties": properties,
        "required": [name for name in properties if name not in optional],
    }
    if oneof:
        payload = {"oneOf": [{"type": "string"}, payload]}
    schemer = scheming.Schemer(
        sed={
            "$id": "",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {"a": payload},
        }
    )
    hby.db.schema.pin(keys=(schemer.said,), val=schemer)
    return schemer


def save(hab, reger, schemer, x, y="c", **attributes):
    creder = proving.credential(
        issuer=hab.pre,
        schema=schemer.said,
        status=hab.pre,
        data={"x": x, "y": y, **attributes},
    )
    saider = coring.Saider(qb64=creder.said)
    reger.creds.pin(keys=(creder.said,), val=creder)
    reger.saved.pin(keys=(creder.said,), val=saider)
    reger.schms.add(keys=(schemer.said,), val=saider)
    return creder


def finish(doer):
    for _ in range(10000):
        doer.recur()
        if doer.repair is None:
            return
    pytest.fail("startup reconciliation did not finish")


def test_typed_equality_and_reopen(stores):
    hby, hab, reger, seeker = stores
    sch = schema(hby)
    schemas = {
        int: schema(hby, x_type="integer"),
        float: sch,
        str: schema(hby, x_type="string"),
    }
    creds = [
        save(hab, reger, schemas[type(value)], value)
        for value in (-12, 1, 1.0, "1", -0.0, 2.75)
    ]
    for creder in creds:
        assert hby.db.schema.get(keys=(creder.schema,)).verify(raw=creder.raw)
    for creder in creds:
        seeker.index(creder.said)
    for creder in creds:
        assert list(seeker.find({"-a-x": creder.sad["a"]["x"]})) == [creder.said]
    assert list(seeker.find({"-a-x": 0.0})) == [creds[4].said]
    assert list(seeker.find({"-a-x": {"$begins": "1"}})) == [creds[3].said]
    assert list(seeker.find({"-a-x": 1, "-a-y": "c"})) == [creds[1].said]
    seeker.close(clear=False)
    seeker.reopen()
    assert list(seeker.find({"-a-x": 1.0})) == [creds[2].said]
    seeker.unindex(creds[1].said)
    assert list(seeker.find({"-a-x": 1})) == []
    with pytest.raises(keriaing.UnsupportedQueryError, match="Numeric sorting"):
        list(seeker.find({}, sort=["-a-x"]))
    with pytest.raises(keriaing.UnsupportedQueryError):
        list(seeker.find({"-a-x": {"$gt": 1}}))


@pytest.mark.parametrize("value", [True, math.inf, -math.inf, math.nan, [], {}, None])
def test_reject_scalars_before_writes(stores, value):
    hby, hab, reger, seeker = stores
    sch = schema(hby)
    creder = save(hab, reger, sch, value)
    with pytest.raises(ValueError):
        seeker.index(creder.said)
    assert all(not list(db.getItemIter()) for db in seeker.indexes.values())


def test_boundaries_strings_and_issueeless(stores):
    hby, hab, reger, seeker = stores
    sch = schema(hby, x_type="string")
    one = save(hab, reger, sch, "ab", "c")
    two = save(hab, reger, sch, "a", "bc")
    for creder in (one, two):
        seeker.index(creder.said)
    assert list(seeker.find({"-a-x": "ab", "-a-y": "c"})) == [one.said]
    assert basing.tupleKey(["ab", "c"]) != basing.tupleKey(["a", "bc"])
    seeker.unindex(one.said)
    assert list(seeker.find({"-a-x": "ab", "-a-y": "c"})) == []
    assert list(seeker.find({"-a-x": {"$begins": "ab"}})) == []
    assert list(seeker.find({"-a-x": "a", "-a-y": "bc"})) == [two.said]
    seeker.index(one.said)
    assert set(seeker.find({"-a-x": {"$begins": "a"}})) == {one.said, two.said}
    assert list(seeker.find({}, sort=["-a-x"])) == [two.said, one.said]
    definitions = seeker.schIdx.get(keys=(sch.said,))
    assert all(
        basing.ISSUEE_FIELD.qb64 not in seeker.dynIdx.get(keys=(idx,)).paths
        for idx in definitions
    )


def test_reconcile_partial_poison_and_repeat(stores):
    hby, hab, reger, seeker = stores
    sch = schema(hby)
    creder = save(hab, reger, sch, -3)
    seeker.generateIndexes(sch.said)
    poison = f"{basing.ISSUEE_FIELD.qb64}.{coring.Pather(path=['a', 'x']).qb64}"
    seeker.createIndex(poison)
    seeker.dynIdx.pin(
        keys=(poison,),
        val=basing.IndexRecord(
            subkey=poison,
            paths=[basing.ISSUEE_FIELD.qb64, coring.Pather(path=["a", "x"]).qb64],
        ),
    )
    seeker.schIdx.add(keys=(sch.said,), val=poison)
    saider = coring.Saider(qb64=creder.said)
    seeker.indexes[poison].add(keys=("legacy-poison",), val=saider)
    seeker.indexes[basing.ISSUER_FIELD.qb64].add(keys=(hab.pre,), val=saider)
    doer = agenting.SeekerDoer(seeker, decking.Deck())
    with pytest.raises(keriaing.IndexNotReadyError):
        seeker.find({})
    finish(doer)
    assert not seeker.failures
    assert seeker.dynIdx.get(keys=(poison,)) is None
    assert seeker.env.open_db(poison.encode(), create=False) is not None
    assert list(seeker.find({"-a-x": -3})) == [creder.said]
    assert list(seeker.indexes[basing.ISSUER_FIELD.qb64].getIter(keys=(hab.pre,))) == []
    before = {name: list(db.getItemIter()) for name, db in seeker.indexes.items()}
    list(seeker.reconcile())
    after = {name: list(db.getItemIter()) for name, db in seeker.indexes.items()}
    assert {
        key: [(keys, val.qb64) for keys, val in rows] for key, rows in before.items()
    } == {key: [(keys, val.qb64) for keys, val in rows] for key, rows in after.items()}
    seeker.close(clear=False)
    seeker.reopen()
    finish(agenting.SeekerDoer(seeker, decking.Deck()))
    assert list(seeker.find({"-a-x": -3})) == [creder.said]


def test_missing_schema_and_permanent_failure(stores):
    hby, hab, reger, seeker = stores
    sch = schema(hby)
    good = save(hab, reger, sch, -3)
    bad = save(hab, reger, sch, True)
    hby.db.schema.rem(keys=(sch.said,))
    cues = decking.Deck([dict(kin="saved", creder=good), dict(kin="saved", creder=bad)])
    doer = agenting.SeekerDoer(seeker, cues)
    finish(doer)
    for _ in range(5):
        doer.recur()
    assert not cues
    assert set(seeker.pending) == {good.said, bad.said}
    hby.db.schema.pin(keys=(sch.said,), val=sch)
    for _ in range(5):
        doer.recur()
    assert not seeker.pending
    assert good.said not in seeker.failures
    assert isinstance(seeker.failures[bad.said], ValueError)
    failure = seeker.failures[bad.said]
    for _ in range(5):
        doer.recur()
    assert seeker.failures[bad.said] is failure
    assert not cues
    with pytest.raises(keriaing.IndexNotReadyError):
        seeker.find({})
    assert reger.saved.get(keys=(bad.said,)) is not None


def test_unexpected_failure_does_not_cycle(stores, monkeypatch):
    hby, hab, reger, seeker = stores
    sch = schema(hby)
    creder = save(hab, reger, sch, 1)
    cues = decking.Deck()
    doer = agenting.SeekerDoer(seeker, cues)
    finish(doer)
    calls = []

    def fail_write(**kwargs):
        calls.append(kwargs)
        raise OSError("injected write failure")

    monkeypatch.setattr(seeker.indexes[basing.ISSUER_FIELD.qb64], "add", fail_write)
    cues.append(dict(kin="saved", creder=creder))
    doer.recur()
    failure = seeker.failures[creder.said]
    assert isinstance(failure, OSError)
    for _ in range(5):
        doer.recur()
    assert len(calls) == 1
    assert not cues and not seeker.pending
    assert seeker.failures[creder.said] is failure
    seeker.unindex(creder.said)
    assert not seeker.failures
    assert all(not list(db.getItemIter()) for db in seeker.indexes.values())


def test_query_errors_are_explicit(stores):
    from types import SimpleNamespace
    import falcon
    from falcon import testing
    from keria.app import credentialing

    hby, hab, reger, seeker = stores
    sch = schema(hby)
    creder = save(hab, reger, sch, 1)
    seeker.index(creder.said)

    class Context:
        def process_request(self, req, resp):
            req.context.agent = SimpleNamespace(
                seeker=seeker, hby=hby, rgy=SimpleNamespace(reger=reger)
            )

    app = falcon.App(middleware=[Context()])
    app.add_route("/credentials/query", credentialing.CredentialQueryCollectionEnd())
    client = testing.TestClient(app)
    result = client.simulate_post(
        "/credentials/query", json={"filter": {"-a": {"$eq": "irrelevant"}}}
    )
    assert result.status_code == 200 and result.json == []
    result = client.simulate_post(
        "/credentials/query", json={"sort": ["-a-absent", "-a-y"]}
    )
    assert result.status_code == 200 and result.json == []
    result = client.simulate_post("/credentials/query", json={"sort": ["-a-x"]})
    assert result.status_code == 400
    assert result.json["title"] == "Unsupported credential query"
    result = client.simulate_post(
        "/credentials/query", json={"filter": {"-a-x": {"$gt": 0}}}
    )
    assert result.status_code == 400
    result = client.simulate_post("/credentials/query", json={"filter": {"-a-x": {}}})
    assert result.status_code == 400
    doer = agenting.SeekerDoer(seeker, decking.Deck())
    result = client.simulate_post("/credentials/query", json={})
    assert result.status_code == 503
    assert result.json["title"] == "Credential indexes unavailable"
    finish(doer)
    seeker.failRepair(RuntimeError("injected startup failure"))
    result = client.simulate_post("/credentials/query", json={})
    assert result.status_code == 503
    assert "startup (RuntimeError)" in result.json["description"]


@pytest.mark.parametrize("length", [153, 423, 511, 1024])
def test_long_valid_strings_and_deletion(stores, length):
    hby, hab, reger, seeker = stores
    sch = schema(hby, issuee=True, x_type="string")
    creder = save(hab, reger, sch, "x" * length, i=hab.pre)
    assert sch.verify(raw=creder.raw)
    assert seeker.process(creder.said) is None
    assert list(seeker.find({"-i": hab.pre, "-s": sch.said, "-a-x": "x" * length})) == [
        creder.said
    ]
    seeker.close(clear=False)
    seeker.reopen()
    assert list(seeker.find({"-a-x": "x" * length})) == [creder.said]
    # Deletion must not require a usable schema.
    hby.db.schema.rem(keys=(sch.said,))
    seeker.unindex(creder.said)
    assert all(not list(db.getItemIter()) for db in seeker.indexes.values())


def test_canonical_compound_definitions(stores):
    hby, hab, reger, seeker = stores
    sch = schema(hby, issuee=True, x_type="string")
    one = save(hab, reger, sch, "c", i="ab")
    two = save(hab, reger, sch, "bc", i="a")
    for creder in (one, two):
        assert sch.verify(raw=creder.raw)
        seeker.index(creder.said)
    assert list(seeker.find({"-a-i": "ab", "-a-x": "c"})) == [one.said]
    assert list(seeker.find({"-a-i": "a", "-a-x": "bc"})) == [two.said]
    for filtr in ({"-i": hab.pre, "-s": sch.said}, {"-s": sch.said, "-i": hab.pre}):
        assert set(seeker.find(filtr)) == {one.said, two.said}
    assert list(seeker.find({"-a-i": "ab", "-s": sch.said})) == [one.said]
    # Repair retained metadata as well as obsolete metadata.
    name = f"{basing.ISSUER_FIELD.qb64}.{basing.SCHEMA_FIELD.qb64}"
    seeker.dynIdx.pin(keys=(name,), val=basing.IndexRecord(subkey=name, paths=[name]))
    list(seeker.reconcile())
    assert seeker.dynIdx.get(keys=(name,)).paths == name.split(".")
    assert set(seeker.find({"-i": hab.pre, "-s": sch.said})) == {one.said, two.said}
    seeker.unindex(one.said)
    assert list(seeker.find({"-a-i": "ab", "-a-x": "c"})) == []


def test_partial_definitions_cannot_become_success(stores):
    hby, hab, reger, seeker = stores
    good = schema(hby)
    seeker.index(save(hab, reger, good, 1).said)
    bad = schema(
        hby,
        extra={"z": {"anyOf": [{"type": "string"}, {"type": "number"}]}},
        optional=("z",),
    )
    creder = save(hab, reger, bad, 2, y="needle")
    assert bad.verify(raw=creder.raw)
    # Simulate interrupted legacy publication; a truthy list cannot bypass validation.
    seeker.schIdx.add(keys=(bad.said,), val=basing.ISSUER_FIELD.qb64)
    cues = decking.Deck([dict(kin="saved", creder=creder)] * 2)
    doer = agenting.SeekerDoer(seeker, cues)
    finish(doer)
    for _ in range(3):
        doer.recur()
    assert isinstance(seeker.failures[creder.said], ValueError)
    assert not cues and not seeker.pending
    with pytest.raises(keriaing.IndexNotReadyError):
        seeker.find({"-a-y": "needle"})
    seeker.unindex(creder.said)
    assert not seeker.failures


def test_optional_attributes_and_scalar_fallback(stores):
    """Exercise the ECR-shaped oneOf attribute object with optional a.u."""
    hby, hab, reger, seeker = stores
    sch = schema(
        hby,
        extra={"u": {"type": "string"}, "flag": {"type": "boolean"}},
        optional=("u",),
        issuee=True,
        oneof=True,
    )
    absent = save(hab, reger, sch, 1, flag=True, i=hab.pre)
    present = save(hab, reger, sch, 2, flag=False, u="salt", i=hab.pre)
    for creder in (absent, present):
        assert sch.verify(raw=creder.raw)
        seeker.index(creder.said)
    assert set(seeker.find({"-s": sch.said})) == {absent.said, present.said}
    assert list(seeker.find({"-a": {"$eq": "irrelevant"}})) == []
    assert list(seeker.find({"-a-flag": 1})) == []
    assert list(seeker.find({}, sort=["-a-u"])) == [present.said]
    assert list(seeker.find({}, sort=["-a-u", "-a-y"])) == [present.said]


def test_delete_during_repair_and_stale_cue(stores):
    hby, hab, reger, seeker = stores
    sch = schema(hby)
    creder = save(hab, reger, sch, 1)
    seeker.index(creder.said)
    repair = seeker.startRepair()
    next(repair)  # accepted SAID has been discovered
    seeker.unindex(creder.said)
    reger.schms.rem(keys=(sch.said,), val=coring.Saider(qb64=creder.said))
    reger.saved.rem(keys=(creder.said,))
    reger.creds.rem(keys=(creder.said,))
    list(repair)
    assert seeker.process(creder.said) is None
    assert not seeker.failures and not seeker.pending
    assert list(seeker.find({})) == []


@pytest.mark.parametrize("steps", [1, 2, 8, 18])
def test_interrupted_repair_restarts(stores, steps):
    hby, hab, reger, seeker = stores
    sch = schema(hby)
    creder = save(hab, reger, sch, 1)
    seeker.index(creder.said)
    repair = seeker.startRepair()
    for _ in range(steps):
        next(repair)
    repair.close()
    with pytest.raises(keriaing.IndexNotReadyError):
        seeker.find({})
    seeker.close(clear=False)
    seeker.reopen()
    doer = agenting.SeekerDoer(seeker, decking.Deck())
    with pytest.raises(keriaing.IndexNotReadyError):
        seeker.find({})
    finish(doer)
    assert not seeker.failures
    assert list(seeker.find({"-a-x": 1})) == [creder.said]


def test_repair_batches_scheduler_work(stores):
    hby, hab, reger, seeker = stores
    sch = schema(hby)
    for value in range(10):
        seeker.index(save(hab, reger, sch, value).said)
    doer = agenting.SeekerDoer(seeker, decking.Deck())
    doer.recur()
    assert doer.repair is not None  # bounded, not an unbounded drain
    doer.recur()
    assert doer.repair is None  # 182 small steps fit in two 128-step turns
    assert len(list(seeker.find({}))) == 10


def test_healthy_unindex_uses_direct_keys(stores, monkeypatch):
    hby, hab, reger, seeker = stores
    creder = save(hab, reger, schema(hby), 1)
    seeker.index(creder.said)

    def unexpected_scan(*args, **kwargs):
        pytest.fail("healthy deletion must not scan every credential index")

    with monkeypatch.context() as patch:
        for db in seeker.indexes.values():
            patch.setattr(db, "getItemIter", unexpected_scan)
        seeker.unindex(creder.said)
    assert all(not list(db.getItemIter()) for db in seeker.indexes.values())


def test_pending_credential_disappears(stores):
    hby, hab, reger, seeker = stores
    sch = schema(hby)
    creder = save(hab, reger, sch, 1)
    hby.db.schema.rem(keys=(sch.said,))
    assert isinstance(seeker.process(creder.said), keriaing.MissingSchemaError)
    reger.creds.rem(keys=(creder.said,))
    said, error = seeker.retry()
    assert said == creder.said and isinstance(error, ValueError)
    assert not isinstance(error, keriaing.MissingSchemaError)
    assert not seeker.pending
    assert seeker.failures[said] is error


def test_partial_deletion_remains_observable(stores, monkeypatch):
    hby, hab, reger, seeker = stores
    creder = save(hab, reger, schema(hby), 1)
    seeker.index(creder.said)

    def fail_remove(**kwargs):
        raise OSError("injected deletion failure")

    with monkeypatch.context() as patch:
        patch.setattr(seeker.indexes[basing.ISSUER_FIELD.qb64], "rem", fail_remove)
        with pytest.raises(OSError):
            seeker.unindex(creder.said)
    with pytest.raises(keriaing.IndexNotReadyError):
        seeker.find({})
    seeker.unindex(creder.said)
    assert not seeker.failures
    assert all(not list(db.getItemIter()) for db in seeker.indexes.values())
