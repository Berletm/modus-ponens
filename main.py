import enum, dataclasses


@enum.unique
class FormulaType(enum.Enum):
    AND  = enum.auto()
    OR   = enum.auto()
    NOT  = enum.auto()
    IMPL = enum.auto()
    VAR  = enum.auto()

@dataclasses.dataclass
class Formula:
    type  : FormulaType
    children : list
    value: str = ""

    def __repr__(self) -> str:
        return formula2str(self)

    def __eq__(self, other) -> bool:
        return is_equal(self, other)

    def __hash__(self) -> int:
        if self.type == FormulaType.VAR:
            return hash(("VAR", self.value))

        children_hash = tuple(hash(child) for child in self.children)

        if self.type == FormulaType.NOT:
            return hash(("NOT", children_hash[0]))

        if self.type in [FormulaType.AND, FormulaType.OR]:
            child_hashes = tuple(sorted(children_hash))
            return hash((self.type.name, child_hashes))

        return hash((self.type.name, children_hash[0], children_hash[1]))


def is_equal(f1: Formula, f2: Formula) -> bool:
    if f1 is None and f2 is None:
        return True

    if f1 is None or f2 is None:
        return False

    if f1.type != f2.type:
        return False

    match f1.type:
        case FormulaType.VAR:
            return f1.value == f2.value

        case FormulaType.NOT:
            return is_equal(f1.children[0], f2.children[0])

        case FormulaType.AND | FormulaType.OR:
            direct_match = (is_equal(f1.children[0], f2.children[0]) and
                            is_equal(f1.children[1], f2.children[1]))

            swapped_match = (is_equal(f1.children[0], f2.children[1]) and
                             is_equal(f1.children[1], f2.children[0]))

            return direct_match or swapped_match

        case FormulaType.IMPL:
            return (is_equal(f1.children[0], f2.children[0]) and
                    is_equal(f1.children[1], f2.children[1]))

        case _:
            return False

def type2str(formula_type: FormulaType) -> str:
    match formula_type:
        case FormulaType.AND:
            return "and"
        case FormulaType.OR:
            return "or"
        case FormulaType.NOT:
            return "not"
        case FormulaType.IMPL:
            return "implies"
        case _:
            return ""

def str2type(formula_type: str) -> FormulaType:
    match formula_type:
        case "and":
            return FormulaType.AND
        case "or":
            return FormulaType.OR
        case "not":
            return FormulaType.NOT
        case "implies":
            return FormulaType.IMPL
        case _:
            return FormulaType.VAR

def formula2str(formula: Formula) -> str:
    match formula.type:
        case FormulaType.VAR:
            return formula.value
        case FormulaType.NOT:
            return "(" + type2str(formula.type) + f" {formula2str(formula.children[0])})"
        case FormulaType.IMPL | FormulaType.AND | FormulaType.OR:
            return "(" + type2str(formula.type) + f" {formula2str(formula.children[0])} {formula2str(formula.children[1])})"

class Parser:
    def __init__(self, formula_str: str):
        self.formula_str = formula_str
        self.pos = 0
        self.len = len(formula_str)

    def skip_whitespace(self) -> None:
        while self.pos < self.len and self.formula_str[self.pos].isspace():
            self.pos += 1

    def read_token(self) -> str:
        self.skip_whitespace()

        if self.pos >= self.len:
            return ""

        if self.formula_str[self.pos] in "()":
            token = self.formula_str[self.pos]
            self.pos += 1
            return token

        token = ""

        while self.pos != self.len:
            c = self.formula_str[self.pos]
            if c == " " or c in "()":
                break
            token += c
            self.pos += 1

        return token

    def parse_formula(self) -> Formula:
        token = self.read_token()

        if token == "(":
            op_token = self.read_token()
            formula_type = str2type(op_token)

            match formula_type:
                case FormulaType.NOT:
                    child = self.parse_formula()
                    close_paren = self.read_token()

                    if close_paren != ")":
                        raise RuntimeError(f"wrong syntax: expected ) at {self.pos - 1}")

                    return Formula(type=formula_type, children=[child], value=type2str(formula_type))
                case FormulaType.AND | FormulaType.OR | FormulaType.IMPL:
                    left_child = self.parse_formula()
                    right_child = self.parse_formula()
                    close_paren = self.read_token()

                    if close_paren != ")":
                        raise RuntimeError(f"wrong syntax: expected ) at {self.pos - 1}")

                    return Formula(type=formula_type, children=[left_child, right_child], value=type2str(formula_type))
                case FormulaType.VAR:
                    var = Formula(type=formula_type, children=[], value=op_token)
                    close_paren = self.read_token()

                    if close_paren != ")":
                        raise RuntimeError(f"wrong syntax: expected ) at {self.pos - 1}")

                    return var
                case _:
                    raise RuntimeError(f"wrong syntax: unexpected trailing symbol at {self.pos}")
        else:
            if not token:
                raise RuntimeError(f"wrong syntax: unexpected end of formula")
            return Formula(type=FormulaType.VAR, children=[], value=token)


