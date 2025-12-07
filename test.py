import pytest
from main import Parser, is_equal, Var, Impl, Not, Formula, match_pattern, apply_substitution


@pytest.mark.parametrize("f1str, f2str, expected", [
    ("(and A B)", "(and A B)", True),
    ("(and A B)", "(or A B)", False),
    ("(or (and A B) (not C))", "(or (not C) (and A B))", True),
])
def test_equal(f1str: str, f2str: str, expected: bool):
    f1 = Parser(f1str).parse_formula()
    f2 = Parser(f2str).parse_formula()

    assert is_equal(f1, f2) == expected

@pytest.mark.parametrize("f1, f2, expected", [
    (Impl(
        Var("P"),
        Impl(
            Var("Q"), Var("P")
        )
    ),
     Impl(
        Var("A"),
        Impl(
            Not(Var("B")), Var("A")
        )
    ), True)
])
def test_equal(f1: Formula, f2: Formula, expected: bool):
    subs = match_pattern(f1, f2)
    f1 = apply_substitution(f1, subs)
    f2 = apply_substitution(f2, subs)

    assert is_equal(f1, f2) == expected
