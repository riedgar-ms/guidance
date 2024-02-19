import json
from typing import Dict, List, Union, Any

from ._grammar import Byte, GrammarFunction, Join, Select, select
from .library._char_range import char_range

_QUOTE = Byte(b'"')
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
_OPEN_BRACE = Byte(b"{")
_CLOSE_BRACE = Byte(b"}")
_OPEN_BRACKET = Byte(b"[")
_CLOSE_BRACKET = Byte(b"]")
_COMMA = Byte(b",")
_COLON = Byte(b":")


def _make_optional(f: GrammarFunction) -> GrammarFunction:
    return select(["", f])


def _process_int() -> GrammarFunction:
    return Join([select(["-", ""]), select([char_range("0", "9")], recurse=True)])


def _process_number() -> GrammarFunction:
    mantissa_int = _process_int()
    mantissa_frac = _make_optional(
        Join([Byte(b"."), select([char_range("0", "9")], recurse=True)])
    )
    exponent = _make_optional(
        Join(
            [
                "e",
                # Since the exponent can contain a '+', can't just reuse
                # _process_int() here
                select(["", "-", "+"]),
                select([char_range("0", "9")], recurse=True),
            ]
        )
    )
    return Join(
        [
            mantissa_int,
            mantissa_frac,
            exponent,
        ],
    )

def _process_object(
    schema_properties: Union[Dict[str, Any], None],
    additional_properties: Union[Dict[str, Any], None],
    definitions: Union[Dict[str, Any], None]
) -> GrammarFunction:
    properties = []
    additional = None

    if schema_properties:
        properties = _process_properties(
            schema_properties,
            definitions
        )
    if additional_properties:
        additional = _process_additional_properties(
            additional_properties,
            definitions
        )
    if properties and additional is None:
        return Join([_OPEN_BRACE, *properties, _CLOSE_BRACE])
    if properties and additional is not None:
        return Join([_OPEN_BRACE, *properties, _make_optional(Join([_COMMA, additional])), _CLOSE_BRACE])
    if not properties and additional is not None:
        return Join([_OPEN_BRACE, _make_optional(additional), _CLOSE_BRACE])
    return Join([_OPEN_BRACE, _CLOSE_BRACE])

def _process_properties(
    schema_properties: Dict[str, Any],
    definitions: Union[Dict[str, Any], None]
):
    properties = []
    for name, nxt_node in schema_properties.items():
        nxt = Join(
            [
                Join([_QUOTE, name, _QUOTE]),
                _COLON,
                _process_node(nxt_node, definitions),
            ]
        )
        properties.append(nxt)
        if len(properties) < len(schema_properties):
            properties.append(_COMMA)
    return properties

def _process_additional_properties(
    additional_properties: Dict[str, Any],
    definitions: Union[Dict[str, Any], None]
):
    s = Select([], recursive=True)
    nxt = Join(
        [
            Join([_QUOTE, _SAFE_STRING, _QUOTE]),
            _COLON,
            _process_node(additional_properties, definitions),
        ]
    )
    s.values = [nxt, Join([nxt, _COMMA, s])]
    return s

def _process_array(
    item_node: Dict[str, Any], definitions: Union[Dict[str, Any], None]
) -> GrammarFunction:
    return Join(
        [
            _OPEN_BRACKET,
            _make_optional(
                # One or more items
                Join(
                    [
                        select(
                            ["", Join([_process_node(item_node, definitions), _COMMA])],
                            recurse=True,
                        ),
                        _process_node(item_node, definitions),
                    ]
                )
            ),
            _CLOSE_BRACKET,
        ]
    )


def _get_definition(reference: str, definitions: Dict[str, Any]) -> Dict[str, Any]:
    assert definitions is not None
    REF_START = "#/$defs/"
    assert reference.startswith(
        REF_START
    ), f"Reference {reference} must start with {REF_START}"

    target_name = reference[len(REF_START) :]
    return definitions[target_name]


def _process_anyOf(
    options: List[Dict[str, Any]], definitions: Dict[str, Any]
) -> GrammarFunction:
    all_opts = []
    for opt in options:
        all_opts.append(_process_node(opt, definitions))
    return select(options=all_opts)

def _process_enum(options: list[Any]):
    # Should we narrow type annotation or use compact json.dumps?
    all_opts = []
    for opt in options:
        all_opts.append(
            json.dumps(opt)
        )
    return select(options=all_opts)

def _process_node(
    node: Dict[str, Any], definitions: Union[Dict[str, Any], None]
) -> GrammarFunction:
    ANYOF_STRING = "anyOf"
    if ANYOF_STRING in node:
        return _process_anyOf(node[ANYOF_STRING], definitions)

    REF_STRING = "$ref"
    if REF_STRING in node:
        node = _get_definition(node[REF_STRING], definitions)

    if "enum" in node:
        return _process_enum(node["enum"])
    if node["type"] == "null":
        # Not completely sure about this
        return Select(["null"])
    elif node["type"] == "string":
        return Join([_QUOTE, _SAFE_STRING, _QUOTE])
    elif node["type"] == "boolean":
        return select(["true", "false"])
    elif node["type"] == "integer":
        return _process_int()
    elif node["type"] == "number":
        return _process_number()
    elif node["type"] == "object":
        return _process_object(
            node.get("properties"),
            node.get("additionalProperties"),
            definitions
        )
    elif node["type"] == "array":
        if "type" in node["items"]:
            item_node = dict(type=node["items"]["type"])
            if item_node["type"] == "object":
                item_node["properties"] = node["items"]["properties"]
        else:
            item_node = _get_definition(node["items"][REF_STRING], definitions)
        return _process_array(item_node, definitions)
    else:
        raise ValueError(f"Unsupported type in schema: {node['type']}")


def _json_schema_obj_to_grammar(schema_obj: Dict[str, Any]) -> GrammarFunction:
    _DEFS_KEY = "$defs"

    definitions = None
    if _DEFS_KEY in schema_obj:
        definitions = schema_obj[_DEFS_KEY]
        del schema_obj[_DEFS_KEY]

    return _process_node(schema_obj, definitions)


def json_schema_to_grammar(schema: str) -> GrammarFunction:
    schema_obj = json.loads(schema)

    return _json_schema_obj_to_grammar(schema_obj)
