from enum import Enum
from typing import Any, Dict, List, Union
from dataclasses import field, make_dataclass
from marshmallow_dataclass import class_schema
from marshmallow import fields as mm_fields
from keri.core import serdering


def inferType(value: Any, key: str = ""):
    if key == "a":
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
        # Try to infer item type from first item if available
        if len(value) > 0:
            item_type = inferType(value[0], key)
        else:
            item_type = str  # Default to str instead of Any
        return List[item_type]
    elif isinstance(value, dict):
        return Dict[str, Any]
    else:
        return Any

def dataclassFromFielddom(name: str, field_dom: serdering.FieldDom) -> (type, class_schema):
    """
    Dynamically create a dataclass from a FieldDom instance.
    """
    fields = []
    custom_fields = {}

    for key, value in field_dom.alls.items():
        # Custom: for "kt" or "nt", allow string or array of strings or array of array of strings
        if key in ("kt", "nt"):
            py_type = Union[str, List[str], List[List[str]]]
            marshmallow_field = mm_fields.Raw(
                required=True,
                metadata={
                    "oneOf": [
                        {"type": "string"},
                        {"type": "array", "items": {"type": "string"}},
                        {"type": "array", "items": {"type": "array", "items": {"type": "string"}}}
                    ]
                }
            )
            field_def = (key, py_type, field(metadata={"marshmallow_field": marshmallow_field}))
            custom_fields[key] = marshmallow_field
        else:
            py_type = inferType(value, key)
            field_def = (key, py_type)

        fields.append(field_def)

    generated_cls = make_dataclass(name, fields)
    schema = class_schema(generated_cls)()

    # Apply custom marshmallow fields for kt/nt
    for key in ("kt", "nt"):
        if key in custom_fields:
            schema._declared_fields[key] = custom_fields[key]

    return generated_cls, schema

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
