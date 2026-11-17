"""Safe expression language for models and contracts (Python syntax, data semantics).

Expressions are DATA, not code. Source is parsed with `ast`, checked against a closed
node whitelist and rewritten so that every operator, literal and iteration goes through
helpers in this module. There is no attribute access (``pre.x``/``post.x`` become a field
lookup), no imports, no lambdas, no calls except the whitelisted functions below, and no
name may start with an underscore. Iteration is canonical (sets and maps in sorted order),
so results never depend on Python hash randomization. A shared work budget bounds every
loop, so a hostile expression fails with an error instead of hanging the checker.
"""
import ast
import time

from .values import FMap, FvError, MAX_COLLECTION, ckey, require, show

MAX_RANGE = 10000
MAX_POWERSET = 12
_KEYWORDS = {"pre", "post"}


class Budget:
    """Wall-clock budget shared by all evaluations of one run."""

    def __init__(self, seconds=None):
        self.deadline = None if seconds is None else time.monotonic() + seconds
        self.ticks = 0

    def tick(self, n=1):
        self.ticks += n
        if self.deadline is not None and self.ticks & 0x3FF == 0 and time.monotonic() > self.deadline:
            raise BudgetExceeded("time budget exhausted")

    def expired(self):
        return self.deadline is not None and time.monotonic() > self.deadline


class BudgetExceeded(FvError):
    pass


_BUDGET = [Budget()]


def set_budget(budget):
    _BUDGET[0] = budget


def _check(v):
    if v is None or v is True or v is False or type(v) in (int, str, tuple, frozenset, FMap):
        return v
    raise FvError("expression produced an unsupported value: " + type(v).__name__)


def _items(x):
    """Canonical iteration over any model collection."""
    b = _BUDGET[0]
    if type(x) is frozenset:
        seq = sorted(x, key=ckey)
    elif type(x) is FMap:
        seq = list(x)
    elif type(x) in (tuple, str):
        seq = x
    elif hasattr(x, "__next__"):  # a generator produced by a whitelisted comprehension
        seq = x
    else:
        raise FvError("cannot iterate over " + type(x).__name__)
    for item in seq:
        b.tick()
        yield item


def _sized(v):
    require(len(v) <= MAX_COLLECTION, "collection exceeds size limit")
    return v


def _num(*xs):
    for x in xs:
        require(type(x) is int, "arithmetic needs integers, got " + type(x).__name__)


def f_add(a, b):
    if type(a) is int and type(b) is int:
        return a + b
    if type(a) is type(b) and type(a) in (str, tuple):
        return _sized(a + b)
    raise FvError("+ needs two integers, strings or sequences")


def f_sub(a, b):
    if type(a) is int and type(b) is int:
        return a - b
    if type(a) is frozenset and type(b) is frozenset:
        return a - b
    raise FvError("- needs two integers or two sets")


def f_mul(a, b):
    _num(a, b)
    return a * b


def f_floordiv(a, b):
    _num(a, b)
    require(b != 0, "division by zero")
    return a // b


def f_mod(a, b):
    _num(a, b)
    require(b != 0, "modulo by zero")
    return a % b


def _setop(name, op):
    def f(a, b):
        if type(a) is frozenset and type(b) is frozenset:
            return _sized(op(a, b))
        if type(a) is int and type(b) is int and type(a) is not bool:
            return op(a, b)
        raise FvError(name + " needs two sets or two integers")
    return f


f_or = _setop("|", lambda a, b: a | b)
f_and = _setop("&", lambda a, b: a & b)
f_xor = _setop("^", lambda a, b: a ^ b)


def f_neg(a):
    _num(a)
    return -a


def f_field(ns, name):
    require(type(ns) is FMap, "pre/post are only available in transition properties")
    return ns[name]


def f_tupleof(it):
    return _sized(tuple(_check(x) for x in _items(it)))


def f_setof(it):
    return _sized(frozenset(_check(x) for x in _items(it)))


def f_mapof(it):
    pairs = []
    for p in _items(it):
        require(type(p) is tuple and len(p) == 2, "map entries must be (key, value) pairs")
        pairs.append((_check(p[0]), _check(p[1])))
    return FMap(pairs)


