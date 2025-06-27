import copy
import falcon
import marshmallow_dataclass
from apispec import yaml_utils
from apispec.core import VALID_METHODS, APISpec
from apispec.ext.marshmallow import MarshmallowPlugin

from keria.app import aiding, agenting, grouping, notifying
from keria.peer import exchanging
from ..core import optypes
from ..utils.openapi import applyAltConstraintsToOpenApiSchema
from . import credentialing
from keri.core import coring
from ..utils.openapi import enumSchemaFromNamedtuple

"""
KERIA
keria.app.specing module

OpenAPI Description Resource for the KERI and ACDC ReST interface
"""


class AgentSpecResource:
    """
    OpenAPI Description Resource for the KERI and ACDC ReST interface

    Contains all the endpoint descriptions for the KERI admin interface including:
    1. Creating and managing autonomic identifiers (AIDs) including multi-signature groups.
    2. Creating and managing authentic chained data containers (ACDCs)
    """

    def __init__(self, app, title, version="1.0.1", openapi_version="3.1.0"):
        self.spec = APISpec(
            title=title,
            version=version,
            openapi_version=openapi_version,
            plugins=[MarshmallowPlugin()],
        )

        # Register marshmallow schemas (pass class)
        self.spec.components.schema("ACDC_V_1", schema=credentialing.ACDCSchema_V_1)
        self.spec.components.schema("ACDC_V_2", schema=credentialing.ACDCSchema_V_2)
        self.spec.components.schema(
            "IssEvent",
            schema=marshmallow_dataclass.class_schema(credentialing.IssEvent)(),
        )
        self.spec.components.schema(
            "Schema", schema=marshmallow_dataclass.class_schema(credentialing.Schema)()
        )
        self.spec.components.schema(
            "Anchor", schema=marshmallow_dataclass.class_schema(credentialing.Anchor)()
        )
        self.spec.components.schema(
            "Seal", schema=marshmallow_dataclass.class_schema(aiding.Seal)()
        )
        self.spec.components.schema(
            "IXN_V_1",
            schema=marshmallow_dataclass.class_schema(aiding.IXN_V_1)(),
        )
        self.spec.components.schema(
            "IXN_V_2",
            schema=marshmallow_dataclass.class_schema(aiding.IXN_V_2)(),
        )
        self.spec.components.schema(
            "ICP_V_1",
            schema=marshmallow_dataclass.class_schema(aiding.ICP_V_1)(),
        )
        self.spec.components.schema(
            "ICP_V_2",
            schema=marshmallow_dataclass.class_schema(aiding.ICP_V_2)(),
        )
        self.spec.components.schema(
            "ROT_V_1",
            schema=marshmallow_dataclass.class_schema(aiding.ROT_V_1)(),
        )
        self.spec.components.schema(
            "ROT_V_2",
            schema=marshmallow_dataclass.class_schema(aiding.ROT_V_2)(),
        )
        self.spec.components.schema(
            "DIP_V_1",
            schema=marshmallow_dataclass.class_schema(aiding.DIP_V_1)(),
        )
        self.spec.components.schema(
            "DIP_V_2",
            schema=marshmallow_dataclass.class_schema(aiding.DIP_V_2)(),
        )
        self.spec.components.schema(
            "DRT_V_1",
            schema=marshmallow_dataclass.class_schema(aiding.DRT_V_1)(),
        )
        self.spec.components.schema(
            "DRT_V_2",
            schema=marshmallow_dataclass.class_schema(aiding.DRT_V_2)(),
        )
        self.spec.components.schema(
            "RPY_V_1", schema=marshmallow_dataclass.class_schema(aiding.RPY_V_1)()
        )
        self.spec.components.schema(
            "RPY_V_2", schema=marshmallow_dataclass.class_schema(aiding.RPY_V_2)()
        )
        self.spec.components.schema(
            "VCP_V_1",
            schema=marshmallow_dataclass.class_schema(agenting.VCP_V_1)(),
        )
        self.spec.components.schema(
            "ISS_V_1",
            schema=marshmallow_dataclass.class_schema(agenting.ISS_V_1)(),
        )
        self.spec.components.schema(
            "REV_V_1",
            schema=marshmallow_dataclass.class_schema(agenting.REV_V_1)(),
        )
        self.spec.components.schema(
            "EXN_V_1",
            schema=marshmallow_dataclass.class_schema(exchanging.EXN_V_1)(),
        )
        self.spec.components.schema(
            "EXN_V_2",
            schema=marshmallow_dataclass.class_schema(exchanging.EXN_V_2)(),
        )
        self.spec.components.schema(
            "Credential",
            schema=marshmallow_dataclass.class_schema(credentialing.ClonedCredential)(),
        )
        self.spec.components.schema(
            "CredentialStateIssOrRev",
            schema=marshmallow_dataclass.class_schema(
                credentialing.CredentialStateIssOrRev
            ),
        )
        self.spec.components.schema(
            "CredentialStateBisOrBrv",
            schema=marshmallow_dataclass.class_schema(
                credentialing.CredentialStateBisOrBrv
            ),
        )

        # Patch the schema to force additionalProperties=True
        acdc_attributes_schema = self.spec.components.schemas["ACDCAttributes"]
        acdc_attributes_schema["additionalProperties"] = True

        # The ACDC class has alts constraints like {'a': 'A', 'A': 'a'}
        acdc_schema_v1 = self.spec.components.schemas["ACDC_V_1"]
        if hasattr(credentialing.ACDCSchema_V_1, "_alt_constraints"):
            applyAltConstraintsToOpenApiSchema(
                acdc_schema_v1, credentialing.ACDCSchema_V_1._alt_constraints
            )

        acdc_schema_v2 = self.spec.components.schemas["ACDC_V_2"]
        if hasattr(credentialing.ACDCSchema_V_2, "_alt_constraints"):
            applyAltConstraintsToOpenApiSchema(
                acdc_schema_v2, credentialing.ACDCSchema_V_2._alt_constraints
            )

        credentialSchema = self.spec.components.schemas["Credential"]
        credentialSchema["properties"]["sad"] = {
            "oneOf": [
                {"$ref": "#/components/schemas/ACDC_V_1"},
                {"$ref": "#/components/schemas/ACDC_V_2"},
            ]
        }
        ancEvent = {
            "oneOf": [
                {"$ref": "#/components/schemas/IXN_V_1"},
                {"$ref": "#/components/schemas/IXN_V_2"},
                {"$ref": "#/components/schemas/ICP_V_1"},
                {"$ref": "#/components/schemas/ICP_V_2"},
                {"$ref": "#/components/schemas/ROT_V_1"},
                {"$ref": "#/components/schemas/ROT_V_2"},
                {"$ref": "#/components/schemas/DIP_V_1"},
                {"$ref": "#/components/schemas/DIP_V_2"},
                {"$ref": "#/components/schemas/DRT_V_1"},
                {"$ref": "#/components/schemas/DRT_V_2"},
            ]
        }
        credentialSchema["properties"]["anc"] = ancEvent

        # CredentialState
        self.spec.components.schemas["CredentialState"] = {
            "oneOf": [
                {"$ref": "#/components/schemas/CredentialStateIssOrRev"},
                {"$ref": "#/components/schemas/CredentialStateBisOrBrv"},
            ]
        }

        credentialSchema["properties"]["status"] = {
            "$ref": "#/components/schemas/CredentialState"
        }

        # Registries
        self.spec.components.schema(
            "Registry",
            schema=marshmallow_dataclass.class_schema(credentialing.Registry)(),
        )
        registrySchema = self.spec.components.schemas["Registry"]
        registrySchema["properties"]["state"] = {
            "$ref": "#/components/schemas/CredentialState"
        }

        self.spec.components.schema(
            "AgentResourceResult",
            schema=marshmallow_dataclass.class_schema(aiding.AgentResourceResult)(),
        )

        agentControllerSchema = self.spec.components.schemas["Controller"]
        agentControllerSchema["properties"]["ee"] = {
            "oneOf": [
                {"$ref": "#/components/schemas/ICP_V_1"},
                {"$ref": "#/components/schemas/ICP_V_2"},
                {"$ref": "#/components/schemas/ROT_V_1"},
                {"$ref": "#/components/schemas/ROT_V_2"},
                {"$ref": "#/components/schemas/DIP_V_1"},
                {"$ref": "#/components/schemas/DIP_V_2"},
                {"$ref": "#/components/schemas/DRT_V_1"},
                {"$ref": "#/components/schemas/DRT_V_2"},
            ]
        }

        # Register HabState
        self.spec.components.schema(
            "HabState", schema=marshmallow_dataclass.class_schema(aiding.HabState)()
        )
        self.spec.components.schema(
            "SaltyState", schema=marshmallow_dataclass.class_schema(aiding.SaltyState)()
        )
        self.spec.components.schema(
            "RandyKeyState",
            schema=marshmallow_dataclass.class_schema(aiding.RandyKeyState)(),
        )
        self.spec.components.schema(
            "GroupKeyState",
            schema=marshmallow_dataclass.class_schema(aiding.GroupKeyState)(),
        )
        self.spec.components.schema(
            "ExternState",
            schema=marshmallow_dataclass.class_schema(aiding.ExternState)(),
        )

        statesList = [
            {
                "required": ["salty"],
                "properties": {"salty": {"$ref": "#/components/schemas/SaltyState"}},
            },
            {
                "required": ["randy"],
                "properties": {"randy": {"$ref": "#/components/schemas/RandyKeyState"}},
            },
            {
                "required": ["group"],
                "properties": {"group": {"$ref": "#/components/schemas/GroupKeyState"}},
            },
            {
                "required": ["extern"],
                "properties": {"extern": {"$ref": "#/components/schemas/ExternState"}},
            },
        ]

        self.spec.components.schema(
            "HabStateBase",
            schema=marshmallow_dataclass.class_schema(aiding.HabStateBase)(),
        )
        habStateSchemaBase = self.spec.components.schemas["HabStateBase"]
        habStateSchemaBase["oneOf"] = statesList
        habStateSchema = self.spec.components.schemas["HabState"]
        habStateSchema["oneOf"] = statesList

        self.spec.components.schemas["GroupKeyState"]["properties"]["mhab"] = {
            "$ref": "#/components/schemas/HabState"
        }
        self.spec.components.schemas["Tier"] = enumSchemaFromNamedtuple(
            coring.Tiers, description="Tier of key material"
        )
        saltyStateSchema = self.spec.components.schemas["SaltyState"]
        saltyStateSchema["properties"]["tier"] = {"$ref": "#/components/schemas/Tier"}

        # Patch the schema to force additionalProperties=True
        externStateSchema = self.spec.components.schemas["ExternState"]
        externStateSchema["additionalProperties"] = True

        # OOBIS
        self.spec.components.schema(
            "OOBI", schema=marshmallow_dataclass.class_schema(aiding.OOBI)()
        )

        # End Roles
        self.spec.components.schema(
            "EndRole", schema=marshmallow_dataclass.class_schema(aiding.EndRole)()
        )

        # Register the Challenge schema
        self.spec.components.schema(
            "Challenge", schema=marshmallow_dataclass.class_schema(aiding.Challenge)()
        )

        # Register the Contact schema
        self.spec.components.schema(
            "Contact", schema=marshmallow_dataclass.class_schema(aiding.Contact)()
        )
        # Patch the schema to force additionalProperties=True
        contactSchema = self.spec.components.schemas["Contact"]
        contactSchema["additionalProperties"] = True

        # Register the GroupMember schema
        self.spec.components.schema(
            "GroupMember",
            schema=marshmallow_dataclass.class_schema(aiding.GroupMember)(),
        )

        # Register the KeyEventRecord schema
        self.spec.components.schema(
            "KeyEventRecord",
            schema=marshmallow_dataclass.class_schema(agenting.KeyEventRecord)(),
        )
        keyEventRecordSchema = self.spec.components.schemas["KeyEventRecord"]
        keyEventRecordSchema["properties"]["ked"] = ancEvent

        # Register the AgentConfig schema
        self.spec.components.schema(
            "AgentConfig",
            schema=marshmallow_dataclass.class_schema(agenting.AgentConfig)(),
        )

        # Register mulisig exn schemas
        self.spec.components.schemas["Exn"] = {
            "oneOf": [
                {"$ref": "#/components/schemas/EXN_V_1"},
                {"$ref": "#/components/schemas/EXN_V_2"},
            ]
        }
        self.spec.components.schemas["Icp"] = {
            "oneOf": [
                {"$ref": "#/components/schemas/ICP_V_1"},
                {"$ref": "#/components/schemas/ICP_V_2"},
            ]
        }
        self.spec.components.schemas["Rot"] = {
            "oneOf": [
                {"$ref": "#/components/schemas/ROT_V_1"},
                {"$ref": "#/components/schemas/ROT_V_2"},
            ]
        }
        self.spec.components.schemas["Vcp"] = {
            "oneOf": [
                {"$ref": "#/components/schemas/VCP_V_1"},
            ]
        }
        self.spec.components.schemas["Iss"] = {
            "oneOf": [
                {"$ref": "#/components/schemas/ISS_V_1"},
            ]
        }
        self.spec.components.schemas["Ixn"] = {
            "oneOf": [
                {"$ref": "#/components/schemas/IXN_V_1"},
                {"$ref": "#/components/schemas/IXN_V_2"},
            ]
        }
        self.spec.components.schemas["Rpy"] = {
            "oneOf": [
                {"$ref": "#/components/schemas/RPY_V_1"},
                {"$ref": "#/components/schemas/RPY_V_2"},
            ]
        }

        # Register Notification schema
        self.spec.components.schema(
            "Notification",
            schema=marshmallow_dataclass.class_schema(notifying.Notification)(),
        )

        # Patch the schema to force additionalProperties=True
        notificationDataSchema = self.spec.components.schemas["NotificationData"]
        notificationDataSchema["additionalProperties"] = True

        # Register the ExchangeResource schema
        self.spec.components.schema(
            "ExchangeResource",
            schema=marshmallow_dataclass.class_schema(exchanging.ExchangeResource)(),
        )
        exchangeResourceSchema = self.spec.components.schemas["ExchangeResource"]
        exchangeResourceSchema["properties"]["exn"] = {
            "$ref": "#/components/schemas/Exn"
        }

        # Register Grouping schemas
        self.spec.components.schema(
            "MultisigInceptEmbeds",
            schema=marshmallow_dataclass.class_schema(grouping.MultisigInceptEmbeds),
        )
        self.spec.components.schemas["MultisigInceptEmbeds"]["properties"]["icp"] = {
            "$ref": "#/components/schemas/Icp"
        }

        self.spec.components.schema(
            "MultisigRotateEmbeds",
            schema=marshmallow_dataclass.class_schema(grouping.MultisigRotateEmbeds),
        )
        self.spec.components.schemas["MultisigRotateEmbeds"]["properties"]["rot"] = {
            "$ref": "#/components/schemas/Rot"
        }

        self.spec.components.schema(
            "MultisigInteractEmbeds",
            schema=marshmallow_dataclass.class_schema(grouping.MultisigInteractEmbeds),
        )
        self.spec.components.schemas["MultisigInteractEmbeds"]["properties"]["ixn"] = {
            "$ref": "#/components/schemas/Ixn"
        }

        self.spec.components.schema(
            "MultisigRegistryInceptEmbeds",
            schema=marshmallow_dataclass.class_schema(
                grouping.MultisigRegistryInceptEmbeds
            ),
        )
        self.spec.components.schemas["MultisigRegistryInceptEmbeds"]["properties"][
            "vcp"
        ] = {"$ref": "#/components/schemas/Vcp"}
        self.spec.components.schemas["MultisigRegistryInceptEmbeds"]["properties"][
            "anc"
        ] = ancEvent

        self.spec.components.schema(
            "MultisigIssueEmbeds",
            schema=marshmallow_dataclass.class_schema(grouping.MultisigIssueEmbeds),
        )
        self.spec.components.schemas["MultisigIssueEmbeds"]["properties"]["acdc"] = {
            "oneOf": [
                {"$ref": "#/components/schemas/ACDC_V_1"},
                {"$ref": "#/components/schemas/ACDC_V_2"},
            ]
        }
        self.spec.components.schemas["MultisigIssueEmbeds"]["properties"]["iss"] = {
            "$ref": "#/components/schemas/Iss"
        }
        self.spec.components.schemas["MultisigIssueEmbeds"]["properties"]["anc"] = (
            ancEvent
        )

        self.spec.components.schema(
            "MultisigRevokeEmbeds",
            schema=marshmallow_dataclass.class_schema(grouping.MultisigRevokeEmbeds),
        )
        self.spec.components.schemas["MultisigRevokeEmbeds"]["properties"]["rev"] = {
            "$ref": "#/components/schemas/REV_V_1"
        }
        self.spec.components.schemas["MultisigRevokeEmbeds"]["properties"]["anc"] = (
            ancEvent
        )

        self.spec.components.schema(
            "MultisigRpyEmbeds",
            schema=marshmallow_dataclass.class_schema(grouping.MultisigRpyEmbeds),
        )
        self.spec.components.schemas["MultisigRpyEmbeds"]["properties"]["rpy"] = {
            "$ref": "#/components/schemas/Rpy"
        }

        self.spec.components.schema(
            "MultisigExnEmbeds",
            schema=marshmallow_dataclass.class_schema(grouping.MultisigExnEmbeds),
        )
        self.spec.components.schemas["MultisigExnEmbeds"]["properties"]["exn"] = {
            "$ref": "#/components/schemas/Exn"
        }

        self.spec.components.schema(
            "ExnEmbeds",
            schema=marshmallow_dataclass.class_schema(grouping.ExnEmbedsBase)(),
        )
        exnEmbedsSchema = self.spec.components.schemas["ExnEmbeds"]
        exnEmbedsSchema["oneOf"] = [
            {"$ref": "#/components/schemas/MultisigInceptEmbeds"},
            {"$ref": "#/components/schemas/MultisigRotateEmbeds"},
            {"$ref": "#/components/schemas/MultisigInteractEmbeds"},
            {"$ref": "#/components/schemas/MultisigRegistryInceptEmbeds"},
            {"$ref": "#/components/schemas/MultisigIssueEmbeds"},
            {"$ref": "#/components/schemas/MultisigRevokeEmbeds"},
            {"$ref": "#/components/schemas/MultisigRpyEmbeds"},
            {"$ref": "#/components/schemas/MultisigExnEmbeds"},
        ]
        self.spec.components.schema(
            "ExnMultisig",
            schema=marshmallow_dataclass.class_schema(grouping.ExnMultisig)(),
        )
        exnMSchema = self.spec.components.schemas["ExnMultisig"]
        exnMSchema["properties"]["exn"] = {"$ref": "#/components/schemas/Exn"}

        # Register the OOBI operation schemas
        self.spec.components.schema(
            "PendingOOBIOperation",
            schema=marshmallow_dataclass.class_schema(optypes.PendingOOBIOperation)(),
        )
        self.spec.components.schema(
            "CompletedOOBIOperation",
            schema=marshmallow_dataclass.class_schema(optypes.CompletedOOBIOperation)(),
        )
        self.spec.components.schema(
            "FailedOOBIOperation",
            schema=marshmallow_dataclass.class_schema(optypes.FailedOOBIOperation)(),
        )
        self.spec.components.schemas["OOBIOperation"] = {
            "oneOf": [
                {"$ref": "#/components/schemas/PendingOOBIOperation"},
                {"$ref": "#/components/schemas/CompletedOOBIOperation"},
                {"$ref": "#/components/schemas/FailedOOBIOperation"},
            ]
        }

        # Register the Query operation schemas
        self.spec.components.schema(
            "PendingQueryOperation",
            schema=marshmallow_dataclass.class_schema(optypes.PendingQueryOperation)(),
        )
        self.spec.components.schema(
            "CompletedQueryOperation",
            schema=marshmallow_dataclass.class_schema(
                optypes.CompletedQueryOperation
            )(),
        )
        self.spec.components.schema(
            "FailedQueryOperation",
            schema=marshmallow_dataclass.class_schema(optypes.FailedQueryOperation)(),
        )
        self.spec.components.schemas["QueryOperation"] = {
            "oneOf": [
                {"$ref": "#/components/schemas/PendingQueryOperation"},
                {"$ref": "#/components/schemas/CompletedQueryOperation"},
                {"$ref": "#/components/schemas/FailedQueryOperation"},
            ]
        }

        # Register the EndRole operation schemas
        self.spec.components.schema(
            "PendingEndRoleOperation",
            schema=marshmallow_dataclass.class_schema(
                optypes.PendingEndRoleOperation
            )(),
        )
        self.spec.components.schema(
            "CompletedEndRoleOperation",
            schema=marshmallow_dataclass.class_schema(
                optypes.CompletedEndRoleOperation
            )(),
        )
        self.spec.components.schema(
            "FailedEndRoleOperation",
            schema=marshmallow_dataclass.class_schema(optypes.FailedEndRoleOperation)(),
        )
        self.spec.components.schemas["CompletedEndRoleOperation"]["properties"][
            "response"
        ] = {
            "oneOf": [
                {"$ref": "#/components/schemas/RPY_V_1"},
                {"$ref": "#/components/schemas/RPY_V_2"},
            ]
        }
        self.spec.components.schemas["EndRoleOperation"] = {
            "oneOf": [
                {"$ref": "#/components/schemas/PendingEndRoleOperation"},
                {"$ref": "#/components/schemas/CompletedEndRoleOperation"},
                {"$ref": "#/components/schemas/FailedEndRoleOperation"},
            ]
        }

        # Register the Witness operation schemas
        self.spec.components.schema(
            "PendingWitnessOperation",
            schema=marshmallow_dataclass.class_schema(
                optypes.PendingWitnessOperation
            )(),
        )
        self.spec.components.schema(
            "CompletedWitnessOperation",
            schema=marshmallow_dataclass.class_schema(
                optypes.CompletedWitnessOperation
            )(),
        )
        self.spec.components.schema(
            "FailedWitnessOperation",
            schema=marshmallow_dataclass.class_schema(optypes.FailedWitnessOperation)(),
        )
        self.spec.components.schemas["CompletedWitnessOperation"]["properties"][
            "response"
        ] = {
            "oneOf": [
                {"$ref": "#/components/schemas/ICP_V_1"},
                {"$ref": "#/components/schemas/ICP_V_2"},
                {"$ref": "#/components/schemas/ROT_V_1"},
                {"$ref": "#/components/schemas/ROT_V_2"},
                {"$ref": "#/components/schemas/IXN_V_1"},
                {"$ref": "#/components/schemas/IXN_V_2"},
            ]
        }
        self.spec.components.schemas["WitnessOperation"] = {
            "oneOf": [
                {"$ref": "#/components/schemas/PendingWitnessOperation"},
                {"$ref": "#/components/schemas/CompletedWitnessOperation"},
                {"$ref": "#/components/schemas/FailedWitnessOperation"},
            ]
        }

        # Register the Delegation operation schemas
        self.spec.components.schema(
            "PendingDelegationOperation",
            schema=marshmallow_dataclass.class_schema(
                optypes.PendingDelegationOperation
            )(),
        )
        self.spec.components.schema(
            "CompletedDelegationOperation",
            schema=marshmallow_dataclass.class_schema(
                optypes.CompletedDelegationOperation
            )(),
        )
        self.spec.components.schema(
            "FailedDelegationOperation",
            schema=marshmallow_dataclass.class_schema(
                optypes.FailedDelegationOperation
            )(),
        )
        self.spec.components.schemas["CompletedDelegationOperation"]["properties"][
            "response"
        ] = {
            "oneOf": [
                {"$ref": "#/components/schemas/DIP_V_1"},
                {"$ref": "#/components/schemas/DIP_V_2"},
                {"$ref": "#/components/schemas/DRT_V_1"},
                {"$ref": "#/components/schemas/DRT_V_2"},
            ]
        }
        self.spec.components.schemas["DelegationOperation"] = {
            "oneOf": [
                {"$ref": "#/components/schemas/PendingDelegationOperation"},
                {"$ref": "#/components/schemas/CompletedDelegationOperation"},
                {"$ref": "#/components/schemas/FailedDelegationOperation"},
            ]
        }

        # Registry operation schemas
        self.spec.components.schema(
            "PendingRegistryOperation",
            schema=marshmallow_dataclass.class_schema(
                optypes.PendingRegistryOperation
            )(),
        )
        self.spec.components.schema(
            "CompletedRegistryOperation",
            schema=marshmallow_dataclass.class_schema(
                optypes.CompletedRegistryOperation
            )(),
        )
        self.spec.components.schema(
            "FailedRegistryOperation",
            schema=marshmallow_dataclass.class_schema(
                optypes.FailedRegistryOperation
            )(),
        )
        self.spec.components.schemas["RegistryOperation"] = {
            "oneOf": [
                {"$ref": "#/components/schemas/PendingRegistryOperation"},
                {"$ref": "#/components/schemas/CompletedRegistryOperation"},
                {"$ref": "#/components/schemas/FailedRegistryOperation"},
            ]
        }

        # LocScheme operation schemas
        self.spec.components.schema(
            "PendingLocSchemeOperation",
            schema=marshmallow_dataclass.class_schema(
                optypes.PendingLocSchemeOperation
            )(),
        )
        self.spec.components.schema(
            "CompletedLocSchemeOperation",
            schema=marshmallow_dataclass.class_schema(
                optypes.CompletedLocSchemeOperation
            )(),
        )
        self.spec.components.schema(
            "FailedLocSchemeOperation",
            schema=marshmallow_dataclass.class_schema(
                optypes.FailedLocSchemeOperation
            )(),
        )
        self.spec.components.schemas["LocSchemeOperation"] = {
            "oneOf": [
                {"$ref": "#/components/schemas/PendingLocSchemeOperation"},
                {"$ref": "#/components/schemas/CompletedLocSchemeOperation"},
                {"$ref": "#/components/schemas/FailedLocSchemeOperation"},
            ]
        }

        # Challenge operation schemas
        self.spec.components.schema(
            "PendingChallengeOperation",
            schema=marshmallow_dataclass.class_schema(
                optypes.PendingChallengeOperation
            )(),
        )
        self.spec.components.schema(
            "CompletedChallengeOperation",
            schema=marshmallow_dataclass.class_schema(
                optypes.CompletedChallengeOperation
            )(),
        )
        self.spec.components.schema(
            "FailedChallengeOperation",
            schema=marshmallow_dataclass.class_schema(
                optypes.FailedChallengeOperation
            )(),
        )
        self.spec.components.schemas["ChallengeOperationResponse"]["properties"][
            "exn"
        ] = {
            "oneOf": [
                {"$ref": "#/components/schemas/EXN_V_1"},
                {"$ref": "#/components/schemas/EXN_V_2"},
            ]
        }
        self.spec.components.schemas["ChallengeOperation"] = {
            "oneOf": [
                {"$ref": "#/components/schemas/PendingChallengeOperation"},
                {"$ref": "#/components/schemas/CompletedChallengeOperation"},
                {"$ref": "#/components/schemas/FailedChallengeOperation"},
            ]
        }

        # Exchange operation schemas
        self.spec.components.schema(
            "PendingExchangeOperation",
            schema=marshmallow_dataclass.class_schema(
                optypes.PendingExchangeOperation
            )(),
        )
        self.spec.components.schema(
            "CompletedExchangeOperation",
            schema=marshmallow_dataclass.class_schema(
                optypes.CompletedExchangeOperation
            )(),
        )
        self.spec.components.schema(
            "FailedExchangeOperation",
            schema=marshmallow_dataclass.class_schema(
                optypes.FailedExchangeOperation
            )(),
        )
        self.spec.components.schemas["ExchangeOperation"] = {
            "oneOf": [
                {"$ref": "#/components/schemas/PendingExchangeOperation"},
                {"$ref": "#/components/schemas/CompletedExchangeOperation"},
                {"$ref": "#/components/schemas/FailedExchangeOperation"},
            ]
        }

        # Submit operation schemas
        self.spec.components.schema(
            "PendingSubmitOperation",
            schema=marshmallow_dataclass.class_schema(optypes.PendingSubmitOperation)(),
        )
        self.spec.components.schema(
            "CompletedSubmitOperation",
            schema=marshmallow_dataclass.class_schema(
                optypes.CompletedSubmitOperation
            )(),
        )
        self.spec.components.schema(
            "FailedSubmitOperation",
            schema=marshmallow_dataclass.class_schema(optypes.FailedSubmitOperation)(),
        )
        self.spec.components.schemas["SubmitOperation"] = {
            "oneOf": [
                {"$ref": "#/components/schemas/PendingSubmitOperation"},
                {"$ref": "#/components/schemas/CompletedSubmitOperation"},
                {"$ref": "#/components/schemas/FailedSubmitOperation"},
            ]
        }

        # Done operation schemas
        self.spec.components.schema(
            "DoneOperationMetadata",
            schema=marshmallow_dataclass.class_schema(optypes.DoneOperationMetadata)(),
        )
        self.spec.components.schemas["DoneOperationMetadata"]["properties"][
            "response"
        ] = {
            "oneOf": [
                {"$ref": "#/components/schemas/ICP_V_1"},
                {"$ref": "#/components/schemas/ICP_V_2"},
                {"$ref": "#/components/schemas/ROT_V_1"},
                {"$ref": "#/components/schemas/ROT_V_2"},
                {"$ref": "#/components/schemas/EXN_V_1"},
                {"$ref": "#/components/schemas/EXN_V_2"},
            ]
        }
        self.spec.components.schema(
            "PendingDoneOperation",
            schema=marshmallow_dataclass.class_schema(optypes.PendingDoneOperation)(),
        )
        self.spec.components.schema(
            "CompletedDoneOperation",
            schema=marshmallow_dataclass.class_schema(optypes.CompletedDoneOperation)(),
        )
        self.spec.components.schema(
            "FailedDoneOperation",
            schema=marshmallow_dataclass.class_schema(optypes.FailedDoneOperation)(),
        )
        self.spec.components.schemas["CompletedDoneOperation"]["properties"][
            "response"
        ] = {
            "oneOf": [
                {"$ref": "#/components/schemas/ICP_V_1"},
                {"$ref": "#/components/schemas/ICP_V_2"},
                {"$ref": "#/components/schemas/ROT_V_1"},
                {"$ref": "#/components/schemas/ROT_V_2"},
                {"$ref": "#/components/schemas/EXN_V_1"},
                {"$ref": "#/components/schemas/EXN_V_2"},
            ]
        }
        self.spec.components.schemas["DoneOperation"] = {
            "oneOf": [
                {"$ref": "#/components/schemas/PendingDoneOperation"},
                {"$ref": "#/components/schemas/CompletedDoneOperation"},
                {"$ref": "#/components/schemas/FailedDoneOperation"},
            ]
        }

        # Credential operation schemas
        self.spec.components.schema(
            "CredentialOperationMetadata",
            schema=marshmallow_dataclass.class_schema(
                optypes.CredentialOperationMetadata
            )(),
        )
        self.spec.components.schemas["CredentialOperationMetadata"]["properties"][
            "ced"
        ] = {
            "oneOf": [
                {"$ref": "#/components/schemas/ACDC_V_1"},
                {"$ref": "#/components/schemas/ACDC_V_2"},
            ]
        }
        self.spec.components.schemas["CredentialOperationMetadata"]["properties"][
            "depends"
        ] = {
            "oneOf": [
                {"$ref": "#/components/schemas/ROT_V_1"},
                {"$ref": "#/components/schemas/ROT_V_2"},
                {"$ref": "#/components/schemas/DRT_V_1"},
                {"$ref": "#/components/schemas/DRT_V_2"},
                {"$ref": "#/components/schemas/IXN_V_1"},
                {"$ref": "#/components/schemas/IXN_V_2"},
            ]
        }
        self.spec.components.schema(
            "CredentialOperationResponse",
            schema=marshmallow_dataclass.class_schema(
                optypes.CredentialOperationResponse
            )(),
        )
        self.spec.components.schemas["CredentialOperationResponse"]["properties"][
            "ced"
        ] = {
            "oneOf": [
                {"$ref": "#/components/schemas/ACDC_V_1"},
                {"$ref": "#/components/schemas/ACDC_V_2"},
            ]
        }
        self.spec.components.schema(
            "PendingCredentialOperation",
            schema=marshmallow_dataclass.class_schema(
                optypes.PendingCredentialOperation
            )(),
        )
        self.spec.components.schema(
            "CompletedCredentialOperation",
            schema=marshmallow_dataclass.class_schema(
                optypes.CompletedCredentialOperation
            )(),
        )
        self.spec.components.schema(
            "FailedCredentialOperation",
            schema=marshmallow_dataclass.class_schema(
                optypes.FailedCredentialOperation
            )(),
        )
        self.spec.components.schemas["CredentialOperation"] = {
            "oneOf": [
                {"$ref": "#/components/schemas/PendingCredentialOperation"},
                {"$ref": "#/components/schemas/CompletedCredentialOperation"},
                {"$ref": "#/components/schemas/FailedCredentialOperation"},
            ]
        }

        # Group operation schemas
        self.spec.components.schema(
            "PendingGroupOperation",
            schema=marshmallow_dataclass.class_schema(optypes.PendingGroupOperation)(),
        )
        self.spec.components.schema(
            "CompletedGroupOperation",
            schema=marshmallow_dataclass.class_schema(
                optypes.CompletedGroupOperation
            )(),
        )
        self.spec.components.schema(
            "FailedGroupOperation",
            schema=marshmallow_dataclass.class_schema(optypes.FailedGroupOperation)(),
        )
        self.spec.components.schemas["CompletedGroupOperation"]["properties"][
            "response"
        ] = ancEvent
        self.spec.components.schemas["GroupOperation"] = {
            "oneOf": [
                {"$ref": "#/components/schemas/PendingGroupOperation"},
                {"$ref": "#/components/schemas/CompletedGroupOperation"},
                {"$ref": "#/components/schemas/FailedGroupOperation"},
            ]
        }

        # Delegator operation schemas
        self.spec.components.schema(
            "DelegatorOperationMetadata",
            schema=marshmallow_dataclass.class_schema(
                optypes.DelegatorOperationMetadata
            )(),
        )
        self.spec.components.schemas["DelegatorOperationMetadata"]["properties"][
            "depends"
        ] = {
            "oneOf": [
                {"$ref": "#/components/schemas/GroupOperation"},
                {"$ref": "#/components/schemas/WitnessOperation"},
                {"$ref": "#/components/schemas/DoneOperation"},
            ]
        }

        self.spec.components.schema(
            "PendingDelegatorOperation",
            schema=marshmallow_dataclass.class_schema(
                optypes.PendingDelegatorOperation
            )(),
        )
        self.spec.components.schema(
            "CompletedDelegatorOperation",
            schema=marshmallow_dataclass.class_schema(
                optypes.CompletedDelegatorOperation
            )(),
        )
        self.spec.components.schema(
            "FailedDelegatorOperation",
            schema=marshmallow_dataclass.class_schema(
                optypes.FailedDelegatorOperation
            )(),
        )
        self.spec.components.schemas["DelegatorOperation"] = {
            "oneOf": [
                {"$ref": "#/components/schemas/PendingDelegatorOperation"},
                {"$ref": "#/components/schemas/CompletedDelegatorOperation"},
                {"$ref": "#/components/schemas/FailedDelegatorOperation"},
            ]
        }

        self.spec.components.schemas["Operation"] = {
            "oneOf": [
                {"$ref": "#/components/schemas/OOBIOperation"},
                {"$ref": "#/components/schemas/QueryOperation"},
                {"$ref": "#/components/schemas/EndRoleOperation"},
                {"$ref": "#/components/schemas/WitnessOperation"},
                {"$ref": "#/components/schemas/DelegationOperation"},
                {"$ref": "#/components/schemas/RegistryOperation"},
                {"$ref": "#/components/schemas/LocSchemeOperation"},
                {"$ref": "#/components/schemas/ChallengeOperation"},
                {"$ref": "#/components/schemas/ExchangeOperation"},
                {"$ref": "#/components/schemas/SubmitOperation"},
                {"$ref": "#/components/schemas/DoneOperation"},
                {"$ref": "#/components/schemas/CredentialOperation"},
                {"$ref": "#/components/schemas/GroupOperation"},
                {"$ref": "#/components/schemas/DelegatorOperation"},
            ]
        }

        self.addRoutes(app)

    def addRoutes(self, app):
        valid_methods = self._get_valid_methods(self.spec)
        routes_to_check = copy.copy(app._router._roots)

        for route in routes_to_check:
            if route.resource is not None:
                operations = dict()
                operations.update(
                    yaml_utils.load_operations_from_docstring(route.resource.__doc__)
                    or {}
                )

                if route.method_map:
                    for method_name, method_handler in route.method_map.items():
                        if method_handler.__module__ == "falcon.responders":
                            continue
                        if method_name.lower() not in valid_methods:
                            continue
                        docstring_yaml = yaml_utils.load_yaml_from_docstring(
                            method_handler.__doc__
                        )
                        operations[method_name.lower()] = docstring_yaml or dict()

                self.spec.path(path=route.uri_template, operations=operations)
            routes_to_check.extend(route.children)

    def _get_valid_methods(self, spec):
        return set(VALID_METHODS[spec.openapi_version.major])

    def on_get(self, _, rep):
        """
        GET endpoint for OpenAPI 3.1.0 spec

        Args:
            _: falcon.Request HTTP request
            rep: falcon.Response HTTP response


        """
        rep.status = falcon.HTTP_200
        rep.content_type = "application/yaml"
        rep.data = self._get_spec_yaml()

    def _get_spec_yaml(self):
        return self.spec.to_yaml().encode("utf-8")
