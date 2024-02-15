import guidance
from guidance import gen, capture
from ..utils import get_model


def test_gpt2():
    gpt2 = get_model("transformers:gpt2")
    lm = gpt2 + "this is a test" + gen("test", max_tokens=10)
    assert len(str(lm)) > len("this is a test")


def test_phi2():
    phi2 = get_model("transformers:microsoft/phi-2")
    lm = phi2 + "this is a test" + gen("test", max_tokens=10)
    assert len(str(lm)) > len("this is a test")


def test_recursion_error():
    """This checks for an infinite recursion error resulting from a terminal node at the root of a grammar."""
    gpt2 = get_model("transformers:gpt2")

    INSTRUCTIONS = "Tweak this proverb to apply to model instructions instead."

    # define a guidance program that adapts a proverb
    lm = gpt2 + f"""{INSTRUCTIONS} {gen('verse', max_tokens=2)}"""
    assert len(str(lm)) > len(INSTRUCTIONS)
