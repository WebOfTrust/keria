# -*- encoding: utf-8 -*-
"""
KERIA
keria.core.operation module

"""

from dataclasses import dataclass, field
from marshmallow import fields
from typing import Union
from marshmallow_dataclass import class_schema
from keria.app import aiding, credentialing
from keria.app.credentialing import (
    Anchor,
    AnchoringEvent,
    ACDC_V_1,
    ACDC_V_2,
    ICP_V_1,
    ICP_V_2,
    ROT_V_1,
    ROT_V_2,
    DIP_V_1,
    DIP_V_2,
    IXN_V_1,
    IXN_V_2,
    DRT_V_1,
    DRT_V_2,
)
from keria.app.aiding import (
    KeyStateRecord,
    RPY_V_1,
    RPY_V_2,
)
from keria.peer.exchanging import EXN_V_1, EXN_V_2
from keria.core.longrunning import (
    OperationStatus,
    PendingOperation,
    CompletedOperation,
    FailedOperation,
)


@dataclass
class OOBIMetadata:
    oobi: str


@dataclass
class BaseOOBIOperation:
    metadata: OOBIMetadata = field(
        default_factory=OOBIMetadata,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(OOBIMetadata), required=False
            )
        },
    )


@dataclass
class PendingOOBIOperation(BaseOOBIOperation, PendingOperation):
    pass


@dataclass(kw_only=True)
class CompletedOOBIOperation(BaseOOBIOperation, CompletedOperation):
    response: aiding.KeyStateRecord = field(
        default_factory=aiding.KeyStateRecord,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(aiding.KeyStateRecord), required=True
            )
        },
    )


@dataclass(kw_only=True)
class FailedOOBIOperation(BaseOOBIOperation, FailedOperation):
    error: OperationStatus = field(
        default=None,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(OperationStatus), required=True
            )
        },
    )


OOBIOperation = Union[PendingOOBIOperation, CompletedOOBIOperation, FailedOOBIOperation]


@dataclass
class QueryMetadata:
    pre: str
    sn: int
    anchor: credentialing.Anchor = field(
        default_factory=credentialing.Anchor,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(credentialing.Anchor), required=False
            )
        },
    )


@dataclass
class BaseQueryOperation:
    metadata: QueryMetadata = field(
        default_factory=QueryMetadata,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(QueryMetadata), required=False
            )
        },
    )


@dataclass
class PendingQueryOperation(BaseQueryOperation, PendingOperation):
    pass


@dataclass(kw_only=True)
class CompletedQueryOperation(BaseQueryOperation, CompletedOperation):
    response: aiding.KeyStateRecord = field(
        default_factory=aiding.KeyStateRecord,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(aiding.KeyStateRecord), required=True
            )
        },
    )


@dataclass(kw_only=True)
class FailedQueryOperation(BaseQueryOperation, FailedOperation):
    error: OperationStatus = field(
        default=None,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(OperationStatus), required=True
            )
        },
    )


QueryOperation = Union[
    PendingQueryOperation, CompletedQueryOperation, FailedQueryOperation
]


@dataclass
class WitnessMetadata:
    pre: str
    sn: int


@dataclass
class BaseWitnessOperation:
    metadata: WitnessMetadata = field(
        default_factory=WitnessMetadata,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(WitnessMetadata), required=False
            )
        },
    )


@dataclass
class PendingWitnessOperation(BaseWitnessOperation, PendingOperation):
    pass


@dataclass(kw_only=True)
class CompletedWitnessOperation(BaseWitnessOperation, CompletedOperation):
    response: Union[ICP_V_1, ICP_V_2, ROT_V_1, ROT_V_2, IXN_V_1, IXN_V_2] = field(
        default=None, metadata={"required": True}
    )  # type: ignore


@dataclass(kw_only=True)
class FailedWitnessOperation(BaseWitnessOperation, FailedOperation):
    error: OperationStatus = field(
        default=None,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(OperationStatus), required=True
            )
        },
    )


WitnessOperation = Union[
    PendingWitnessOperation, CompletedWitnessOperation, FailedWitnessOperation
]


