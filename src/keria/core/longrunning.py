# -*- encoding: utf-8 -*-
"""
KERIA
keria.core.longrunning module

"""

import datetime
from collections import namedtuple
from dataclasses import dataclass, asdict, field
from marshmallow import fields
from typing import Literal, Optional, Dict, Union

import falcon
import json
from dataclasses_json import dataclass_json
from keri import kering
from keri.app.oobiing import Result
from keri.core import eventing, coring, serdering
from keri.db import dbing, koming
from keri.help import helping

from keria.app import delegating

# long running operation types
Typeage = namedtuple(
    "Tierage",
    "oobi witness delegation group query registry credential endrole "  # type: ignore[name-match]
    "locscheme challenge exchange submit regsync credsync done",
)

OpTypes = Typeage(
    oobi="oobi",
    witness="witness",
    delegation="delegation",
    group="group",
    query="query",
    registry="registry",
    credential="credential",
    endrole="endrole",
    locscheme="locscheme",
    challenge="challenge",
    exchange="exchange",
    submit="submit",
    regsync="regsync",
    credsync="credsync",
    done="done",
)


def ensure_registry_anchor(hby, reger, gid, regk, regd, anchor):
    """Ensure the local registry VCP has the source-seal couple it needs.

    Late joiners may learn the group KEL event that seals a registry inception
    before any TEL replay path writes the local `reger.ancs` couple for the VCP.
    When that happens, credential-history replay can stall waiting for the
    registry inception anchor even though the sealing group event is already in
    the local KEL. Reuse the known group-event seal to materialize the registry
    anchor couple eagerly.
    """

    if regd is None or anchor is None:
        return False

    dgkey = dbing.dgKey(regk, regd)
    if reger.getAnc(dgkey) is not None:
        return True

    serder = hby.db.fetchLastSealingEventByEventSeal(pre=gid, seal=anchor)
    if serder is None:
        return False

    seqner = coring.Seqner(sn=serder.sn)
    saider = coring.Saider(qb64=serder.said)
    reger.putAnc(dgkey, seqner.qb64b + saider.qb64b)
    return True


def ensure_tel_anchor(hby, reger, gid, pre, said, anchor):
    """Ensure the local TEL event has the source-seal couple it needs.

    Late joiners may have already learned the group KEL event that seals a
    synced credential TEL event while still missing the local `reger.ancs`
    couple for that TEL event. When that happens, replay can stall in
    anchorless escrow even though the sealing group event is already present
    locally.
    """

    if pre is None or said is None or anchor is None:
        return False

    dgkey = dbing.dgKey(pre, said)
    if reger.getAnc(dgkey) is not None:
        return True

    serder = hby.db.fetchLastSealingEventByEventSeal(pre=gid, seal=anchor)
    if serder is None:
        return False

    seqner = coring.Seqner(sn=serder.sn)
    saider = coring.Saider(qb64=serder.said)
    reger.putAnc(dgkey, seqner.qb64b + saider.qb64b)
    return True


def stabilize_credsync_state(registrar=None, credentialer=None):
    """Drive the local escrows needed for imported credential history to settle.

    Late-join credential sync can import the raw CESR material before the local
    TEL, verifier, registrar, and credential dissemination escrows have all had
    a chance to observe the newly available state. Running one explicit
    stabilization pass keeps `/operations/credsync.*` from timing out on state
    that is already locally derivable.
    """

    rgy = registrar.rgy if registrar is not None else None
    if rgy is not None:
        rgy.processEscrows()

    verifier = None
    if credentialer is not None:
        verifier = getattr(credentialer, "verifier", None)
    if verifier is None and registrar is not None:
        verifier = getattr(registrar, "verifier", None)
    if verifier is not None:
        verifier.processEscrows()

    if registrar is not None:
        registrar.processEscrows()

    if credentialer is not None:
        credentialer.processEscrows()


