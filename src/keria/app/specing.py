import copy
from typing import Any, Dict, List, Optional
import yaml
from dataclasses import dataclass, field
import falcon
from apispec import yaml_utils
from apispec.core import VALID_METHODS, APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from marshmallow import Schema, fields
from keria.app import aiding

from marshmallow import fields, Schema

from dataclasses import dataclass
from ..core import longrunning

import marshmallow_dataclass
from marshmallow_oneofschema import OneOfSchema

"""
KERIA
keria.app.specing module

OpenAPI Description Resource for the KERI and ACDC ReST interface
"""

# Marshmallow schema for IdentifierCollectionEnd GET response (list of identifiers)
class IdentifierSchema(Schema):
    name = fields.Str(required=True, description="The name of the identifier")
    prefix = fields.Str(required=True, description="The identifier prefix")
    # Add other fields as needed to match your info(hab, agent.mgr) output

# Marshmallow schema for IdentifierCollectionEnd POST request
class IdentifierCreateRequestSchema(Schema):
    icp = fields.Dict(required=True, description="The inception event for the identifier.")
    name = fields.Str(required=True, description="The name of the identifier.")
    sigs = fields.List(fields.Str(), required=True, description="The signatures for the inception event.")
    group = fields.Dict(description="Multisig group information.")
    salty = fields.Dict(description="Salty parameters.")
    randy = fields.Dict(description="Randomly generated materials.")
    extern = fields.Dict(description="External parameters.")

@dataclass
class HabGroupInfo:
    mhab: Optional['HabInfo'] = None  # Recursive type for nested group info

@dataclass
class HabInfo:
    name: str
    prefix: str
    # The following fields are dynamically added, so we use Optional/Any
    group: Optional[HabGroupInfo] = None
    icp_dt: Optional[str] = None
    transferable: Optional[bool] = None
    state: Optional[Dict[str, Any]] = None
    windexes: Optional[List[int]] = None
    # Add any other keeper.params fields as needed
    # For a generic catch-all for keeper.params:
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Move any unknown fields into extra
        known = {'name', 'prefix', 'group', 'icp_dt', 'transferable', 'state', 'windexes'}
        for k in list(self.__dict__):
            if k not in known and not k.startswith('_'):
                self.extra[k] = self.__dict__.pop(k)

@dataclass
class Op:
    oid: str
    type: str
    start: str
    metadata: dict

# Marshmallow schema for Operation error field
class OperationStatusSchema(Schema):
    code = fields.Int(required=True, description="HTTP status code or error code")
    message = fields.Str(required=True, description="Error or status message")
    

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
        # Register schemas with generated examples
        self.spec.components.schema(
            "Identifier", 
            schema=IdentifierSchema
        )
        self.spec.components.schema(
            "IdentifierCreateRequest", 
            schema=IdentifierCreateRequestSchema
        )

        # Register schemas with apispec (instantiate here)
        self.spec.components.schema("OpResponseKel", schema=OpResponseKelSchema())
        self.spec.components.schema("IdentifierCreateResponse", schema=OperationSchema)
        self.spec.components.schema(
            "OpStatus", 
            schema=OperationStatusSchema
        )
        self.addRoutes(app)

    def addRoutes(self, app):
        valid_methods = self._get_valid_methods(self.spec)
        routes_to_check = copy.copy(app._router._roots)

        for route in routes_to_check:
            if route.resource is not None:
                if not isinstance(route.resource, aiding.IdentifierCollectionEnd):
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
        spec_dict = self.spec.to_dict()
        spec_dict['components']['schemas']['ResponseUnion'] = {
            'oneOf': [
                {'$ref': '#/components/schemas/OpResponseKel'},
                {'type': 'object'},
                {'type': 'null'}  # Allow None as a valid response
            ]
        }
        return yaml.dump(spec_dict).encode("utf-8")

OpResponseKelSchema = marshmallow_dataclass.class_schema(longrunning.OpResponseKel)

class ResponseUnionSchema(OneOfSchema):
    type_schemas = {
        "OpResponseKel": OpResponseKelSchema
    }

class OperationSchema(Schema):
    name = fields.Str(required=True)
    metadata = fields.Nested(marshmallow_dataclass.class_schema(longrunning.OpMetadata)())
    done = fields.Bool(missing=False)
    response = fields.Nested(ResponseUnionSchema, allow_none=True)