@dataclass
class DelegationMetadata:
    pre: str
    sn: int


@dataclass
class BaseDelegationOperation:
    metadata: DelegationMetadata = field(
        default_factory=DelegationMetadata,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(DelegationMetadata), required=False
            )
        },
    )


@dataclass
class PendingDelegationOperation(BaseDelegationOperation, PendingOperation):
    pass


@dataclass(kw_only=True)
class CompletedDelegationOperation(BaseDelegationOperation, CompletedOperation):
    response: Union[DIP_V_1, DIP_V_2, DRT_V_1, DRT_V_2] = field(
        default=None, metadata={"required": True}
    )  # type: ignore


@dataclass(kw_only=True)
class FailedDelegationOperation(BaseDelegationOperation, FailedOperation):
    error: OperationStatus = field(
        default=None,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(OperationStatus), required=True
            )
        },
    )


DelegationOperation = Union[
    PendingDelegationOperation, CompletedDelegationOperation, FailedDelegationOperation
]


@dataclass
class DoneOperationMetadata:
    response: Union[ICP_V_1, ICP_V_2, ROT_V_1, ROT_V_2, EXN_V_1, EXN_V_2]  # type: ignore
    pre: str = None


@dataclass
class BaseDoneOperation:
    metadata: DoneOperationMetadata = field(
        default_factory=DoneOperationMetadata,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(DoneOperationMetadata), required=False
            )
        },
    )


@dataclass
class PendingDoneOperation(BaseDoneOperation, PendingOperation):
    pass


@dataclass(kw_only=True)
class CompletedDoneOperation(BaseDoneOperation, CompletedOperation):
    response: Union[ICP_V_1, ICP_V_2, ROT_V_1, ROT_V_2, EXN_V_1, EXN_V_2] = field(
        default=None, metadata={"required": True}
    )  # type: ignore


@dataclass(kw_only=True)
class FailedDoneOperation(BaseDoneOperation, FailedOperation):
    error: OperationStatus = field(
        default=None,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(OperationStatus), required=True
            )
        },
    )


DoneOperation = Union[PendingDoneOperation, CompletedDoneOperation, FailedDoneOperation]


@dataclass
class GroupOperationMetadata:
    pre: str
    sn: int


@dataclass
class BaseGroupOperation:
    metadata: GroupOperationMetadata = field(
        default_factory=GroupOperationMetadata,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(GroupOperationMetadata), required=False
            )
        },
    )


@dataclass
class PendingGroupOperation(BaseGroupOperation, PendingOperation):
    pass


@dataclass(kw_only=True)
class CompletedGroupOperation(BaseGroupOperation, CompletedOperation):
    response: AnchoringEvent = field(default=None, metadata={"required": True})  # type: ignore


@dataclass(kw_only=True)
class FailedGroupOperation(BaseGroupOperation, FailedOperation):
    error: OperationStatus = field(
        default=None,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(OperationStatus), required=True
            )
        },
    )


GroupOperation = Union[
    PendingGroupOperation, CompletedGroupOperation, FailedGroupOperation
]


@dataclass
class DelegatorOperationMetadata:
    pre: str
    teepre: str
    anchor: credentialing.Anchor = field(
        default_factory=credentialing.Anchor,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(credentialing.Anchor), required=False
            )
        },
    )
    depends: Union["GroupOperation", "WitnessOperation", "DoneOperation"] = None  # type: ignore


@dataclass
class BaseDelegatorOperation:
    metadata: DelegatorOperationMetadata = field(
        default_factory=DelegatorOperationMetadata,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(DelegatorOperationMetadata), required=False
            )
        },
    )


@dataclass
class PendingDelegatorOperation(BaseDelegatorOperation, PendingOperation):
    pass


@dataclass(kw_only=True)
class CompletedDelegatorOperation(BaseDelegatorOperation, CompletedOperation):
    response: str


@dataclass(kw_only=True)
class FailedDelegatorOperation(BaseDelegatorOperation, FailedOperation):
    error: OperationStatus = field(
        default=None,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(OperationStatus), required=True
            )
        },
    )