def credsync_statuses(rgy, saids):
    """Summarize per-credential readiness for late-join history replay."""

    statuses = []
    for said in saids:
        status = dict(said=said)

        if rgy.reger.saved.get(keys=(said,)) is None:
            status["state"] = "missing_saved"
            statuses.append(status)
            continue

        try:
            creder, _, _, _ = rgy.reger.cloneCred(said=said)
        except kering.MissingEntryError:
            status["state"] = "missing_clone"
            statuses.append(status)
            continue

        regk = creder.regi if getattr(creder, "regi", None) is not None else creder.sad.get("ri")
        if regk is None:
            status["state"] = "missing_registry_reference"
            statuses.append(status)
            continue

        status["regk"] = regk
        if regk not in rgy.regs or regk not in rgy.tevers:
            status["state"] = "missing_registry_state"
            statuses.append(status)
            continue

        try:
            vcstate = rgy.tevers[regk].vcState(said)
        except Exception as ex:
            status["state"] = "vc_state_error"
            status["error"] = str(ex)
            statuses.append(status)
            continue

        if vcstate is None:
            status["state"] = "missing_vc_state"
            statuses.append(status)
            continue

        status["state"] = "ready"
        status["sn"] = getattr(vcstate, "sn", getattr(vcstate, "s", None))
        status["et"] = getattr(vcstate, "et", getattr(vcstate, "eilk", None))
        statuses.append(status)

    return statuses


@dataclass_json
@dataclass
class OperationStatus:
    code: int
    message: str
    details: Optional[Dict] = field(
        default=None, metadata={"marshmallow_field": fields.Dict(allow_none=True)}
    )


@dataclass_json
@dataclass
class BaseOperation:
    name: str
    metadata: Optional[dict]


@dataclass_json
@dataclass
class PendingOperation(BaseOperation):
    done: Literal[False] = False


@dataclass_json
@dataclass
class CompletedOperation(BaseOperation):
    response: dict
    done: Literal[True] = True


@dataclass_json
@dataclass
class FailedOperation(BaseOperation):
    error: OperationStatus
    done: Literal[True] = True


Operation = Union[PendingOperation, CompletedOperation, FailedOperation]


@dataclass
class Op:
    oid: str
    type: str
    start: str
    metadata: dict


class Operator(dbing.LMDBer):
    TailDirPath = "keri/opr"
    AltTailDirPath = ".keri/opr"
    TempPrefix = "keri_ops_"

    def __init__(self, name="opr", headDirPath=None, reopen=True, **kwa):
        """

        Parameters:
            headDirPath:
            perm:
            reopen:
            kwa:
        """
        self.ops = None
        self.msgs = None

        super(Operator, self).__init__(
            name=name, headDirPath=headDirPath, reopen=reopen, **kwa
        )

    def reopen(self, **kwa):
        """Reopen database and initialize sub-dbs"""
        super(Operator, self).reopen(**kwa)

        # Long running operations, keyed by "name" which is f"{type}.{oid}"
        self.ops = koming.Komer(
            db=self,
            subkey="opr.",
            schema=Op,
        )

        return self.env


