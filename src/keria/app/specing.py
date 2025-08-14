import copy
import falcon
import marshmallow_dataclass
from apispec import yaml_utils
from apispec.core import VALID_METHODS, APISpec
from apispec.ext.marshmallow import MarshmallowPlugin

from keria.app import aiding, agenting
from ..core import longrunning
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
            "Seal", schema=marshmallow_dataclass.class_schema(credentialing.Seal)()
        )
        self.spec.components.schema(
            "IXN_V_1",
            schema=marshmallow_dataclass.class_schema(credentialing.IXN_V_1)(),
        )
        self.spec.components.schema(
            "IXN_V_2",
            schema=marshmallow_dataclass.class_schema(credentialing.IXN_V_2)(),
        )
        self.spec.components.schema(
            "ICP_V_1",
            schema=marshmallow_dataclass.class_schema(credentialing.ICP_V_1)(),
        )
        self.spec.components.schema(
            "ICP_V_2",
            schema=marshmallow_dataclass.class_schema(credentialing.ICP_V_2)(),
        )
        self.spec.components.schema(
            "ROT_V_1",
            schema=marshmallow_dataclass.class_schema(credentialing.ROT_V_1)(),
        )
        self.spec.components.schema(
            "ROT_V_2",
            schema=marshmallow_dataclass.class_schema(credentialing.ROT_V_2)(),
        )
        self.spec.components.schema(
            "DIP_V_1",
            schema=marshmallow_dataclass.class_schema(credentialing.DIP_V_1)(),
        )
        self.spec.components.schema(
            "DIP_V_2",
            schema=marshmallow_dataclass.class_schema(credentialing.DIP_V_2)(),
        )
        self.spec.components.schema(
            "DRT_V_1",
            schema=marshmallow_dataclass.class_schema(credentialing.DRT_V_1)(),
        )
        self.spec.components.schema(
            "DRT_V_2",
            schema=marshmallow_dataclass.class_schema(credentialing.DRT_V_2)(),
        )
        self.spec.components.schema(
            "RPY_V_1", schema=marshmallow_dataclass.class_schema(aiding.RPY_V_1)()
        )
        self.spec.components.schema(
            "RPY_V_2", schema=marshmallow_dataclass.class_schema(aiding.RPY_V_2)()
        )
        self.spec.components.schema(
            "Credential",
            schema=marshmallow_dataclass.class_schema(credentialing.ClonedCredential)(),
        )
        self.spec.components.schema(
            "Operation",
            schema=marshmallow_dataclass.class_schema(longrunning.Operation)(),
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
        credentialSchema["properties"]["anc"] = {
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

        # Operation
        operationSchema = self.spec.components.schemas["Operation"]
        operationSchema["properties"]["metadata"] = {"type": "object"}
        operationSchema["properties"]["response"] = {"type": "object"}

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

        # Identifiers
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
        self.spec.components.schema(
            "Identifier", schema=marshmallow_dataclass.class_schema(aiding.HabState)()
        )
        identifierSchema = self.spec.components.schemas["Identifier"]
        identifierSchema["oneOf"] = [
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
        self.spec.components.schemas["GroupKeyState"]["properties"]["mhab"] = {
            "$ref": "#/components/schemas/Identifier"
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

        self.spec.components.schemas["Rpy"] = {
            "oneOf": [
                {"$ref": "#/components/schemas/RPY_V_1"},
                {"$ref": "#/components/schemas/RPY_V_2"},
            ]
        }

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
        self.spec.components.schema("KeyEventRecord", schema=marshmallow_dataclass.class_schema(agenting.KeyEventRecord)())
        keyEventRecordSchema = self.spec.components.schemas["KeyEventRecord"]
        keyEventRecordSchema["properties"]["ked"] = {
            "oneOf": [
                # Keri V1.0
                {"$ref": "#/components/schemas/IcpV1"},
                {"$ref": "#/components/schemas/RotV1"},
                {"$ref": "#/components/schemas/IxnV1"},
                {"$ref": "#/components/schemas/DipV1"},
                {"$ref": "#/components/schemas/DrtV1"},
                {"$ref": "#/components/schemas/RctV1"},
                {"$ref": "#/components/schemas/QryV1"},
                {"$ref": "#/components/schemas/RpyV1"},
                {"$ref": "#/components/schemas/ProV1"},
                {"$ref": "#/components/schemas/BarV1"},
                {"$ref": "#/components/schemas/ExnV1"},
                {"$ref": "#/components/schemas/VcpV1"},
                {"$ref": "#/components/schemas/VrtV1"},
                {"$ref": "#/components/schemas/IssV1"},
                {"$ref": "#/components/schemas/RevV1"},
                {"$ref": "#/components/schemas/BisV1"},
                {"$ref": "#/components/schemas/BrvV1"},
                # Keri V2.0
                {"$ref": "#/components/schemas/IcpV2"},
                {"$ref": "#/components/schemas/RotV2"},
                {"$ref": "#/components/schemas/IxnV2"},
                {"$ref": "#/components/schemas/DipV2"},
                {"$ref": "#/components/schemas/DrtV2"},
                {"$ref": "#/components/schemas/RctV2"},
                {"$ref": "#/components/schemas/QryV2"},
                {"$ref": "#/components/schemas/RpyV2"},
                {"$ref": "#/components/schemas/ProV2"},
                {"$ref": "#/components/schemas/BarV2"},
                {"$ref": "#/components/schemas/XipV2"},
                {"$ref": "#/components/schemas/ExnV2"}
            ]
        }

        # Register the AgentConfig schema
        self.spec.components.schema("AgentConfig", schema=marshmallow_dataclass.class_schema(agenting.AgentConfig)())

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
