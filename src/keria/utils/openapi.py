from enum import Enum
from typing import Any, Dict, List
from dataclasses import field, make_dataclass
from marshmallow_dataclass import class_schema
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

    for key, value in field_dom.alls.items():
        py_type = inferType(value, key)

        # Default value
        if isinstance(value, list):
            default = field(default_factory=list)
        elif isinstance(value, dict):
            default = field(default_factory=dict)
        else:
            default = value

        fields.append((key, py_type, default))

    # Create the dataclass dynamically
    generated_cls = make_dataclass(name, fields)

    return generated_cls, class_schema(generated_cls)

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