class Monitor:
    """Monitoring and garbage collecting long running operations

    Attributes:
        hby (Habery): identifier database environment
        opr(Operator): long running operations database
        swain(Anchorer): Delegation processes tracker

    """

    def __init__(
        self,
        hby,
        swain,
        counselor=None,
        registrar=None,
        exchanger=None,
        credentialer=None,
        submitter=None,
        opr=None,
        temp=False,
    ):
        """Create long running operation monitor

        Parameters:
            hby (Habery): identifier database environment
            swain(Anchorer): Delegation processes tracker
            opr (Operator): long running operations database

        """
        self.hby = hby
        self.swain = swain
        self.counselor = counselor
        self.registrar = registrar
        self.exchanger = exchanger
        self.credentialer = credentialer
        self.submitter = submitter
        self.opr = opr if opr is not None else Operator(name=hby.name, temp=temp)

    def submit(self, oid, typ, metadata=None):
        """Submit a new long running operation to track

        parameters:
            oid (str): opaque identifier of the target of the long running operation (type specific)
            typ (Typeage): long running operation type
            metadata (dict): additional metadata for the long running operation (type specific)

        Returns:
            Operation: the initial long running operation status object

        """
        if typ not in OpTypes:
            raise kering.InvalidValueError(
                f"{typ} not a valid long running operation type"
            )

        name = f"{typ}.{oid}"
        op = Op(oid=oid, type=typ, start=helping.nowIso8601(), metadata=metadata)

        # Overwrite any existing long running operation of this type for this resource.
        # resets the clock basically
        self.opr.ops.pin(keys=(name,), val=op)

        # Return Operation with full status check in case its already finished.
        return self.get(name)

    def update(self, name, metadata):
        """Update metadata for an existing long running operation."""
        if (op := self.opr.ops.get(keys=(name,))) is None:
            raise kering.ValidationError(f"long running operation '{name}' not found")

        updated = Op(oid=op.oid, type=op.type, start=op.start, metadata=metadata)
        self.opr.ops.pin(keys=(name,), val=updated)
        return updated

    def get(self, name):
        if (op := self.opr.ops.get(keys=(name,))) is None:
            return None

        operation = self.status(op)

        return operation

    def getOperations(self, type=None):
        """Return list of long running opterations, optionally filtered by type"""
        ops = self.opr.ops.getItemIter()
        if type is not None:
            ops = filter(lambda i: i[1].type == type, ops)

        def get_status(op):
            try:
                return self.status(op)
            except Exception as err:
                # self.status may throw an exception.
                # Handling error by returning an operation with error status
                return FailedOperation(
                    name=f"{op.type}.{op.oid}",
                    metadata=op.metadata,
                    done=True,
                    error=OperationStatus(code=500, message=f"{err}"),
                )

        return [get_status(op) for (_, op) in ops]

    def rem(self, name):
        """Remove tracking of the long running operation represented by name"""
        return self.opr.ops.rem(keys=(name,))

    def status(self, op):
        """Calculate the status of an operation.

        Base on the type of an operation, determine the current status of the operation, including loading
        any availabie error messages if the operation failed of the sucessful result of the operation which
        will be the same that would be returned by the original endpoint if the operation were not long running

        Parameters:
            op (Op): database storage for long running operation

        Returns:
            Operation: The status of the operation, including any errors or results as appropriate.

        """

        done = False
        response = None
        error = None
        name = f"{op.type}.{op.oid}"
        metadata = op.metadata

        if op.type in (OpTypes.witness,):
            if "pre" not in op.metadata or "sn" not in op.metadata:
                raise kering.ValidationError(
                    f"invalid long running {op.type} operation, metadata missing required fields ('pre', 'sn')"
                )

            pre = op.metadata["pre"]
            if pre not in self.hby.kevers:
                raise kering.ValidationError(
                    f"identifier {pre} not found for long running {op.oid} ({op.type})"
                )

            sn = op.metadata["sn"]
            kever = self.hby.kevers[pre]
            sdig = self.hby.db.getKeLast(
                key=dbing.snKey(pre=kever.prefixer.qb64b, sn=sn)
            )
            if sdig is not None:
                dgkey = dbing.dgKey(kever.prefixer.qb64b, bytes(sdig))
                wigs = self.hby.db.getWigs(dgkey)

                if len(wigs) >= kever.toader.num:
                    evt = self.hby.db.getEvt(
                        dbing.dgKey(pre=kever.prefixer.qb64, dig=bytes(sdig))
                    )
                    serder = serdering.SerderKERI(raw=bytes(evt))
                    done = True
                    response = serder.ked

                else:
                    start = helping.fromIso8601(op.start)
                    dtnow = helping.nowUTC()
                    if (dtnow - start) > datetime.timedelta(
                        seconds=eventing.Kevery.TimeoutPWE
                    ):
                        done = True
                        error = OperationStatus(
                            code=408,  # Using HTTP error codes here for lack of a better alternative
                            message=f"long running {op.type} for {op.oid} (pre: {pre}) operation timed out before "
                            f"receiving sufficient witness receipts",
                        )
                    else:
                        done = False

            else:
                done = False

        elif op.type in (OpTypes.oobi,):
            if "oobi" not in op.metadata:
                raise kering.ValidationError(
                    "invalid OOBI long running operation, missing oobi"
                )

            oobi = op.metadata["oobi"]
            obr = self.hby.db.roobi.get(keys=(oobi,))
            if obr is None:
                done = False
            elif obr.state == Result.resolved:
                done = True
                if obr.cid and obr.cid in self.hby.kevers:
                    kever = self.hby.kevers[obr.cid]
                    response = asdict(kever.state())
                else:
                    response = dict(oobi=oobi)

            elif obr.state == Result.failed:
                done = True
                error = OperationStatus(
                    code=500, message=f"resolving OOBI {op.oid} failed"
                )
            else:
                done = False

        elif op.type in (OpTypes.delegation,):
            if "pre" not in op.metadata:
                raise kering.ValidationError(
                    f"invalid long running {op.type} operation, metadata missing required field 'pre'"
                )

            pre = op.metadata["pre"]
            if pre not in self.hby.kevers:
                raise kering.ValidationError(
                    f"long running {op.type} operation identifier {pre} not found (oid: {op.oid})"
                )

            kever = self.hby.kevers[pre]

            reqsn = "sn"
            reqtee = "teepre"
            anchor = "anchor"
            required = [reqsn, reqtee]
            if reqsn in op.metadata:  # delegatee detects successful delegation
                sn = op.metadata["sn"]
                seqner = coring.Seqner(sn=sn)
                sdig = self.hby.db.getKeLast(key=dbing.snKey(pre=pre, sn=sn))

                if self.swain.complete(kever.prefixer, seqner):
                    evt = self.hby.db.getEvt(
                        dbing.dgKey(pre=kever.prefixer.qb64, dig=bytes(sdig))
                    )
                    serder = serdering.SerderKERI(raw=bytes(evt))

                    done = True
                    response = serder.ked
                else:
                    done = False
            elif (
                reqtee in op.metadata
            ):  # delegator detects delegatee delegation success
                teepre = op.metadata[reqtee]
                anc = op.metadata[anchor]
                if (
                    teepre in self.hby.kevers
                ):  # delegatee dip has been processed by the delegator
                    done = True
                    response = op.metadata[reqtee]
                else:
                    hab = self.hby.habByPre(kever.prefixer.qb64)
                    delegating.approveDelegation(hab, anc)
                    done = False
            else:
                raise falcon.HTTPBadRequest(
                    description=f"longrunning operation type {op.type} requires one of {required}, but are missing from request"
                )

        elif op.type in (OpTypes.group,):
            if "pre" not in op.metadata or "sn" not in op.metadata:
                raise kering.ValidationError(
                    f"invalid long running {op.type} operation, metadata missing required fields ('pre', 'sn')"
                )

            pre = op.metadata["pre"]
            prefixer = coring.Prefixer(qb64=pre)
            seqner = coring.Seqner(sn=op.metadata["sn"])

            if self.counselor.complete(prefixer, seqner):
                sdig = self.hby.db.getKeLast(key=dbing.snKey(pre=pre, sn=seqner.sn))
                evt = self.hby.db.getEvt(
                    dbing.dgKey(pre=prefixer.qb64, dig=bytes(sdig))
                )
                serder = serdering.SerderKERI(raw=bytes(evt))

                done = True
                response = serder.ked
            else:
                done = False

        elif op.type in (OpTypes.query,):
            if "pre" not in op.metadata:
                raise kering.ValidationError(
                    f"invalid long running {op.type} operation, metadata missing required field 'pre'"
                )

            pre = op.metadata["pre"]
            if pre not in self.hby.kevers:
                done = False

            else:
                kever = self.hby.kevers[pre]
                if "sn" in op.metadata:
                    sn = int(op.metadata["sn"], 16)
                    if kever.sn >= sn:
                        done = True
                        response = asdict(kever.state())
                    else:
                        done = False
                elif "anchor" in op.metadata:
                    anchor = op.metadata["anchor"]
                    if self.hby.db.findAnchoringSealEvent(pre, seal=anchor) is not None:
                        done = True
                        response = asdict(kever.state())
                    else:
                        done = False
                else:
                    ksn = None
                    for _, saider in self.hby.db.knas.getItemIter(keys=(pre,)):
                        ksn = self.hby.db.ksns.get(keys=(saider.qb64,))
                        break

                    if ksn and ksn.d == kever.serder.said:
                        done = True
                        response = asdict(kever.state())
                    else:
                        done = False

        elif op.type in (OpTypes.registry,):
            if "pre" not in op.metadata or "anchor" not in op.metadata:
                raise kering.ValidationError(
                    f"invalid long running {op.type} operation, metadata missing required fields ('pre', 'anchor')"
                )

            pre = op.metadata["pre"]
            if pre not in self.hby.kevers:
                raise kering.ValidationError(
                    f"identifier {pre} for long running {op.type} operation {op.oid} not found"
                )

            anchor = op.metadata["anchor"]
            if self.hby.db.findAnchoringSealEvent(pre, seal=anchor) is not None:
                done = True
                response = dict(anchor=anchor)
            else:
                done = False

        elif op.type in (OpTypes.credential,):
            if "ced" not in op.metadata:
                raise kering.ValidationError(
                    f"invalid long running {op.type} operation, metadata missing 'ced' field"
                )

            ced = op.metadata["ced"]
            if self.credentialer.complete(ced["d"]):
                done = True
                response = dict(ced=ced)
            else:
                done = False

        elif op.type in (OpTypes.exchange,):
            if self.exchanger.complete(op.oid):
                done = True
                response = dict(said=op.oid)
            else:
                done = False

        elif op.type in (OpTypes.endrole,):
            if (
                "cid" not in op.metadata
                or "role" not in op.metadata
                or "eid" not in op.metadata
            ):
                raise kering.ValidationError(
                    f"invalid long running {op.type} operation, metadata missing required fields ('cid', 'role', 'eid')"
                )

            cid = op.metadata["cid"]
            role = op.metadata["role"]
            eid = op.metadata["eid"]

            end = self.hby.db.ends.get(keys=(cid, role, eid))
            if end and (end.enabled or end.allowed):
                saider = self.hby.db.eans.get(keys=(cid, role, eid))
                serder = self.hby.db.rpys.get(keys=(saider.qb64,))
                done = True
                response = serder.ked
            else:
                done = False

        elif op.type in (OpTypes.locscheme,):
            if (
                "eid" not in op.metadata
                or "scheme" not in op.metadata
                or "url" not in op.metadata
            ):
                raise kering.ValidationError(
                    f"invalid long running {op.type} operation, metadata missing required fields ('eid', 'scheme', 'url')"
                )

            eid = op.metadata["eid"]
            scheme = op.metadata["scheme"]
            url = op.metadata["url"]

            loc = self.hby.db.locs.get(keys=(eid, scheme))
            if loc:
                done = True
                response = dict(eid=eid, scheme=scheme, url=url)
            else:
                done = False

        elif op.type in (OpTypes.challenge,):
            if op.oid not in self.hby.kevers:
                done = False

            if "words" not in op.metadata:
                raise kering.ValidationError(
                    f"invalid long running {op.type} operation, metadata missing 'words' field"
                )

            found = False
            words = op.metadata["words"]
            saiders = self.hby.db.reps.get(keys=(op.oid,))
            for saider in saiders:
                exn = self.hby.db.exns.get(keys=(saider.qb64,))
                if words == exn.ked["a"]["words"]:
                    found = True
                    break

            if found:
                done = True
                response = dict(exn=exn.ked)
            else:
                done = False

        elif op.type in (OpTypes.submit,):
            kever = self.hby.kevers[op.oid]
            if (
                kever
                and len(self.submitter.submits) == 0
                and len(self.submitter.doers) == 0
            ):
                done = True
                response = asdict(kever.state())
            else:
                start = helping.fromIso8601(op.start)
                dtnow = helping.nowUTC()
                if (dtnow - start) > datetime.timedelta(
                    seconds=eventing.Kevery.TimeoutPWE
                ):
                    done = True
                    error = OperationStatus(
                        code=408,  # Using HTTP error codes here for lack of a better alternative
                        message=f"long running {op.type} for {op.oid} operation timed out before "
                        f"receiving sufficient witness receipts",
                    )
                else:
                    done = False

        elif op.type in (OpTypes.regsync,):
            required = ("pre", "source", "phase", "phase_start", "request", "targets")
            missing = [field for field in required if field not in op.metadata]
            if missing:
                raise kering.ValidationError(
                    f"invalid long running {op.type} operation, metadata missing required fields {tuple(missing)}"
                )

            if "error" in op.metadata and op.metadata["error"] is not None:
                err = op.metadata["error"]
                done = True
                error = OperationStatus(
                    code=err["code"],
                    message=err["message"],
                    details=err.get("details"),
                )
            else:
                phase = op.metadata["phase"]
                phase_start = helping.fromIso8601(op.metadata["phase_start"])
                dtnow = helping.nowUTC()

                if phase == "catalog":
                    if (dtnow - phase_start) > datetime.timedelta(seconds=10):
                        done = True
                        error = OperationStatus(
                            code=504,
                            message=(
                                f"long running {op.type} for {op.oid} timed out waiting "
                                f"for registry catalog response from {op.metadata['source']}"
                            ),
                            details=dict(phase=phase, source=op.metadata["source"]),
                        )
                    else:
                        done = False

                elif phase == "replay":
                    rgy = self.registrar.rgy if self.registrar is not None else None
                    if rgy is None:
                        raise kering.ValidationError(
                            f"invalid long running {op.type} operation, registrar not configured"
                        )

                    pending = False
                    for target in op.metadata["targets"]:
                        regk = target["regk"]
                        regd = target.get("regd")
                        target_sn = int(target["sn"])
                        if regk not in rgy.regs or regk not in rgy.tevers:
                            pending = True
                            break

                        if rgy.tevers[regk].sn < target_sn:
                            pending = True
                            break

                        anchor = target.get("anc")
                        if anchor is not None and regd is not None:
                            if not ensure_registry_anchor(
                                hby=self.hby,
                                reger=rgy.reger,
                                gid=op.metadata["pre"],
                                regk=regk,
                                regd=regd,
                                anchor=anchor,
                            ):
                                pending = True
                                break

                        if regd is not None and rgy.reger.getAnc(dbing.dgKey(regk, regd)) is None:
                            pending = True
                            break

                    if pending:
                        if (dtnow - phase_start) > datetime.timedelta(seconds=30):
                            done = True
                            error = OperationStatus(
                                code=504,
                                message=(
                                    f"long running {op.type} for {op.oid} timed out waiting "
                                    f"for registry TEL replay"
                                ),
                                details=dict(
                                    phase=phase,
                                    source=op.metadata["source"],
                                    targets=op.metadata["targets"],
                                ),
                            )
                        else:
                            done = False
                    else:
                        done = True
                        response = dict(
                            pre=op.metadata["pre"],
                            source=op.metadata["source"],
                            synced=[
                                dict(
                                    name=target["name"],
                                    regk=target["regk"],
                                    sn=target["sn"],
                                )
                                for target in op.metadata["targets"]
                            ],
                        )
                else:
                    raise kering.ValidationError(
                        f"invalid long running {op.type} operation, unknown phase '{phase}'"
                    )

        elif op.type in (OpTypes.credsync,):
            required = (
                "pre",
                "source",
                "phase",
                "phase_start",
                "request",
                "saids",
                "synced",
            )
            missing = [field for field in required if field not in op.metadata]
            if missing:
                raise kering.ValidationError(
                    f"invalid long running {op.type} operation, metadata missing required fields {tuple(missing)}"
                )

            if "error" in op.metadata and op.metadata["error"] is not None:
                err = op.metadata["error"]
                done = True
                error = OperationStatus(
                    code=err["code"],
                    message=err["message"],
                    details=err.get("details"),
                )
            else:
                phase = op.metadata["phase"]
                if phase != "replay":
                    raise kering.ValidationError(
                        f"invalid long running {op.type} operation, unknown phase '{phase}'"
                    )

                if self.registrar is None:
                    raise kering.ValidationError(
                        f"invalid long running {op.type} operation, registrar not configured"
                    )

                phase_start = helping.fromIso8601(op.metadata["phase_start"])
                dtnow = helping.nowUTC()
                rgy = self.registrar.rgy
                stabilize_credsync_state(
                    registrar=self.registrar,
                    credentialer=self.credentialer,
                )
                statuses = credsync_statuses(rgy=rgy, saids=op.metadata["saids"])
                pending = any(status["state"] != "ready" for status in statuses)

                if pending:
                    if (dtnow - phase_start) > datetime.timedelta(seconds=30):
                        done = True
                        error = OperationStatus(
                            code=504,
                            message=(
                                f"long running {op.type} for {op.oid} timed out waiting "
                                f"for credential history replay"
                            ),
                            details=dict(
                                phase=phase,
                                source=op.metadata["source"],
                                saids=op.metadata["saids"],
                                synced=op.metadata["synced"],
                                statuses=statuses,
                            ),
                        )
                    else:
                        done = False
                else:
                    done = True
                    response = dict(
                        pre=op.metadata["pre"],
                        source=op.metadata["source"],
                        synced=op.metadata["saids"],
                    )

        elif op.type in (OpTypes.done,):
            done = True
            response = op.metadata["response"]

        else:
            done = True
            error = OperationStatus(
                code=404,  # Using HTTP error codes here for lack of a better alternative
                message=f"long running operation type {op.type} unknown",
            )

        if error is not None:
            return FailedOperation(
                name=name,
                metadata=metadata,
                error=error,
            )
        elif done:
            return CompletedOperation(
                name=name,
                metadata=metadata,
                response=response,
            )
        else:
            return PendingOperation(
                name=name,
                metadata=metadata,
            )