def f_len(x):
    require(type(x) in (tuple, frozenset, FMap, str), "len() needs a collection")
    return len(x)


def f_sum(it):
    total = 0
    for x in _items(it):
        _num(x)
        total += x
    return total


def _extreme(pick, args):
    items = list(_items(args[0])) if len(args) == 1 else list(args)
    require(items, "min()/max() of an empty collection")
    return pick(items, key=ckey)


def f_min(*args):
    return _extreme(min, args)


def f_max(*args):
    return _extreme(max, args)


def f_abs(x):
    _num(x)
    return abs(x)


def f_all(it):
    return all(bool(x) for x in _items(it))


def f_any(it):
    return any(bool(x) for x in _items(it))


def f_sorted(it):
    return tuple(sorted(_items(it), key=ckey))


def f_set(it=()):
    return f_setof(it)


def f_tuple(it=()):
    return f_tupleof(it)


def f_range(a, b=None):
    lo, hi = (0, a) if b is None else (a, b)
    _num(lo, hi)
    require(hi - lo <= MAX_RANGE, "range() larger than %d elements" % MAX_RANGE)
    return tuple(range(lo, hi))


def f_update(m, k, v):
    if type(m) is FMap:
        return FMap(list(m.items()) + [(k, _check(v))])
    if type(m) is tuple:
        require(type(k) is int and 0 <= k < len(m), "sequence index out of range")
        return m[:k] + (_check(v),) + m[k + 1:]
    raise FvError("update() needs a map or a sequence")


def f_keys(m):
    require(type(m) is FMap, "keys() needs a map")
    return frozenset(m)


def f_values(m):
    require(type(m) is FMap, "values() needs a map")
    return tuple(v for _, v in m.items())


def f_items(m):
    require(type(m) is FMap, "items() needs a map")
    return frozenset(m.items())


def f_get(m, k, default=None):
    require(type(m) is FMap, "get() needs a map")
    return m.get(k, default)


def f_remove(m, k):
    if type(m) is FMap:
        return FMap((key, v) for key, v in m.items() if key != k or ckey(key) != ckey(k))
    if type(m) is frozenset:
        return m - {k}
    raise FvError("remove() needs a map or a set")


def f_merge(a, b):
    require(type(a) is FMap and type(b) is FMap, "merge() needs two maps")
    return FMap(list(a.items()) + list(b.items()))


def f_implies(a, b):
    return (not a) or bool(b)


def f_powerset(s):
    require(type(s) is frozenset and len(s) <= MAX_POWERSET, "powerset() needs a set of at most %d elements" % MAX_POWERSET)
    items = sorted(s, key=ckey)
    out = []
    for mask in range(1 << len(items)):
        _BUDGET[0].tick()
        out.append(frozenset(items[i] for i in range(len(items)) if mask >> i & 1))
    return frozenset(out)


def f_choose(s):
    items = list(_items(s))
    require(items, "choose() from an empty collection")
    return min(items, key=ckey)


def f_append(t, x):
    require(type(t) is tuple, "append() needs a sequence")
    return _sized(t + (_check(x),))


def f_head(t):
    require(type(t) is tuple and t, "head() of an empty sequence")
    return t[0]


def f_tail(t):
    require(type(t) is tuple and t, "tail() of an empty sequence")
    return t[1:]


def f_last(t):
    require(type(t) is tuple and t, "last() of an empty sequence")
    return t[-1]


def f_count(it):
    return sum(1 for x in _items(it) if x)


