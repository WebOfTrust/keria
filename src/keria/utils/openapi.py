from typing import Any, Dict, List, Union, Optional
from enum import Enum
from dataclasses import field, make_dataclass
from marshmallow_dataclass import class_schema
from marshmallow import fields as mm_fields
from keri.core import serdering


class OneOfField(mm_fields.Field):
    """Generic field for oneOf schema types that generates proper OpenAPI oneOf schema."""
    
    def _serialize(self, value, attr, obj, **kwargs):
        return value
        
    def _deserialize(self, value, attr, data, **kwargs):
        return value
        
    def __init__(self, schema_options: List[Dict[str, Any]], **kwargs):
        """
        Initialize OneOfField with schema options.
        
        Args:
            schema_options: List of OpenAPI schema dictionaries for oneOf
            **kwargs: Additional marshmallow field kwargs
        """
        super().__init__(**kwargs)
        self.metadata['oneOf'] = schema_options


class StringOrStringArrayField(OneOfField):
    def __init__(self, **kwargs):
        super().__init__([
            {'type': 'string'},
            {'type': 'array', 'items': {'type': 'string'}}
        ], **kwargs)


class StringOrArrayOrArrayOfArraysField(OneOfField):
    def __init__(self, **kwargs):
        super().__init__([
            {'type': 'string'},
            {'type': 'array', 'items': {'type': 'string'}},
            {'type': 'array', 'items': {'type': 'array', 'items': {'type': 'string'}}}
        ], **kwargs)


class UnionField(mm_fields.Field):
    """Custom field for generic Union types that generates anyOf schema."""
    def _serialize(self, value, attr, obj, **kwargs):
        return value
        
    def _deserialize(self, value, attr, data, **kwargs):
        return value
        
    def __init__(self, union_type, **kwargs):
        super().__init__(**kwargs)
        self.metadata['anyOf'] = []
        for arg in union_type.__args__:
            if arg is str:
                self.metadata['anyOf'].append({'type': 'string'})
            elif hasattr(arg, '__origin__') and arg.__origin__ is list:
                if arg.__args__ and arg.__args__[0] is str:
                    self.metadata['anyOf'].append({'type': 'array', 'items': {'type': 'string'}})
                else:
                    self.metadata['anyOf'].append({'type': 'array'})


def inferType(value: Any, key: str = ""):
    """Infer the Python type from a value, with special handling for certain keys."""
    if key in ("a", "A"):
        return Any
    if isinstance(value, str):
        return str
    elif isinstance(value, int):
        return int
    elif isinstance(value, float):
        return float
    elif isinstance(value, bool):
        return bool
    elif isinstance(value, list):
        if len(value) > 0:
            item_type = inferType(value[0], key)
        else:
            item_type = str
        return List[item_type]
    elif isinstance(value, dict):
        return Dict[str, Any]
    else:
        return Any


def createDataclassNestedField(key: str, customType: type, isOptional: bool) -> tuple[tuple, mm_fields.Field]:
    """Create nested field for dataclass types.
    
    Handles regular dataclass types like ACDCAttributes, Seal, etc. by creating
    marshmallow Nested fields with proper class_schema() serialization.
    
    Args:
        key: Field name from the FieldDom
        customType: Dataclass type (must have __dataclass_fields__ attribute)
        isOptional: Whether the field should be optional in the schema
        
    Returns:
        Tuple of (field_definition_for_dataclass, marshmallow_field_for_schema)
    """
    nestedSchema = class_schema(customType)()
    return createOptionalField(key, customType, mm_fields.Nested, (nestedSchema,), {}, isOptional)


def createOptionalField(
    key: str,
    fieldType: type,
    marshmallowFieldClass: type,
    marshmallowFieldArgs: tuple = None,
    marshmallowFieldKwargs: dict = None,
    isOptional: bool = True
) -> tuple[tuple, mm_fields.Field]:
    """
    Create marshmallow field and fieldDef tuple with consistent optional/required handling.
    
    Args:
        key: Field name
        fieldType: Python type for the field
        marshmallowFieldClass: Marshmallow field class to instantiate
        marshmallowFieldArgs: Positional arguments for marshmallow field constructor
        marshmallowFieldKwargs: Additional kwargs for marshmallow field (beyond required/missing/default/allow_none)
        isOptional: Whether field should be optional
    
    Returns:
        Tuple of (fieldDef, marshmallowField) where fieldDef is tuple for dataclass field definition
    """
    if marshmallowFieldArgs is None:
        marshmallowFieldArgs = ()
    if marshmallowFieldKwargs is None:
        marshmallowFieldKwargs = {}
    
    if isOptional:
        marshmallowField = marshmallowFieldClass(
            *marshmallowFieldArgs,
            required=False,
            missing=mm_fields.missing_,
            default=mm_fields.missing_,
            allow_none=False,
            **marshmallowFieldKwargs
        )
        fieldDef = (key, Optional[fieldType], field(default=None))
    else:
        marshmallowField = marshmallowFieldClass(
            *marshmallowFieldArgs,
            required=True,
            missing=mm_fields.missing_,
            default=mm_fields.missing_,
            **marshmallowFieldKwargs
        )
        fieldDef = (key, fieldType, field())
    
    return fieldDef, marshmallowField


