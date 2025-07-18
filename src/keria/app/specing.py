import copy
import falcon
import marshmallow_dataclass
from apispec import yaml_utils
from apispec.core import VALID_METHODS, APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from ..core import longrunning
from . import credentialing
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

    def __init__(self, app, title, version='1.0.1', openapi_version="3.1.0"):
        self.spec = APISpec(
            title=title,
            version=version,
            openapi_version=openapi_version,
            plugins=[MarshmallowPlugin()],
        )

        # Register marshmallow schemas (pass class)
        self.spec.components.schema("ACDC", schema=marshmallow_dataclass.class_schema(credentialing.ACDC)())
        self.spec.components.schema("IssEvt", schema=marshmallow_dataclass.class_schema(credentialing.IssEvt)())
        self.spec.components.schema("Schema", schema=marshmallow_dataclass.class_schema(credentialing.Schema)())
        self.spec.components.schema("StatusAnchor", schema=marshmallow_dataclass.class_schema(credentialing.StatusAnchor)())
        self.spec.components.schema("CredentialStatus", schema=marshmallow_dataclass.class_schema(credentialing.Status)())
        self.spec.components.schema("Anchor", schema=marshmallow_dataclass.class_schema(credentialing.Anchor)())
        self.spec.components.schema("Seal", schema=marshmallow_dataclass.class_schema(credentialing.Seal)())
        self.spec.components.schema("ANC", schema=marshmallow_dataclass.class_schema(credentialing.ANC)())
        self.spec.components.schema("Credential", schema=marshmallow_dataclass.class_schema(credentialing.ClonedCredential)())
        self.spec.components.schema("OperationBase", schema=marshmallow_dataclass.class_schema(longrunning.OperationBase)())
        self.spec.components.schema("CredentialStateIssOrRev", schema=marshmallow_dataclass.class_schema(credentialing.CredentialStateIssOrRev))
        self.spec.components.schema("CredentialStateBisOrBrv", schema=marshmallow_dataclass.class_schema(credentialing.CredentialStateBisOrBrv))

        # Patch the schema to force additionalProperties=True
        acdcAttributesSchema = self.spec.components.schemas["ACDCAttributes"]
        acdcAttributesSchema["additionalProperties"] = True

        # CredentialState
        self.spec.components.schemas["CredentialState"] = {
            "oneOf": [
                {"$ref": "#/components/schemas/CredentialStateIssOrRev"},
                {"$ref": "#/components/schemas/CredentialStateBisOrBrv"},
            ]
        }

        credentialSchema = self.spec.components.schemas["Credential"]
        credentialSchema["properties"]["status"] = {
            "$ref": "#/components/schemas/CredentialState"
        }

        # Register manual schema using direct assignment (not component or schema)
        self.spec.components.schemas["Operation"] = {
            "allOf": [
                {"$ref": "#/components/schemas/OperationBase"},
                {
                    "type": "object",
                    "properties": {
                        "metadata": {"type": "object"},
                        "response": {"type": "object"},
                    },
                },
            ]
        }

        # Registries
        self.spec.components.schema("Registry", schema=marshmallow_dataclass.class_schema(credentialing.Registry)())
        registrySchema = self.spec.components.schemas["Registry"]
        registrySchema["properties"]["state"] = {
            "$ref": "#/components/schemas/CredentialState"
        }


        self.addRoutes(app)

    def addRoutes(self, app):
        valid_methods = self._get_valid_methods(self.spec)
        routes_to_check = copy.copy(app._router._roots)

        for route in routes_to_check:
            if route.resource is not None:
                operations = dict()
                operations.update(yaml_utils.load_operations_from_docstring(route.resource.__doc__) or {})

                if route.method_map:
                    for method_name, method_handler in route.method_map.items():
                        if method_handler.__module__ == "falcon.responders":
                            continue
                        if method_name.lower() not in valid_methods:
                            continue
                        docstring_yaml = yaml_utils.load_yaml_from_docstring(method_handler.__doc__)
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
