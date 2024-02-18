from typing import List, Union

import json
import pydantic
import pydantic.json_schema
import pytest

from guidance._grammar import GrammarFunction
from guidance._parser import ParserException
from guidance._pydantic_to_grammar import pydantic_model_to_grammar, type_to_grammar


def check_object_with_grammar(
    target_object: pydantic.JsonValue | pydantic.BaseModel,
    grammar: GrammarFunction
):
    print(f"Checking {target_object}")
    json_string = json.dumps(
        target_object,
        separators=(",", ":"),
        default=pydantic.json_schema.to_jsonable_python
    )
    matches = grammar.match(json_string.encode(), raise_exceptions=True)
    assert matches.partial == False


def test_simple_model():
    class Simple(pydantic.BaseModel):
        my_string: str

    my_obj = Simple(my_string="some string")

    grammar = pydantic_model_to_grammar(my_obj)
    check_object_with_grammar(my_obj, grammar)


def test_model_with_int_list():
    class MyModel(pydantic.BaseModel):
        my_list: List[int] = pydantic.Field(default_factory=list)

    my_obj = MyModel(my_list=[1, 2, 3, 4])
    grammar = pydantic_model_to_grammar(my_obj)
    check_object_with_grammar(my_obj, grammar)


def test_nested_model():
    class A(pydantic.BaseModel):
        my_str: str = pydantic.Field(default="my_a_str")

    class B(pydantic.BaseModel):
        my_str: str = pydantic.Field(default="my_b_str")
        my_A: A = pydantic.Field(default_factory=A)

    class C(pydantic.BaseModel):
        my_str: str = pydantic.Field(default="my_c_str")
        my_B: B = pydantic.Field(default_factory=B)

    my_obj = C(my_str="some other string!")
    grammar = pydantic_model_to_grammar(my_obj)
    check_object_with_grammar(my_obj, grammar)


@pytest.mark.parametrize("has_A", [True, False])
def test_model_with_optional(has_A):
    class A(pydantic.BaseModel):
        my_str: str = pydantic.Field(default="my_a_str")

    class B(pydantic.BaseModel):
        b_str: str = pydantic.Field(default="Some string")
        my_A: Union[A, None] = pydantic.Field(default=None)

    if has_A:
        my_obj = B(my_A=A(my_str="a long string or two"))
    else:
        my_obj = B(b_str="A long b string")

    grammar = pydantic_model_to_grammar(my_obj)
    check_object_with_grammar(my_obj, grammar)


@pytest.mark.parametrize('type, obj', [(None, None), (str, 'hello'), (bool, True), (int, 42), (float, 3.14)])
def test_builtin_types(type, obj):
    grammar = type_to_grammar(type)
    check_object_with_grammar(obj, grammar)


def test_subscripted_generic():
    type = list[str]
    grammar = type_to_grammar(type)
    good = ['a', 'b', 'c']
    bad = [1, 2, 3]
    check_object_with_grammar(good, grammar)
    with pytest.raises(ParserException):
        check_object_with_grammar(bad, grammar)


def test_union():
    type = bool | int
    grammar = type_to_grammar(type)
    check_object_with_grammar(42, grammar)
    check_object_with_grammar(True, grammar)
    with pytest.raises(ParserException):
        check_object_with_grammar('string', grammar)


def test_dict():
    type = dict[str, int]
    grammar = type_to_grammar(type)
    check_object_with_grammar({'a': 1, 'b': 2}, grammar)
    with pytest.raises(ParserException):
        check_object_with_grammar({'a': '1', 'b': '2'}, grammar)
    with pytest.raises(ParserException):
        check_object_with_grammar({1: 1, 2: 2}, grammar)


def test_list_of_models():
    class Simple(pydantic.BaseModel):
        my_string: str
    type = list[Simple]
    grammar = type_to_grammar(type)
    obj = [
        Simple(my_string='hello'),
        Simple(my_string='world!')
    ]
    check_object_with_grammar(obj, grammar)


def test_type_to_grammar_on_model():
    class Simple(pydantic.BaseModel):
        my_string: str
    grammar = type_to_grammar(Simple)
    obj = Simple(my_string='hello')
    check_object_with_grammar(obj, grammar)
