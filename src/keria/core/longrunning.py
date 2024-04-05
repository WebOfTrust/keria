# -*- encoding: utf-8 -*-
"""
KERIA
keria.core.longrunning module

"""
import datetime
from collections import namedtuple
from dataclasses import dataclass, asdict

import falcon
import json
from dataclasses_json import dataclass_json
from keri import kering
from keri.app.oobiing import Result
from keri.core import eventing, coring, serdering
from keri.db import dbing, koming
from keri.help import helping

# long running operationt types
Typeage = namedtuple("Tierage", 'oobi witness delegation group query registry credential endrole challenge exchange '
                                'done')

OpTypes = Typeage(oobi="oobi", witness='witness', delegation='delegation', group='group', query='query',
                  registry='registry', credential='credential', endrole='endrole', challenge='challenge',
                  exchange='exchange', done='done')


@dataclass_json
@dataclass
class Status:
    code: int
    message: str
    details: dict = None


@dataclass_json
@dataclass
class Operation:
    name: str
    metadata: dict
    done: bool = False
    error: Status = None
    response: dict = None


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

        super(Operator, self).__init__(name=name, headDirPath=headDirPath, reopen=reopen, **kwa)

    def reopen(self, **kwa):
        """  Reopen database and initialize sub-dbs
        """
        super(Operator, self).reopen(**kwa)

        # Long running operations, keyed by "name" which is f"{type}.{oid}"
        self.ops = koming.Komer(db=self, subkey='opr.', schema=Op, )

        return self.env


