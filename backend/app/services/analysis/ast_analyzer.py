"""Structural (AST) analysis.

Parses student code once and extracts a :class:`CodeFeatures` snapshot that the
misconception rules consume. The analyzer is deliberately *descriptive*: it
records structural facts (there is a ``range(len(x) + 1)`` here, this function
has no ``return``) without judging them. Judgement lives in the rules, so the
same features can feed many rules and new rules need no analyzer changes.

If the code does not parse, ``CodeFeatures.syntax_error`` is populated and the
structural lists are left empty.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field


@dataclass
class RangeCall:
    """A ``range(...)`` call appearing in a for-loop header."""

    line: int
    # Raw unparsed argument snippets, for evidence messages.
    args_src: list[str] = field(default_factory=list)
    # True if any argument is of the form ``len(...) + <int>``.
    len_plus_offset: bool = False
    offset: int | None = None  # the +N / -N applied to len(...)


@dataclass
class IndexExpr:
    """A subscript like ``x[i]`` or ``x[len(x)]``."""

    line: int
    src: str
    uses_len_as_index: bool = False  # x[len(x)] pattern


@dataclass
class WhileLoop:
    """A while-loop with enough detail to reason about termination."""

    line: int
    test_src: str
    is_literal_true: bool = False          # while True
    has_break: bool = False
    # Names compared in the test, e.g. {'i'} in `while i < n`.
    test_names: set[str] = field(default_factory=set)
    # Names assigned (mutated) anywhere in the loop body.
    body_assigned_names: set[str] = field(default_factory=set)


@dataclass
class FunctionInfo:
    """A function definition and facts needed by multiple rules."""

    name: str
    line: int
    args: list[str] = field(default_factory=list)
    # Default values that are mutable literals (list/dict/set).
    mutable_default_args: list[str] = field(default_factory=list)
    has_return_value: bool = False   # at least one `return <expr>`
    has_bare_return: bool = False    # `return` with no value
    prints: bool = False             # calls print(...)
    # Names assigned at the top level of the body.
    assigned_names: set[str] = field(default_factory=set)
    # Names read in the body.
    read_names: set[str] = field(default_factory=set)
    is_recursive: bool = False       # calls itself
    # For recursion: does the body contain an if/return that can stop recursion?
    has_conditional_return: bool = False
    end_line: int = 0


@dataclass
class CallInfo:
    """A function call, for argument-count checks against local defs."""

    func_name: str
    line: int
    positional_count: int
    has_starargs: bool = False


@dataclass
class CodeFeatures:
    """Everything the rules need from a structural pass."""

    syntax_error: bool = False
    syntax_error_line: int | None = None
    syntax_error_msg: str | None = None

    for_ranges: list[RangeCall] = field(default_factory=list)
    index_exprs: list[IndexExpr] = field(default_factory=list)
    while_loops: list[WhileLoop] = field(default_factory=list)
    functions: list[FunctionInfo] = field(default_factory=list)
    calls: list[CallInfo] = field(default_factory=list)

    # `if x = 5` is a SyntaxError in Py3, but `if x is y` vs `==`, and
    # single-`=`-looking intent shows up as walrus misuse or assignment typos.
    assignment_in_bool_context: list[int] = field(default_factory=list)
    # `==` used where a statement/effect seems intended (expression statement).
    comparison_as_statement: list[int] = field(default_factory=list)

    # Boolean anti-patterns, each a (line, description) pair.
    boolean_antipatterns: list[tuple[int, str]] = field(default_factory=list)

    # Names used but never assigned/among params/builtins (scope hints).
    undefined_name_reads: dict[str, int] = field(default_factory=dict)

    total_lines: int = 0


_BUILTINS = set(dir(__builtins__)) | {
    "self",
    "cls",
    "print",
    "range",
    "len",
    "enumerate",
    "list",
    "dict",
    "set",
    "tuple",
    "str",
    "int",
    "float",
    "bool",
    "sum",
    "min",
    "max",
    "sorted",
    "abs",
    "True",
    "False",
    "None",
}


def _src(node: ast.AST) -> str:
    """Best-effort source for a node (for evidence messages)."""
    try:
        return ast.unparse(node)
    except Exception:  # pragma: no cover - unparse is reliable on 3.9+
        return "<expr>"


class _Analyzer(ast.NodeVisitor):
    def __init__(self) -> None:
        self.features = CodeFeatures()
        self._current_fn: FunctionInfo | None = None

    # ---- functions ----
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        info = FunctionInfo(name=node.name, line=node.lineno)
        info.end_line = getattr(node, "end_lineno", node.lineno) or node.lineno
        info.args = [a.arg for a in node.args.args]

        # Mutable default arguments: defaults align to the tail of args.
        defaults = node.args.defaults
        if defaults:
            tail = info.args[-len(defaults):]
            for name, default in zip(tail, defaults):
                if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    info.mutable_default_args.append(name)

        prev = self._current_fn
        self._current_fn = info

        for child in ast.walk(node):
            if isinstance(child, ast.Return):
                if child.value is None:
                    info.has_bare_return = True
                else:
                    info.has_return_value = True
            elif isinstance(child, ast.Call):
                fn = child.func
                if isinstance(fn, ast.Name):
                    if fn.id == "print":
                        info.prints = True
                    if fn.id == node.name:
                        info.is_recursive = True
            elif isinstance(child, ast.If):
                # A base case is typically an if whose body returns.
                for sub in ast.walk(child):
                    if isinstance(sub, ast.Return):
                        info.has_conditional_return = True
                        break

        # Top-level assigned / read names within the function body.
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                if isinstance(child.ctx, ast.Store):
                    info.assigned_names.add(child.id)
                elif isinstance(child.ctx, ast.Load):
                    info.read_names.add(child.id)

        self.features.functions.append(info)
        self.generic_visit(node)
        self._current_fn = prev

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

    # ---- for loops with range() ----
    def visit_For(self, node: ast.For) -> None:
        it = node.iter
        if isinstance(it, ast.Call) and isinstance(it.func, ast.Name) and it.func.id == "range":
            rc = RangeCall(line=it.lineno, args_src=[_src(a) for a in it.args])
            for arg in it.args:
                off = _len_plus_offset(arg)
                if off is not None:
                    rc.len_plus_offset = True
                    rc.offset = off
            self.features.for_ranges.append(rc)
        self.generic_visit(node)

    # ---- while loops ----
    def visit_While(self, node: ast.While) -> None:
        wl = WhileLoop(line=node.lineno, test_src=_src(node.test))
        if isinstance(node.test, ast.Constant) and node.test.value is True:
            wl.is_literal_true = True
        for n in ast.walk(node.test):
            if isinstance(n, ast.Name):
                wl.test_names.add(n.id)
        for stmt in node.body:
            for n in ast.walk(stmt):
                if isinstance(n, ast.Break):
                    wl.has_break = True
                if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
                    wl.body_assigned_names.add(n.id)
                # Augmented assignment (i += 1) stores via Name target too.
                if isinstance(n, ast.AugAssign) and isinstance(n.target, ast.Name):
                    wl.body_assigned_names.add(n.target.id)
        self.features.while_loops.append(wl)
        self.generic_visit(node)

    # ---- subscripts: x[i], x[len(x)] ----
    def visit_Subscript(self, node: ast.Subscript) -> None:
        ix = IndexExpr(line=node.lineno, src=_src(node))
        idx = node.slice
        # x[len(x)] — using length directly as an index.
        if (
            isinstance(idx, ast.Call)
            and isinstance(idx.func, ast.Name)
            and idx.func.id == "len"
        ):
            ix.uses_len_as_index = True
        self.features.index_exprs.append(ix)
        self.generic_visit(node)

    # ---- function calls (for arg-count checks) ----
    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name):
            has_star = any(isinstance(a, ast.Starred) for a in node.args)
            pos = sum(1 for a in node.args if not isinstance(a, ast.Starred))
            self.features.calls.append(
                CallInfo(
                    func_name=node.func.id,
                    line=node.lineno,
                    positional_count=pos,
                    has_starargs=has_star,
                )
            )
        self.generic_visit(node)

    # ---- comparison used as a bare statement: `x == 5` on its own line ----
    def visit_Expr(self, node: ast.Expr) -> None:
        if isinstance(node.value, ast.Compare) and any(
            isinstance(op, ast.Eq) for op in node.value.ops
        ):
            self.features.comparison_as_statement.append(node.lineno)
        self.generic_visit(node)

    # ---- boolean anti-patterns in conditions ----
    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        # Classic: `x == 1 or 2` / `x == 1 or x == 2 ... or 3` where an operand
        # of an `or`/`and` is a bare truthy constant (always True/short-circuits
        # incorrectly). Detects `if day == "sat" or "sun"`.
        if isinstance(node.op, ast.Or):
            for value in node.values:
                if isinstance(value, ast.Constant) and value.value not in (True, False, None):
                    self.features.boolean_antipatterns.append(
                        (
                            node.lineno,
                            f"`or {value.value!r}` is always truthy — a bare value "
                            "on one side of `or` does not compare against anything.",
                        )
                    )
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> None:
        # `is` / `is not` used to compare values (numbers, strings) rather than
        # identity — works by luck for small ints / interned strings, fails
        # generally.
        for op, comparator in zip(node.ops, node.comparators):
            if isinstance(op, (ast.Is, ast.IsNot)):
                if isinstance(comparator, ast.Constant) and not isinstance(
                    comparator.value, bool
                ) and comparator.value is not None:
                    self.features.boolean_antipatterns.append(
                        (
                            node.lineno,
                            "`is` compares identity, not value; use `==` to "
                            "compare values.",
                        )
                    )
        self.generic_visit(node)


def _len_plus_offset(node: ast.AST) -> int | None:
    """If node is ``len(...) + N`` or ``len(...) - N``, return the signed N."""
    if not isinstance(node, ast.BinOp) or not isinstance(node.op, (ast.Add, ast.Sub)):
        return None
    left, right = node.left, node.right
    is_len = (
        isinstance(left, ast.Call)
        and isinstance(left.func, ast.Name)
        and left.func.id == "len"
    )
    if is_len and isinstance(right, ast.Constant) and isinstance(right.value, int):
        return right.value if isinstance(node.op, ast.Add) else -right.value
    return None


def analyze_code(code: str) -> CodeFeatures:
    """Parse ``code`` and return structural features."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return CodeFeatures(
            syntax_error=True,
            syntax_error_line=e.lineno,
            syntax_error_msg=e.msg,
            total_lines=len(code.splitlines()),
        )

    analyzer = _Analyzer()
    analyzer.visit(tree)
    features = analyzer.features
    features.total_lines = len(code.splitlines())

    # Simple scope hint: names read in a function but never assigned there,
    # not a parameter, and not a builtin / global function name.
    global_fn_names = {f.name for f in features.functions}
    for fn in features.functions:
        local = set(fn.args) | fn.assigned_names | _BUILTINS | global_fn_names
        for name in fn.read_names:
            if name not in local:
                features.undefined_name_reads.setdefault(name, fn.line)

    return features