class OperationCollectionEnd:
    @staticmethod
    def on_get(req, rep):
        """Get list of long running operations

        Parameters:
            req (Request):  Falcon HTTP Request object
            rep (Response): Falcon HTTP Response object

        ---
        summary: Get list of long running operations
        parameters:
          - in: query
            name: type
            schema:
              type: string
            required: false
            description: filter list of long running operations by type
        responses:
            200:
              description: list of long running operations
              content:
                  application/json:
                    schema:
                        type: array
                        items:
                          $ref: '#/components/schemas/Operation'
        """
        agent = req.context.agent
        type = req.params.get("type")
        ops = agent.monitor.getOperations(type=type)
        rep.data = json.dumps(ops, default=lambda o: o.to_dict()).encode("utf-8")
        rep.content_type = "application/json"
        rep.status = falcon.HTTP_200


class OperationResourceEnd:
    """Single Resource REST endpoint for long running operations"""

    @staticmethod
    def on_get(req, rep, name):
        """GET single resource REST endpoint

        Parameters:
            req (Request):  Falcon HTTP Request object
            rep (Response): Falcon HTTP Response object
            name (str): Long running operation resource name to load
        ---
        summary: Retrieve a specific long running operation.
        description: This endpoint retrieves the status of a long running operation by its name.
        tags:
        - Operation
        parameters:
          - in: path
            name: name
            schema:
              type: string
            required: true
            description: The name of the long running operation to retrieve.
        responses:
          200:
            description: Successfully retrieved the status of the long running operation.
            content:
                application/json:
                    schema:
                        $ref: '#/components/schemas/Operation'
          404:
            description: The requested long running operation was not found.

        """
        agent = req.context.agent
        if (operation := agent.monitor.get(name)) is None:
            raise falcon.HTTPNotFound(
                title=f"long running operation '{name}' not found"
            )

        rep.content_type = "application/json"
        rep.data = operation.to_json().encode("utf-8")
        rep.status = falcon.HTTP_200

    @staticmethod
    def on_delete(req, rep, name):
        """DELETE single resource REST endpoint

        Args:
            req (Request):  Falcon HTTP Request object
            rep (Response): Falcon HTTP Response object
            name (str): Long running operation resource name to load
        ---
        summary: Remove a specific long running operation.
        description: This endpoint removes a long running operation by its name.
        tags:
        - Operation
        parameters:
          - in: path
            name: name
            schema:
              type: string
            required: true
            description: The name of the long running operation to remove.
        responses:
          204:
              description: Successfully removed the long running operation.
          404:
              description: The requested long running operation was not found.
          500:
              description: Internal server error. This could be due to an issue with removing the operation.
        """

        agent = req.context.agent
        if agent.monitor.get(name) is None:
            raise falcon.HTTPNotFound(
                title=f"long running operation '{name}' not found"
            )

        deleted = agent.monitor.rem(name)
        if deleted:
            rep.status = falcon.HTTP_204
        else:
            raise falcon.HTTPInternalServerError(
                f"unable to delete long running operation {name}"
            )
