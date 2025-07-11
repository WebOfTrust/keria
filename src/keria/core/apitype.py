from dataclasses import dataclass, field
from marshmallow import fields, ValidationError, Schema
from typing import List, Dict, Any, Optional, Tuple, Literal

class EmptyDictSchema(Schema):
    class Meta:
        additional = ()

@dataclass
class SADAttributes:
    d: str
    LEI: str
    dt: str
    i: Optional[str] = field(default=None, metadata={"marshmallow_field": fields.String(allow_none=False)})

@dataclass
class Seal:
    s: str
    d: str
    i: Optional[str] = field(default=None, metadata={"marshmallow_field": fields.String(allow_none=False)})
    t: Optional[str] = field(default=None, metadata={"marshmallow_field": fields.String(allow_none=False)})
    p: Optional[str] = field(default=None, metadata={"marshmallow_field": fields.String(allow_none=False)})

# The following fields are REQUIRED [v, d, i, s]
@dataclass
class SAD:
    v: str
    d: str
    i: str
    s: str
    ri: Optional[str] = field(default=None, metadata={"marshmallow_field": fields.String(allow_none=False)})
    a: Optional[SADAttributes] = field(default=None, metadata={"marshmallow_field": fields.Dict(allow_none=False)})
    u: Optional[str] = field(default=None, metadata={"marshmallow_field": fields.String(allow_none=False)})
    e: Optional[List[Any]] = field(default=None, metadata={"marshmallow_field": fields.List(fields.Raw(), allow_none=False)})
    r: Optional[List[Any]] = field(default=None, metadata={"marshmallow_field": fields.List(fields.Raw(), allow_none=False)})

@dataclass
class ISS:
    v: str
    t: str
    d: str
    i: str
    s: str
    ri: str
    dt: str

@dataclass
class Schema:
    _id: str = field(metadata={"data_key": "$id"})
    _schema: str = field(metadata={"data_key": "$schema"})
    title: str
    description: str
    type: str
    credentialType: str
    version: str
    properties: Dict[str, Any]
    additionalProperties: bool
    required: List[str]

@dataclass
class StatusAnchor:
    s: int
    d: str

@dataclass
class Status:
    vn: List[int]
    i: str
    s: str
    d: str
    ri: str
    ra: Dict[str, Any]
    a: StatusAnchor
    dt: str
    et: str


@dataclass
class CredentialStateBase:
    vn: Tuple[int, int]
    i: str
    s: str
    d: str
    ri: str
    a: Seal
    dt: str
    et: str  # Will be narrowed in the subclasses

@dataclass
class CredentialStateIssOrRev(CredentialStateBase):
    et: Literal['iss', 'rev']
    ra: Dict[str, Any] = field(
        metadata={
            "marshmallow_field": fields.Nested(EmptyDictSchema(), allow_none=False, required=True)
        }
    )

@dataclass
class RaFields:
    i: str
    s: str
    d: str

@dataclass
class CredentialStateBisOrBrv(CredentialStateBase):
    et: Literal['bis', 'brv']
    ra: RaFields

@dataclass
class Anchor:
    pre: str
    sn: int
    d: str

@dataclass
class ANC:
    v: str
    t: str
    d: str
    i: str
    s: str
    p: str
    a: List[Seal]

@dataclass
class Credential:
    sad: SAD
    atc: str
    iss: ISS
    issAtc: str = field(metadata={"data_key": "issAtc"})
    pre: str
    schema: Schema
    chains: List[Dict[str, Any]]
    status: Any
    anchor: Anchor
    anc: ANC
    ancAttachment: str

#Registry
@dataclass
class Registry:
    name: str
    regk: str
    pre: str
    state: Any