DelegatorOperation = Union[
    PendingDelegatorOperation, CompletedDelegatorOperation, FailedDelegatorOperation
]


@dataclass
class SubmitOperationMetadata:
    pre: str
    sn: int


@dataclass
class BaseSubmitOperation:
    metadata: SubmitOperationMetadata = field(
        default_factory=SubmitOperationMetadata,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(SubmitOperationMetadata), required=False
            )
        },
    )


@dataclass
class PendingSubmitOperation(BaseSubmitOperation, PendingOperation):
    pass


@dataclass(kw_only=True)
class CompletedSubmitOperation(BaseSubmitOperation, CompletedOperation):
    response: KeyStateRecord = field(
        default=None,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(KeyStateRecord), required=True
            )
        },
    )


@dataclass(kw_only=True)
class FailedSubmitOperation(BaseSubmitOperation, FailedOperation):
    error: OperationStatus = field(
        default=None,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(OperationStatus), required=True
            )
        },
    )


SubmitOperation = Union[
    PendingSubmitOperation, CompletedSubmitOperation, FailedSubmitOperation
]


@dataclass
class EndRoleMetadata:
    cid: str
    role: str
    eid: str


@dataclass
class BaseEndRoleOperation:
    metadata: EndRoleMetadata = field(
        default_factory=EndRoleMetadata,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(EndRoleMetadata), required=False
            )
        },
    )


@dataclass
class PendingEndRoleOperation(BaseEndRoleOperation, PendingOperation):
    pass


@dataclass(kw_only=True)
class CompletedEndRoleOperation(BaseEndRoleOperation, CompletedOperation):
    response: Union[RPY_V_1, RPY_V_2] = field(default=None, metadata={"required": True})  # type: ignore


@dataclass(kw_only=True)
class FailedEndRoleOperation(BaseEndRoleOperation, FailedOperation):
    error: OperationStatus = field(
        default=None,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(OperationStatus), required=True
            )
        },
    )


EndRoleOperation = Union[
    PendingEndRoleOperation, CompletedEndRoleOperation, FailedEndRoleOperation
]


@dataclass
class LocSchemeMetadata:
    eid: str
    scheme: str
    url: str


@dataclass
class BaseLocSchemeOperation:
    metadata: LocSchemeMetadata = field(
        default_factory=LocSchemeMetadata,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(LocSchemeMetadata), required=False
            )
        },
    )


@dataclass
class PendingLocSchemeOperation(BaseLocSchemeOperation, PendingOperation):
    pass


@dataclass(kw_only=True)
class CompletedLocSchemeOperation(BaseLocSchemeOperation, CompletedOperation):
    response: LocSchemeMetadata = field(
        default_factory=LocSchemeMetadata,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(LocSchemeMetadata), required=True
            )
        },
    )


@dataclass(kw_only=True)
class FailedLocSchemeOperation(BaseLocSchemeOperation, FailedOperation):
    error: OperationStatus = field(
        default=None,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(OperationStatus), required=True
            )
        },
    )


LocSchemeOperation = Union[
    PendingLocSchemeOperation, CompletedLocSchemeOperation, FailedLocSchemeOperation
]


@dataclass
class ChallengeOperationMetadata:
    words: list[str]


@dataclass
class ChallengeOperationResponse:
    exn: Union[EXN_V_1, EXN_V_2]  # type: ignore


@dataclass
class BaseChallengeOperation:
    metadata: ChallengeOperationMetadata = field(
        default_factory=ChallengeOperationMetadata,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(ChallengeOperationMetadata), required=False
            )
        },
    )


@dataclass
class PendingChallengeOperation(BaseChallengeOperation, PendingOperation):
    pass


@dataclass(kw_only=True)
class CompletedChallengeOperation(BaseChallengeOperation, CompletedOperation):
    response: ChallengeOperationResponse = field(
        default_factory=ChallengeOperationResponse,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(ChallengeOperationResponse), required=True
            )
        },
    )


@dataclass(kw_only=True)
class FailedChallengeOperation(BaseChallengeOperation, FailedOperation):
    error: OperationStatus = field(
        default=None,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(OperationStatus), required=True
            )
        },
    )