class Monitor:
    """  Monitoring and garbage collecting long running operations

    Attributes:
        hby (Habery): identifier database environment
        opr(Operator): long running operations database
        swain(Anchorer): Delegation processes tracker

    """

    def __init__(self, hby, swain, counselor=None, registrar=None, exchanger=None, credentialer=None, opr=None,
                 temp=False):
        """ Create long running operation monitor

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
        self.opr = opr if opr is not None else Operator(name=hby.name, temp=temp)

    def submit(self, oid, typ, metadata=None):
        """  Submit a new long running operation to track

        parameters:
            oid (str): opaque identifier of the target of the long running operation (type specific)
            typ (Typeage): long running operation type
            metadata (dict): additional metadata for the long running operation (type specific)

        Returns:
            Operation: the initial long running operation status object

        """
        if typ not in OpTypes:
            raise kering.InvalidValueError(f"{typ} not a valid long running operation type")

        name = f"{typ}.{oid}"
        op = Op(oid=oid, type=typ, start=helping.nowIso8601(), metadata=metadata)

        # Overwrite any existing long running operation of this type for this resource.
        # resets the clock basically
        self.opr.ops.pin(keys=(name,), val=op)

        # Return Operation with full status check in case its already finished.
        return self.get(name)

    def get(self, name):
        if (op := self.opr.ops.get(keys=(name,))) is None:
            return None

        operation = self.status(op)

        return operation

    def getOperations(self, type=None):
        """ Return list of long running opterations, optionally filtered by type """
        ops = self.opr.ops.getItemIter()
        if type != None:
            ops = filter(lambda i: i[1].type == type, ops)

        def get_status(op):
            try:
                return self.status(op)
            except Exception as err:
                # self.status may throw an exception.
                # Handling error by returning an operation with error status
                return Operation(
                    name=f"{op.type}.{op.oid}",
                    metadata=op.metadata,
                    done=True,
                    error=Status(code=500, message=f"{err}"))

        return [get_status(op) for (_, op) in ops]

    def rem(self, name):
        """ Remove tracking of the long running operation represented by name """
        return self.opr.ops.rem(keys=(name,))

    def status(self, op):
        """  Calculate the status of an operation.

        Base on the type of an operation, determine the current status of the operation, including loading
        any availabie error messages if the operation failed of the sucessful result of the operation which
        will be the same that would be returned by the original endpoint if the operation were not long running

        Parameters:
            op (Op): database storage for long running operation

        Returns:
            Operation: The status of the operation, including any errors or results as appropriate.

        """

        operation = Operation(
            name=f"{op.type}.{op.oid}",
            metadata=op.metadata,
        )

        if op.type in (OpTypes.witness,):
            if op.oid not in self.hby.kevers:
                raise kering.ValidationError(f"long running {op.type} operation identifier {op.oid} not found")

            if "sn" not in op.metadata:
                raise kering.ValidationError(f"invalid long running {op.type} operation, metadata missing 'sn' field")

            sn = op.metadata["sn"]
            kever = self.hby.kevers[op.oid]
            sdig = self.hby.db.getKeLast(key=dbing.snKey(pre=kever.prefixer.qb64b, sn=sn))
            if sdig is not None:

                dgkey = dbing.dgKey(kever.prefixer.qb64b, bytes(sdig))
                wigs = self.hby.db.getWigs(dgkey)

                if len(wigs) >= kever.toader.num:
                    evt = self.hby.db.getEvt(dbing.dgKey(pre=kever.prefixer.qb64, dig=bytes(sdig)))
                    serder = serdering.SerderKERI(raw=bytes(evt))
                    operation.done = True
                    operation.response = serder.ked

                else:
                    start = helping.fromIso8601(op.start)
                    dtnow = helping.nowUTC()
                    if (dtnow - start) > datetime.timedelta(seconds=eventing.Kevery.TimeoutPWE):
                        operation.done = True
                        operation.error = Status(code=408,  # Using HTTP error codes here for lack of a better alternative
                                                 message=f"long running {op.type} for {op.oid} operation timed out before "
                                                         f"receiving sufficient witness receipts")
                    else:
                        operation.done = False

            else:
                operation.done = False

        elif op.type in (OpTypes.oobi,):
            if "oobi" not in op.metadata:
                raise kering.ValidationError("invalid OOBI long running operation, missing oobi")

            oobi = op.metadata["oobi"]
            obr = self.hby.db.roobi.get(keys=(oobi,))
            if obr is None:
                operation.done = False
            elif obr.state == Result.resolved:
                operation.done = True
                if obr.cid and obr.cid in self.hby.kevers:
                    kever = self.hby.kevers[obr.cid]
                    operation.response = asdict(kever.state())
                else:
                    operation.response = dict(oobi=oobi)

            elif obr.state == Result.failed:
                operation.done = True
                operation.failed = Status(code=500,
                                          message=f"resolving OOBI {op.oid} failed")
            else:
                operation.done = False

        elif op.type in (OpTypes.delegation, ):
            if op.oid not in self.hby.kevers:
                raise kering.ValidationError(f"long running {op.type} operation identifier {op.oid} not found")

            if "sn" not in op.metadata:
                raise kering.ValidationError(f"invalid long running {op.type} operation, metadata missing 'sn' field")

            kever = self.hby.kevers[op.oid]
            sn = op.metadata["sn"]
            seqner = coring.Seqner(sn=sn)
            sdig = self.hby.db.getKeLast(key=dbing.snKey(pre=op.oid, sn=sn))

            if self.swain.complete(kever.prefixer, seqner):
                evt = self.hby.db.getEvt(dbing.dgKey(pre=kever.prefixer.qb64, dig=bytes(sdig)))
                serder = serdering.SerderKERI(raw=bytes(evt))

                operation.done = True
                operation.response = serder.ked
            else:
                operation.done = False

        elif op.type in (OpTypes.group, ):
            if "sn" not in op.metadata:
                raise kering.ValidationError(f"invalid long running {op.type} operation, metadata missing 'sn' field")

            prefixer = coring.Prefixer(qb64=op.oid)
            seqner = coring.Seqner(sn=op.metadata["sn"])

            if self.counselor.complete(prefixer, seqner):
                sdig = self.hby.db.getKeLast(key=dbing.snKey(pre=op.oid, sn=seqner.sn))
                evt = self.hby.db.getEvt(dbing.dgKey(pre=prefixer.qb64, dig=bytes(sdig)))
                serder = serdering.SerderKERI(raw=bytes(evt))

                operation.done = True
                operation.response = serder.ked
            else:
                operation.done = False

        elif op.type in (OpTypes.query, ):
            if op.oid not in self.hby.kevers:
                operation.done = False

            else:
                kever = self.hby.kevers[op.oid]
                if "sn" in op.metadata:
                    sn = int(op.metadata['sn'], 16)
                    if kever.sn >= sn:
                        operation.done = True
                        operation.response = asdict(kever.state())
                    else:
                        operation.done = False
                elif "anchor" in op.metadata:
                    anchor = op.metadata["anchor"]
                    if self.hby.db.findAnchoringSealEvent(op.oid, seal=anchor) is not None:
                        operation.done = True
                        operation.response = asdict(kever.state())
                    else:
                        operation.done = False
                else:
                    ksn = None
                    for (_, saider) in self.hby.db.knas.getItemIter(keys=(op.oid,)):
                        ksn = self.hby.db.ksns.get(keys=(saider.qb64,))
                        break

                    if ksn and ksn.d == kever.serder.said:
                        operation.done = True
                        operation.response = asdict(kever.state())
                    else:
                        operation.done = False

        elif op.type in (OpTypes.registry, ):
            if op.oid not in self.hby.kevers:
                raise kering.ValidationError(
                    f"long running {op.type} operation identifier {op.oid} not found")
            if "anchor" not in op.metadata:
                raise kering.ValidationError(
                    f"invalid long running {op.type} operation, metadata missing 'anchor' field")

            anchor = op.metadata["anchor"]
            if self.hby.db.findAnchoringSealEvent(op.oid, seal=anchor) is not None:
                operation.done = True
                operation.response = dict(anchor=anchor)
            else:
                operation.done = False

        elif op.type in (OpTypes.credential,):
            if "ced" not in op.metadata:
                raise kering.ValidationError(
                    f"invalid long running {op.type} operation, metadata missing 'ced' field")

            ced = op.metadata["ced"]
            if self.credentialer.complete(ced['d']):
                operation.done = True
                operation.response = dict(ced=ced)
            else:
                operation.done = False

        elif op.type in (OpTypes.exchange,):
            if "said" not in op.metadata:
                raise kering.ValidationError(
                    f"invalid long running {op.type} operation, metadata missing 'said' field")

            said = op.metadata["said"]
            if self.exchanger.complete(said):
                operation.done = True
                operation.response = dict(said=said)
            else:
                operation.done = False

        elif op.type in (OpTypes.endrole, ):
            if "cid" not in op.metadata or "role" not in op.metadata or "eid" not in op.metadata:
                raise kering.ValidationError(
                    f"invalid long running {op.type} operation, metadata missing 'ced' field")

            cid = op.metadata['cid']
            role = op.metadata['role']
            eid = op.metadata['eid']

            end = self.hby.db.ends.get(keys=(cid, role, eid))
            if end and (end.enabled or end.allowed):
                saider = self.hby.db.eans.get(keys=(cid, role, eid))
                serder = self.hby.db.rpys.get(keys=(saider.qb64,))
                operation.done = True
                operation.response = serder.ked
            else:
                operation.done = False

        elif op.type in (OpTypes.challenge,):
            if op.oid not in self.hby.kevers:
                operation.done = False

            if "words" not in op.metadata:
                raise kering.ValidationError(
                    f"invalid long running {op.type} operation, metadata missing 'ced' field")

            found = False
            words = op.metadata["words"]
            saiders = self.hby.db.reps.get(keys=(op.oid,))
            for saider in saiders:
                exn = self.hby.db.exns.get(keys=(saider.qb64,))
                if words == exn.ked['a']['words']:
                    found = True
                    break

            if found:
                operation.done = True
                operation.response = dict(exn=exn.ked)
            else:
                operation.done = False

        elif op.type in (OpTypes.done, ):
            operation.done = True
            operation.response = op.metadata["response"]

        else:
            operation.done = True
            operation.error = Status(code=404,  # Using HTTP error codes here for lack of a better alternative
                                     message=f"long running operation type {op.type} unknown")

        return operation


class OperationCollectionEnd:
    @staticmethod
    def on_get(req, rep):
        """ Get list of long running operations

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
              content:
                  application/json:
                    schema:
                        type: array

        """
        agent = req.context.agent
        type = req.params.get("type")
        ops = agent.monitor.getOperations(type=type)
        rep.data = json.dumps(ops, default=lambda o: o.to_dict()).encode("utf-8")
        rep.content_type = "application/json"
        rep.status = falcon.HTTP_200


class OperationResourceEnd:
    """ Single Resource REST endpoint for long running operations

    """

    @staticmethod
    def on_get(req, rep, name):
        """  GET single resource REST endpoint

        Parameters:
            req (Request):  Falcon HTTP Request object
            rep (Response): Falcon HTTP Response object
            name (str): Long running operation resource name to load

        """
        agent = req.context.agent
        if (operation := agent.monitor.get(name)) is None:
            raise falcon.HTTPNotFound(title=f"long running operation '{name}' not found")

        rep.content_type = "application/json"
        rep.data = operation.to_json().encode("utf-8")
        rep.status = falcon.HTTP_200

    @staticmethod
    def on_delete(req, rep, name):
        """ DELETE single resource REST endpoint

        Args:
            req (Request):  Falcon HTTP Request object
            rep (Response): Falcon HTTP Response object
            name (str): Long running operation resource name to load

        """

        agent = req.context.agent
        if agent.monitor.get(name) is None:
            raise falcon.HTTPNotFound(title=f"long running operation '{name}' not found")

        deleted = agent.monitor.rem(name)
        if deleted:
            rep.status = falcon.HTTP_204
        else:
            raise falcon.HTTPInternalServerError(f"unable to delete long running operation {name}")