FUNCTIONS = {
    "len": f_len, "sum": f_sum, "min": f_min, "max": f_max, "abs": f_abs, "all": f_all, "any": f_any,
    "sorted": f_sorted, "set": f_set, "tuple": f_tuple, "range": f_range, "update": f_update,
    "keys": f_keys, "values": f_values, "items": f_items, "get": f_get, "remove": f_remove,
    "merge": f_merge, "mapof": f_mapof, "implies": f_implies, "powerset": f_powerset, "choose": f_choose,
    "append": f_append, "head": f_head, "tail": f_tail, "last": f_last, "count": f_count,
}
_HELPERS = {
    "_fv_add": f_add, "_fv_sub": f_sub, "_fv_mul": f_mul, "_fv_floordiv": f_floordiv, "_fv_mod": f_mod,
    "_fv_or": f_or, "_fv_and": f_and, "_fv_xor": f_xor, "_fv_neg": f_neg, "_fv_field": f_field,
    "_fv_tupleof": f_tupleof, "_fv_setof": f_setof, "_fv_mapof": f_mapof, "_fv_items": _items,
}
_BINOPS = {ast.Add: "_fv_add", ast.Sub: "_fv_sub", ast.Mult: "_fv_mul", ast.FloorDiv: "_fv_floordiv",
           ast.Mod: "_fv_mod", ast.BitOr: "_fv_or", ast.BitAnd: "_fv_and", ast.BitXor: "_fv_xor"}
RESERVED = set(FUNCTIONS) | _KEYWORDS | {"True", "False", "None"}

_ALLOWED = (ast.Expression, ast.BoolOp, ast.And, ast.Or, ast.BinOp, ast.UnaryOp, ast.Not, ast.USub, ast.UAdd,
            ast.Compare, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.In, ast.NotIn,
            ast.IfExp, ast.Name, ast.Load, ast.Store, ast.Constant, ast.Tuple, ast.List, ast.Set, ast.Dict,
            ast.Subscript, ast.Slice, ast.Attribute, ast.Call, ast.GeneratorExp, ast.ListComp, ast.SetComp,
            ast.DictComp, ast.comprehension) + tuple(_BINOPS)


def _call(name, *args):
    return ast.Call(func=ast.Name(id=name, ctx=ast.Load()), args=list(args), keywords=[])


class _Rewrite(ast.NodeTransformer):
    def visit_BinOp(self, node):
        self.generic_visit(node)
        return _call(_BINOPS[type(node.op)], node.left, node.right)

    def visit_UnaryOp(self, node):
        self.generic_visit(node)
        if isinstance(node.op, ast.USub):
            return _call("_fv_neg", node.operand)
        if isinstance(node.op, ast.UAdd):
            return _call("_fv_add", ast.Constant(value=0), node.operand)
        return node

    def visit_Attribute(self, node):
        self.generic_visit(node)
        return _call("_fv_field", node.value, ast.Constant(value=node.attr))

    def visit_List(self, node):
        self.generic_visit(node)
        return ast.Tuple(elts=node.elts, ctx=ast.Load())

    def visit_Set(self, node):
        self.generic_visit(node)
        return _call("_fv_setof", ast.Tuple(elts=node.elts, ctx=ast.Load()))

    def visit_Dict(self, node):
        self.generic_visit(node)
        pairs = [ast.Tuple(elts=[k, v], ctx=ast.Load()) for k, v in zip(node.keys, node.values)]
        return _call("_fv_mapof", ast.Tuple(elts=pairs, ctx=ast.Load()))

    def visit_comprehension(self, node):
        self.generic_visit(node)
        node.iter = _call("_fv_items", node.iter)
        return node

    def _gen(self, node, elt):
        return ast.GeneratorExp(elt=elt, generators=node.generators)

    def visit_ListComp(self, node):
        self.generic_visit(node)
        return _call("_fv_tupleof", self._gen(node, node.elt))

    def visit_SetComp(self, node):
        self.generic_visit(node)
        return _call("_fv_setof", self._gen(node, node.elt))

    def visit_DictComp(self, node):
        self.generic_visit(node)
        pair = ast.Tuple(elts=[node.key, node.value], ctx=ast.Load())
        return _call("_fv_mapof", self._gen(node, pair))


