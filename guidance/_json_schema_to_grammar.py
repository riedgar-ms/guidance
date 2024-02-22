import json
from typing import Dict, List, Union

import guidance
from .library._char_range import char_range
from .library import select, optional, zero_or_more, one_or_more

_SAFE_STRING = select(
    [
        char_range("a", "z"),
        char_range("A", "Z"),
        char_range("0", "9"),
        *[c for c in "-_' ,.!?/[]{}():;"],
        "\\n",
        "\\t",
        "\\\\",
    ],
    recurse=True,
)

@guidance(stateless=True)
def json_string(lm):
    return lm + '"' + _SAFE_STRING + '"'

@guidance(stateless=True)
def json_integer(lm):
    return lm + select(["-", ""]) + one_or_more(char_range("0", "9"))

@guidance(stateless=True)
def json_number(lm):
    mantissa_int = json_integer()
    mantissa_frac = "." + one_or_more(char_range("0", "9"))
    exponent = "e" + select(["", "-", "+"]) + one_or_more(char_range("0", "9"))
    return lm + mantissa_int + optional(mantissa_frac) + optional(exponent)

@guidance(stateless=True)
def json_object(
    lm, schema_properties: Dict[str, any], definitions: Union[Dict[str, any], None]
):
    lm += "{"
    items = list(schema_properties.items())
    for i, (name, nxt_node) in enumerate(items):
        lm += f'"{name}":' + json_node(nxt_node, definitions)
        if i < len(items) - 1:
            lm += ','
    lm += '}'
    return lm

@guidance(stateless=True)
def json_array(
    lm, item_node: Dict[str, any], definitions: Union[Dict[str, any], None]
):
    inner = optional(
        zero_or_more(json_node(item_node, definitions) + ",")
        + json_node(item_node, definitions)
    )
    return lm + "[" + inner + "]"

@guidance(stateless=True)
def json_anyOf(
    lm, options: List[Dict[str, any]], definitions: Dict[str, any]
):
    all_opts = []
    for opt in options:
        all_opts.append(json_node(opt, definitions))
    return lm + select(options=all_opts)

def _get_definition(reference: str, definitions: Dict[str, any]) -> Dict[str, any]:
    assert definitions is not None
    REF_START = "#/$defs/"
    assert reference.startswith(
        REF_START
    ), f"Reference {reference} must start with {REF_START}"

    target_name = reference[len(REF_START) :]
    return definitions[target_name]

@guidance(stateless=True)
def json_node(
    lm, node: Dict[str, any], definitions: Union[Dict[str, any], None]
):
    ANYOF_STRING = "anyOf"
    if ANYOF_STRING in node:
        return lm + json_anyOf(node[ANYOF_STRING], definitions)

    REF_STRING = "$ref"
    if REF_STRING in node:
        node = _get_definition(node[REF_STRING], definitions)

    if node["type"] == "null":
        return lm + "null"
    elif node["type"] == "string":
        return lm + json_string()
    elif node["type"] == "boolean":
        return lm + select(["true", "false"])
    elif node["type"] == "integer":
        return lm + json_integer()
    elif node["type"] == "number":
        return lm + json_number()
    elif node["type"] == "object":
        return lm + json_object(node["properties"], definitions)
    elif node["type"] == "array":
        return lm + json_array(node["items"], definitions)
    else:
        raise ValueError(f"Unsupported type in schema: {node['type']}")


@guidance(stateless=True)
def json_schema_to_grammar(lm, schema: str | Dict[str, any]):
    if isinstance(schema, str):
        schema = json.loads(schema)
        
    _DEFS_KEY = "$defs"

    definitions = None
    if _DEFS_KEY in schema:
        definitions = schema[_DEFS_KEY]
        del schema[_DEFS_KEY]

    return lm + json_node(schema, definitions)