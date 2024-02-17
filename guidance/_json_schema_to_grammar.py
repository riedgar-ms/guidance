import json
from collections.abc import MutableMapping
from typing import Dict, List, Union

from ._grammar import Byte, GrammarFunction, Join, Select, select, Ref
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
    schema_properties: Dict[str, any], refs: MutableMapping[str, Ref]
) -> GrammarFunction:
    properties = []
    for name, nxt_node in schema_properties.items():
        nxt = Join(
            [
                Join([_QUOTE, name, _QUOTE]),
                _COLON,
                _process_node(nxt_node, refs),
            ]
        )
        properties.append(nxt)
        if len(properties) < len(schema_properties):
            properties.append(_COMMA)
    return Join([_OPEN_BRACE, *properties, _CLOSE_BRACE])


def _process_array(
    item_node: Dict[str, any], refs: MutableMapping[str, Ref]
) -> GrammarFunction:
    return Join(
        [
            _OPEN_BRACKET,
            _make_optional(
                # One or more items
                Join(
                    [
                        select(
                            ["", Join([_process_node(item_node, refs), _COMMA])],
                            recurse=True,
                        ),
                        _process_node(item_node, refs),
                    ]
                )
            ),
            _CLOSE_BRACKET,
        ]
    )


def _process_anyOf(
    options: List[Dict[str, any]], refs: MutableMapping[str, Ref]
) -> GrammarFunction:
    all_opts = []
    for opt in options:
        all_opts.append(_process_node(opt, refs))
    return select(options=all_opts)


def _process_node(
    node: Dict[str, any], refs: MutableMapping[str, Ref]
) -> GrammarFunction:
    ANYOF_STRING = "anyOf"
    if ANYOF_STRING in node:
        return _process_anyOf(node[ANYOF_STRING], refs)

    REF_STRING = "$ref"
    if REF_STRING in node:
        return refs.setdefault(node[REF_STRING], Ref())

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
        return _process_object(node["properties"], refs)
    elif node["type"] == "array":
        item_node = node["items"]
        return _process_array(item_node, refs)
    else:
        raise ValueError(f"Unsupported type in schema: {node['type']}")


def _json_schema_obj_to_grammar(schema_obj: Dict[str, any]) -> GrammarFunction:
    _DEFS_KEY = "$defs"

    refs = {}
    definitions = None
    if _DEFS_KEY in schema_obj:
        definitions = schema_obj[_DEFS_KEY]
        definitions = {f'#/{_DEFS_KEY}/{k}': _process_node(v, refs) for k,v in definitions.items()}
        del schema_obj[_DEFS_KEY]
    
    node = _process_node(schema_obj, refs)
    
    if refs:
        # Update refs
        assert definitions is not None
        for k,v in refs.items():
            v.update(definitions[k])
    return node


def json_schema_to_grammar(schema: str) -> GrammarFunction:
    schema_obj = json.loads(schema)

    return _json_schema_obj_to_grammar(schema_obj)