def createCustomNestedField(key: str, customType: type, isOptional: bool) -> tuple[tuple, mm_fields.Field]:
    """Create custom nested field for specified type.
    
    This function is essential for converting KERI protocol FieldDom specifications into proper
    marshmallow fields for OpenAPI schema generation.
    
    Args:
        key: Field name from the FieldDom
        customType: Type annotation (could be Union, List[DataClass], regular DataClass, etc.)
        isOptional: Whether the field should be optional in the schema
        
    Returns:
        Tuple of (field_definition_for_dataclass, marshmallow_field_for_schema)
    """
    # Check if this is a Union type (e.g., Union[str, List[str]])
    if hasattr(customType, '__origin__') and customType.__origin__ is Union:
        # Handle Union types - these create polymorphic fields in KERI protocol
        union_args = customType.__args__
        
        # Check for the specific pattern Union[str, List[str]] which is common in KERI
        # This generates a more specific oneOf schema instead of generic anyOf
        if len(union_args) == 2 and str in union_args:
            # Find if one of the union args is List[str]
            list_type = next((arg for arg in union_args if hasattr(arg, '__origin__') and arg.__origin__ is list), None)
            # Ensure it's List[str] specifically (single string type argument)
            # This matches the KERI pattern Union[str, List[str]] exactly
            if list_type and len(list_type.__args__) == 1 and list_type.__args__[0] is str:
                return createOptionalField(key, customType, StringOrStringArrayField, (), {}, isOptional)
        
        # For other Union types, fall back to Raw field with anyOf
        return createOptionalField(key, customType, UnionField, (customType,), {}, isOptional)
    
    # Check if this is a generic type like List[SomeClass], Dict[str, Any], etc.
    # __origin__ identifies the base generic type (list, dict, etc.)
    elif hasattr(customType, '__origin__'):
        if customType.__origin__ is list:
            # Handle List[SomeClass] types - common in KERI for repeated elements
            # __args__ contains the type parameters, e.g., List[Seal] has __args__ = (Seal,)
            if customType.__args__:
                inner_type = customType.__args__[0]
                # Check if the inner type is a dataclass (has __dataclass_fields__ attribute)
                # This ensures we can safely call class_schema() on it for nested serialization
                if hasattr(inner_type, '__dataclass_fields__'):
                    # Create a List field with nested schema
                    nestedField = mm_fields.Nested(class_schema(inner_type)())
                    return createOptionalField(key, customType, mm_fields.List, (nestedField,), {}, isOptional)
        
        # For other generic types, fall back to Raw field
        return createOptionalField(key, customType, mm_fields.Raw, (), {}, isOptional)
    
    # This validation prevents AttributeError: __mro__ when calling class_schema() on non-dataclass types
    elif hasattr(customType, '__dataclass_fields__'):
        return createDataclassNestedField(key, customType, isOptional)
    
    # For non-dataclass, non-generic types, use Raw field
    else:
        return createOptionalField(key, customType, mm_fields.Raw, (), {}, isOptional)


def createKtNtField(key: str, isOptional: bool) -> tuple[tuple, mm_fields.Field]:
    # Type can be string, List[str], or List[List[str]]
    pyType = Union[str, List[str], List[List[str]]]
    
    return createOptionalField(key, pyType, StringOrArrayOrArrayOfArraysField, (), {}, isOptional)


def createRegularField(key: str, value: Any, isOptional: bool = True) -> tuple[tuple, Optional[mm_fields.Field]]:
    """Create regular field without custom nested handling."""
    inferredType = inferType(value, key)
    
    marshmallowField = None
    if isOptional and key not in ("a", "A"):
        if inferredType is str or inferredType is Optional[str]:
            marshmallowField = mm_fields.String(
                required=False,
                missing=mm_fields.missing_,
                default=mm_fields.missing_,
                allow_none=False
            )
        else:
            marshmallowField = mm_fields.Field(
                required=False,
                missing=mm_fields.missing_,
                default=mm_fields.missing_,
                allow_none=False
            )
    
    if isOptional:
        fieldDef = (key, Optional[inferredType], field(default=None))
    else:
        fieldDef = (key, inferredType)
    
    return fieldDef, marshmallowField


def processField(key: str, value: Any, fieldDom: serdering.FieldDom, customTypes: Dict[str, type], name: str = "") -> tuple[tuple, Optional[mm_fields.Field]]:
    """Process a single field from the FieldDom."""
    isOptional = key in fieldDom.opts
    
    # Check if there's a custom type specified
    if key in customTypes:
        return createCustomNestedField(key, customTypes[key], isOptional)
    
    # Custom: for "kt" or "nt", allow string or array of strings or array of array of strings
    elif key in ("kt", "nt"):
        return createKtNtField(key, isOptional)
    
    else:
        return createRegularField(key, value, isOptional)


