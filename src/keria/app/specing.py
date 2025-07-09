import copy
import falcon
import marshmallow_dataclass
from apispec import yaml_utils
from apispec.core import VALID_METHODS, APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from ..core import longrunning, apitype
from keria.app import aiding, credentialing
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
        self.spec.components.schema("SADSchema", schema=marshmallow_dataclass.class_schema(apitype.SAD)())

        self.spec.components.schema("SADAttributesSchema", schema=marshmallow_dataclass.class_schema(apitype.SADAttributes)())

        self.spec.components.schema("ISSSchema", schema=marshmallow_dataclass.class_schema(apitype.ISS)())

        self.spec.components.schema("SchemaSchema", schema=marshmallow_dataclass.class_schema(apitype.Schema)())

        self.spec.components.schema("StatusAnchorSchema", schema=marshmallow_dataclass.class_schema(apitype.StatusAnchor)())

        self.spec.components.schema("CredentialStatusSchema", schema=marshmallow_dataclass.class_schema(apitype.Status)())

        self.spec.components.schema("AnchorSchema", schema=marshmallow_dataclass.class_schema(apitype.Anchor)())

        self.spec.components.schema("SealSchema", schema=marshmallow_dataclass.class_schema(apitype.Seal)())

        self.spec.components.schema("ANCSchema", schema=marshmallow_dataclass.class_schema(apitype.ANC)())

        self.spec.components.schema("CredentialSchema", schema=marshmallow_dataclass.class_schema(apitype.Credential)())

        # self.spec.components.schema("StatusSchema", schema=marshmallow_dataclass.class_schema(longrunning.Status)())
        self.spec.components.schema("OperationBaseSchema", schema=marshmallow_dataclass.class_schema(longrunning.OperationBase)())
        self.spec.components.schema("StatusSchema", schema=marshmallow_dataclass.class_schema(longrunning.Status)())
        self.spec.components.schema("OperationBase", schema=marshmallow_dataclass.class_schema(longrunning.OperationBase)())

        self.spec.components.schema("CredentialStateIssOrRevSchema", schema=marshmallow_dataclass.class_schema(apitype.CredentialStateIssOrRev))
        self.spec.components.schema("CredentialStateBisOrBrvSchema", schema=marshmallow_dataclass.class_schema(apitype.CredentialStateBisOrBrv))

        cred_schema = self.spec.components.schemas["CredentialSchema"]
        cred_schema["properties"]["status"] = {
            "oneOf": [
                {"$ref": "#/components/schemas/CredentialStateIssOrRevSchema"},
                {"$ref": "#/components/schemas/CredentialStateBisOrBrvSchema"},
            ]
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

        self.addRoutes(app)

    def addRoutes(self, app):
        valid_methods = self._get_valid_methods(self.spec)
        routes_to_check = copy.copy(app._router._roots)

        for route in routes_to_check:
            if route.resource is not None:
                if not isinstance(route.resource, aiding.IdentifierCollectionEnd) and not isinstance(route.resource, credentialing.CredentialCollectionEnd):
                    continue
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