def normalize_formula(formula: Formula) -> Formula:
    if not formula:
        return formula

    match formula.type:
        case FormulaType.AND:
            left_child = normalize_formula(formula.children[0])
            right_child = normalize_formula(formula.children[1])

            new_right = Formula(
                type=FormulaType.NOT,
                children=[right_child],
                value=type2str(FormulaType.NOT)
            )

            impl_formula = Formula(
                type=FormulaType.IMPL,
                children=[left_child, new_right],
                value=type2str(FormulaType.IMPL)
            )

            return Formula(
                type=FormulaType.NOT,
                children=[impl_formula],
                value=type2str(FormulaType.NOT)
            )

        case FormulaType.OR:
            left_child = normalize_formula(formula.children[0])
            right_child = normalize_formula(formula.children[1])

            new_left = Formula(
                type=FormulaType.NOT,
                children=[left_child],
                value=type2str(FormulaType.NOT)
            )

            return Formula(
                type=FormulaType.IMPL,
                children=[new_left, right_child],
                value=type2str(FormulaType.IMPL)
            )

        case _:
            return formula

def copy_formula(f: Formula) -> Formula:
    children_copy = [copy_formula(child) for child in f.children]
    return Formula(type=f.type, children=children_copy, value=f.value)

def match_pattern(pattern: Formula, target: Formula, substitution: dict[str, Formula] = None) -> dict[str, Formula] | None:
    if substitution is None:
        substitution = {}

    if pattern.type == FormulaType.VAR:
        var_name = pattern.value

        if var_name in substitution:
            if not substitution[var_name] == target:
                return None
            return substitution
        else:
            substitution[var_name] = copy_formula(target)
            return substitution

    if pattern.type != target.type:
        return None

    if pattern.type == FormulaType.NOT:
        if len(pattern.children) != 1 or len(target.children) != 1:
            return None
        return match_pattern(pattern.children[0], target.children[0], substitution)

    if pattern.type in [FormulaType.AND, FormulaType.OR, FormulaType.IMPL]:
        if len(pattern.children) != 2 or len(target.children) != 2:
            return None

        substitution = match_pattern(pattern.children[0], target.children[0], substitution)
        if substitution is None:
            return None

        substitution = match_pattern(pattern.children[1], target.children[1], substitution)
        return substitution

    return None

def Var(name: str) -> Formula:
    return Formula(type=FormulaType.VAR, children=[], value=name)

def Impl(left: Formula, right: Formula) -> Formula:
    return Formula(type=FormulaType.IMPL, children=[left, right])

def Not(f: Formula) -> Formula:
    return Formula(type=FormulaType.NOT, children=[f])

def apply_substitution(pattern: Formula, substitution: dict[str, Formula]) -> Formula:
    if pattern.type == FormulaType.VAR:
        if pattern.value in substitution:
            return copy_formula(substitution[pattern.value])
        return Var(pattern.value)

    children = [apply_substitution(child, substitution) for child in pattern.children]
    return Formula(type=pattern.type, children=children, value=pattern.value)

class Prover:
    def __init__(self):
        self.proof_cache = {}
        self.axioms = [
                        "(implies A (implies B A))",
                        "(implies (implies A (implies B C)) (implies (implies A B) (implies A C)))",
                        "(implies (implies (not B) (not A)) (implies (implies (not B) A) B))",
                        "(implies A A)"
                    ]
        self.axioms = [Parser(ax).parse_formula() for ax in self.axioms]


    def prove(self, target: Formula, hypotheses:list = None, depth:int = 0, max_depth:int = 1000) -> list|None:
        if hypotheses is None:
            hypotheses = []

        cache_key = (target, tuple(hypotheses), depth)
        if cache_key in self.proof_cache:
            return self.proof_cache[cache_key]

        if depth > max_depth:
            return None

        for i, hyp in enumerate(hypotheses):
            if hyp == target:
                proof = [("hypothesis", i, target)]
                self.proof_cache[cache_key] = proof
                return proof

        if target.type == FormulaType.IMPL:
            left  = target.children[0]
            right = target.children[1]

            new_hypotheses = hypotheses + [left]
            proof_right = self.prove(right, new_hypotheses, depth + 1, max_depth)

            if proof_right is not None:
                proof = [("deduction", left, right, proof_right)]
                self.proof_cache[cache_key] = proof
                return proof

        for i, hyp in enumerate(hypotheses):
            if hyp.type == FormulaType.IMPL and hyp.children[1] == target:
                left = hyp.children[0]
                proof_left = self.prove(left, hypotheses, depth + 1, max_depth)

                if proof_left is not None:
                    proof = [("mp", i, proof_left, target)]
                    self.proof_cache[cache_key] = proof
                    return proof

        for axiom_idx, axiom in enumerate(self.axioms):
            substitution = match_pattern(axiom, target)
            if substitution is not None:
                proof = [("axiom", axiom_idx + 1, substitution, target)]
                self.proof_cache[cache_key] = proof
                return proof

def  main() -> None:
    exp = "(implies A A)"

    f = Parser(exp).parse_formula()

    f = normalize_formula(f)

    print(Prover().prove(f))

if __name__ == "__main__":
    main()