def dataclassFromFielddom(name: str, fieldDom: serdering.FieldDom, customTypes: Optional[Dict[str, type]] = None):
    """
    Generates a dataclass from a FieldDom instance with proper marshmallow schema.
    Args:
        name: Name for the generated dataclass
        fieldDom: FieldDom instance containing field definitions
        customTypes: Optional dict mapping field names to custom types
    
    Returns:
        Tuple of (generated_dataclass, marshmallow_schema)
    """
    if customTypes is None:
        customTypes = {}
        
    requiredFields = []
    optionalFields = []
    customFields = {}
    
    # Store alt constraints for use by schema generation
    altConstraints = getattr(fieldDom, 'alts', {})
    
    # Process all fields from alls (all possible fields)
    for key, value in fieldDom.alls.items():
        fieldDef, marshmallowField = processField(key, value, fieldDom, customTypes, name)
        
        if marshmallowField:
            customFields[key] = marshmallowField
        
        # Check if field is optional (in opts)
        isOptional = key in fieldDom.opts
        if isOptional:
            optionalFields.append(fieldDef)
        else:
            requiredFields.append(fieldDef)

    allFields = requiredFields + optionalFields
    generatedCls = make_dataclass(name, allFields)
    schema = class_schema(generatedCls)()

    # Override the automatically generated fields with our custom ones
    # marshmallow_dataclass automatically creates fields with allow_none=True for Optional[T]
    # We need to override them to have allow_none=False for openapi-typescript compatibility
    for key, marshmallowField in customFields.items():
        schema.fields[key] = marshmallowField
        schema._declared_fields[key] = marshmallowField

    # Store alt constraints for later use in OpenAPI generation
    schema._alt_constraints = altConstraints

    return generatedCls, schema


def applyAltConstraintsToOpenApiSchema(openApiSchemaDict: dict, altConstraints: Dict[str, str]):
    """
    Modify an OpenAPI schema to include oneOf constraints for alternate fields.
    
    This should be called after the schema is registered in the OpenAPI spec.
    
    Args:
        openApiSchemaDict: The OpenAPI schema dictionary to modify
        altConstraints: Dict mapping alternate fields (e.g., {'a': 'A', 'A': 'a'})
    """
    if not altConstraints or 'properties' not in openApiSchemaDict:
        return
    
    properties = openApiSchemaDict.get('properties', {})
    required = openApiSchemaDict.get('required', [])
    
    # Find alternate field pairs that exist in properties
    altGroups = {}
    processedAlts = set()
    
    for field1, field2 in altConstraints.items():
        if field1 in processedAlts or field2 in processedAlts:
            continue
        if field1 in properties and field2 in properties:
            groupKey = f"{field1}_{field2}"
            altGroups[groupKey] = [field1, field2]
            processedAlts.add(field1)
            processedAlts.add(field2)
    
    if not altGroups:
        return
    
    # Create oneOf schemas for alternate field combinations
    oneOfSchemas = []
    
    for _, altFields in altGroups.items():
        field1, field2 = altFields
        
        # Base properties (all except alternates)
        baseProps = {k: v for k, v in properties.items() if k not in altFields}
        baseRequired = [f for f in required if f not in altFields]
        
        # Schema with field1 only
        schemaWithField1 = {
            "type": "object",
            "properties": {**baseProps, field1: properties[field1]},
            "additionalProperties": openApiSchemaDict.get("additionalProperties", False)
        }
        if field1 in required or baseRequired:
            schemaWithField1["required"] = baseRequired + ([field1] if field1 in required else [])
        oneOfSchemas.append(schemaWithField1)
        
        # Schema with field2 only
        schemaWithField2 = {
            "type": "object", 
            "properties": {**baseProps, field2: properties[field2]},
            "additionalProperties": openApiSchemaDict.get("additionalProperties", False)
        }
        if field2 in required or baseRequired:
            schemaWithField2["required"] = baseRequired + ([field2] if field2 in required else [])
        oneOfSchemas.append(schemaWithField2)
    
    # Replace the schema with oneOf constraint
    if oneOfSchemas:
        openApiSchemaDict.clear()
        openApiSchemaDict["oneOf"] = oneOfSchemas

def enumSchemaFromNamedtuple(nt_instance, description=None):
    """
    Generate an OpenAPI schema dict for a namedtuple instance.
    """
    return {
        "type": "string",
        "enum": [v for v in nt_instance._asdict().values()],
        "description": description or nt_instance.__class__.__name__
    }

def namedtupleToEnum(nt_instance, enum_name="AutoEnum"):
    if not isinstance(nt_instance, tuple) or not hasattr(nt_instance, "_fields"):
        raise TypeError("Must pass a namedtuple instance")

    # Build dict of {field_name: value}
    members = {field: getattr(nt_instance, field) for field in nt_instance._fields}

    # Dynamically create a subclass of str & Enum
    return Enum(enum_name, members, type=str)