ChallengeOperation = Union[
    PendingChallengeOperation, CompletedChallengeOperation, FailedChallengeOperation
]


@dataclass
class RegistryOperationMetadata:
    pre: str
    depends: Union[
        "GroupOperation", "WitnessOperation", "DoneOperation", "DelegationOperation"
    ]
    anchor: Anchor = field(
        default_factory=Anchor,
        metadata={
            "marshmallow_field": fields.Nested(class_schema(Anchor), required=True)
        },
    )


@dataclass
class RegistryOperationResponse:
    anchor: Anchor = field(
        default_factory=Anchor,
        metadata={
            "marshmallow_field": fields.Nested(class_schema(Anchor), required=True)
        },
    )


@dataclass
class BaseRegistryOperation:
    metadata: RegistryOperationMetadata = field(
        default_factory=RegistryOperationMetadata,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(RegistryOperationMetadata), required=False
            )
        },
    )


@dataclass
class PendingRegistryOperation(BaseRegistryOperation, PendingOperation):
    pass


@dataclass(kw_only=True)
class CompletedRegistryOperation(BaseRegistryOperation, CompletedOperation):
    response: RegistryOperationResponse = field(
        default_factory=RegistryOperationResponse,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(RegistryOperationResponse), required=True
            )
        },
    )


@dataclass(kw_only=True)
class FailedRegistryOperation(BaseRegistryOperation, FailedOperation):
    error: OperationStatus = field(
        default=None,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(OperationStatus), required=True
            )
        },
    )


RegistryOperation = Union[
    PendingRegistryOperation, CompletedRegistryOperation, FailedRegistryOperation
]


@dataclass
class CredentialOperationMetadata:
    ced: Union[ACDC_V_1, ACDC_V_2]  # type: ignore
    depends: Union[ROT_V_1, ROT_V_2, DRT_V_1, DRT_V_2, IXN_V_1, IXN_V_2] = None  # type: ignore


@dataclass
class CredentialOperationResponse:
    ced: Union[ACDC_V_1, ACDC_V_2] = None  # type: ignore


@dataclass
class BaseCredentialOperation:
    metadata: CredentialOperationMetadata = field(
        default_factory=CredentialOperationMetadata,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(CredentialOperationMetadata), required=False
            )
        },
    )


@dataclass
class PendingCredentialOperation(BaseCredentialOperation, PendingOperation):
    pass


@dataclass(kw_only=True)
class CompletedCredentialOperation(BaseCredentialOperation, CompletedOperation):
    response: CredentialOperationResponse = field(
        default_factory=CredentialOperationResponse,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(CredentialOperationResponse), required=True
            )
        },
    )


@dataclass(kw_only=True)
class FailedCredentialOperation(BaseCredentialOperation, FailedOperation):
    error: OperationStatus = field(
        default=None,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(OperationStatus), required=True
            )
        },
    )


CredentialOperation = Union[
    PendingCredentialOperation, CompletedCredentialOperation, FailedCredentialOperation
]


@dataclass
class ExchangeOperationMetadata:
    said: str


@dataclass
class BaseExchangeOperation:
    metadata: ExchangeOperationMetadata = field(
        default_factory=ExchangeOperationMetadata,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(ExchangeOperationMetadata), required=False
            )
        },
    )


@dataclass
class PendingExchangeOperation(BaseExchangeOperation, PendingOperation):
    pass


@dataclass(kw_only=True)
class CompletedExchangeOperation(BaseExchangeOperation, CompletedOperation):
    response: ExchangeOperationMetadata = field(
        default_factory=ExchangeOperationMetadata,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(ExchangeOperationMetadata), required=True
            )
        },
    )


@dataclass(kw_only=True)
class FailedExchangeOperation(BaseExchangeOperation, FailedOperation):
    error: OperationStatus = field(
        default=None,
        metadata={
            "marshmallow_field": fields.Nested(
                class_schema(OperationStatus), required=True
            )
        },
    )


ExchangeOperation = Union[
    PendingExchangeOperation, CompletedExchangeOperation, FailedExchangeOperation
]