def _validate(tree, source):
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED):
            raise FvError("unsupported syntax %s in expression: %s" % (type(node).__name__, source))
        if isinstance(node, ast.Name) and node.id.startswith("_"):
            raise FvError("names may not start with an underscore: " + node.id)
        if isinstance(node, ast.Constant) and not (node.value is None or type(node.value) in (bool, int, str)):
            raise FvError("only integer, string, boolean and None literals are allowed: " + source)
        if isinstance(node, ast.Attribute):
            if not (isinstance(node.value, ast.Name) and node.value.id in _KEYWORDS and not node.attr.startswith("_")):
                raise FvError("attribute access is only allowed as pre.<name> / post.<name>: " + source)
        if isinstance(node, ast.Call):
            if not (isinstance(node.func, ast.Name) and node.func.id in FUNCTIONS) or node.keywords:
                raise FvError("only whitelisted functions may be called (positional args): " + source)
            if any(isinstance(a, ast.Starred) for a in node.args):
                raise FvError("starred arguments are not allowed: " + source)
        if isinstance(node, ast.comprehension) and getattr(node, "is_async", 0):
            raise FvError("async comprehensions are not allowed")
        if isinstance(node, ast.Dict) and any(k is None for k in node.keys):
            raise FvError("dict unpacking is not allowed: " + source)


def free_names(tree):
    """Names read by the expression that are not bound by one of its comprehensions."""
    found = set()

    def targets(t):
        if isinstance(t, ast.Name):
            return {t.id}
        if isinstance(t, ast.Tuple):
            out = set()
            for e in t.elts:
                out |= targets(e)
            return out
        raise FvError("comprehension targets must be names or tuples of names")

    def visit(node, bound):
        if isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Load) and node.id not in bound:
                found.add(node.id)
            return
        if isinstance(node, (ast.GeneratorExp, ast.ListComp, ast.SetComp, ast.DictComp)):
            inner = set(bound)
            for gen in node.generators:
                visit(gen.iter, inner)
                inner = inner | targets(gen.target)
                for cond in gen.ifs:
                    visit(cond, inner)
            for part in ("elt", "key", "value"):
                if hasattr(node, part):
                    visit(getattr(node, part), inner)
            return
        if isinstance(node, ast.Attribute):
            visit(node.value, bound)
            return
        for child in ast.iter_child_nodes(node):
            visit(child, bound)

    visit(tree, set())
    return found


class Expr:
    __slots__ = ("source", "code", "names", "tree")

    def __init__(self, source):
        require(isinstance(source, str) and source.strip(), "expression must be a nonempty string")
        require(len(source) <= 8192, "expression longer than 8192 characters")
        try:
            tree = ast.parse(source.strip(), mode="eval")
        except SyntaxError as error:
            raise FvError("syntax error in expression %r: %s" % (source, error.msg)) from None
        _validate(tree, source)
        self.source = source
        self.tree = tree
        self.names = free_names(tree.body) - set(FUNCTIONS)
        rewritten = ast.fix_missing_locations(_Rewrite().visit(tree))
        self.code = compile(rewritten, "<fv-expression>", "eval")

    def constants(self):
        return {n.value for n in ast.walk(self.tree) if isinstance(n, ast.Constant) and type(n.value) is str}

    def __call__(self, env):
        scope = dict(_GLOBALS)
        scope.update(env)
        try:
            return _check(eval(self.code, scope))  # noqa: S307 - validated, rewritten AST; no builtins
        except FvError as error:
            raise FvError("%s (in: %s)" % (error, self.source)) from None
        except (TypeError, KeyError, IndexError, ZeroDivisionError, NameError, RecursionError, ValueError) as error:
            raise FvError("cannot evaluate %r: %s: %s" % (self.source, type(error).__name__, str(error)[:200])) from None


_GLOBALS = {"__builtins__": {}}
_GLOBALS.update(FUNCTIONS)
_GLOBALS.update(_HELPERS)
_CACHE = {}


def compile_expr(source):
    key = source if isinstance(source, str) else None
    if key is not None and key in _CACHE:
        return _CACHE[key]
    e = Expr(source)
    if key is not None and len(_CACHE) < 20000:
        _CACHE[key] = e
    return e


def check_identifier(name, what):
    require(isinstance(name, str) and name.isidentifier() and not name.startswith("_"),
            "%s name must be an identifier without a leading underscore: %r" % (what, name))
    require(name not in RESERVED, "%s name %r collides with a built-in function or keyword" % (what, name))
    import keyword
    require(not keyword.iskeyword(name), "%s name %r is a Python keyword" % (what, name))


def truth(value, source):
    require(type(value) is bool, "predicate must be boolean, got %s: %s (= %s)" % (type(value).__name__, source, show(value)))
    return value
