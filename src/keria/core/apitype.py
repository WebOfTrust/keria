from dataclasses import dataclass, field
from marshmallow import fields
from typing import List, Dict, Any, Optional

@dataclass
class SADAttributes:
    d: str
    i: str
    LEI: str
    dt: str

@dataclass
class SAD:
    v: str
    d: str
    i: str
    ri: str
    s: str
    a: SADAttributes
    u: Optional[str] = field(default=None, metadata={"marshmallow_field": fields.Boolean(allow_none=False)})
    e: Optional[List[Any]] = field(default=None, metadata={"marshmallow_field": fields.Boolean(allow_none=False)})
    r: Optional[List[Any]] = field(default=None, metadata={"marshmallow_field": fields.Boolean(allow_none=False)})

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
class Anchor:
    pre: str
    sn: int
    d: str

@dataclass
class Seal:
    i: str
    s: str
    d: str
    t: Optional[str] = field(default=None, metadata={"marshmallow_field": fields.Boolean(allow_none=False)})
    p: Optional[str] = field(default=None, metadata={"marshmallow_field": fields.Boolean(allow_none=False)})

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
    status: Status
    anchor: Anchor
    anc: ANC
    ancAttachment: str
