"""Immutable model values, canonical ordering and JSON projection.

Model values are: None, bool, int, str, tuple (sequence), frozenset (set) and FMap (map).
Python treats 1 == True; canonical keys keep the types apart so two states that differ
only by bool/int never collapse into one explored state.
"""
import hashlib
import json

MAX_COLLECTION = 100000


class FvError(ValueError):
    """Any user-facing formal-verification error (bad spec, bad evidence, bad trace)."""


def require(condition, message):
    if not condition:
        raise FvError(message)


class FMap:
    """Immutable, hashable map. Iteration order is canonical (sorted by ckey)."""
    __slots__ = ("_items", "_dict", "_hash")

    def __init__(self, pairs=()):
        d = {}
        for key, value in pairs:
            d[key] = value
        require(len(d) <= MAX_COLLECTION, "map exceeds size limit")
        object.__setattr__(self, "_dict", d)
        object.__setattr__(self, "_items", tuple(sorted(d.items(), key=lambda kv: ckey(kv[0]))))
        object.__setattr__(self, "_hash", None)

    def __setattr__(self, name, value):
        raise FvError("maps are immutable; use update(m, k, v)")

    def __getitem__(self, key):
        try:
            return self._dict[key]
        except KeyError:
            raise FvError("key not in map domain: " + show(key)) from None
        except TypeError:
            raise FvError("unhashable map key") from None

    def __contains__(self, key):
        try:
            return key in self._dict
        except TypeError:
            return False

    def __iter__(self):
        return iter([k for k, _ in self._items])

    def __len__(self):
        return len(self._items)

    def __eq__(self, other):
        return isinstance(other, FMap) and ckey(self) == ckey(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        if self._hash is None:
            object.__setattr__(self, "_hash", hash(ckey(self)))
        return self._hash

    def items(self):
        return self._items

    def get(self, key, default=None):
        return self._dict.get(key, default)

    def __repr__(self):
        return "FMap(" + show(self) + ")"


def ckey(v):
    """Total, type-separated ordering key for every model value."""
    if v is None:
        return (0,)
    if v is True or v is False:
        return (1, int(v))
    if type(v) is int:
        return (2, v)
    if type(v) is str:
        return (3, v)
    if type(v) is tuple:
        return (4, tuple(ckey(x) for x in v))
    if type(v) is frozenset:
        return (5, tuple(sorted(ckey(x) for x in v)))
    if type(v) is FMap:
        return (6, tuple((ckey(k), ckey(x)) for k, x in v.items()))
    raise FvError("unsupported model value type: " + type(v).__name__)


def freeze(v, path="value"):
    """JSON/YAML data -> model value. Lists become tuples, objects become maps."""
    if v is None or v is True or v is False or type(v) in (int, str):
        return v
    if type(v) is float:
        raise FvError(path + ": floating point values are not supported (use integers)")
    if isinstance(v, (list, tuple)):
        require(len(v) <= MAX_COLLECTION, path + ": collection too large")
        return tuple(freeze(x, path) for x in v)
    if isinstance(v, (set, frozenset)):
        return frozenset(freeze(x, path) for x in v)
    if isinstance(v, dict):
        return FMap((k, freeze(x, path + "." + str(k))) for k, x in v.items())
    if isinstance(v, FMap):
        return v
    raise FvError(path + ": unsupported value " + type(v).__name__)


def to_json(v):
    """Model value -> JSON data (lossy for sets/maps; use ckey for identity)."""
    if v is None or v is True or v is False or type(v) in (int, str):
        return v
    if type(v) is tuple:
        return [to_json(x) for x in v]
    if type(v) is frozenset:
        return [to_json(x) for x in sorted(v, key=ckey)]
    if type(v) is FMap:
        if all(type(k) is str for k in v):
            return {k: to_json(x) for k, x in v.items()}
        return [[to_json(k), to_json(x)] for k, x in v.items()]
    raise FvError("unsupported model value type: " + type(v).__name__)


def from_json(v, kind="any"):
    """Trace JSON -> model value under a declared observable type."""
    if kind in ("int", "bool", "str"):
        expect = {"int": int, "bool": bool, "str": str}[kind]
        require(type(v) is expect, "expected %s, got %s" % (kind, type(v).__name__))
        return v
    if kind == "set":
        require(isinstance(v, list), "expected a JSON array for a set")
        return frozenset(from_json(x) for x in v)
    if kind == "seq":
        require(isinstance(v, list), "expected a JSON array for a sequence")
        return tuple(from_json(x) for x in v)
    if kind == "map":
        if isinstance(v, dict):
            return FMap((k, from_json(x)) for k, x in v.items())
        require(isinstance(v, list) and all(isinstance(p, list) and len(p) == 2 for p in v),
                "expected a JSON object or [[key, value], ...] for a map")
        return FMap((from_json(k), from_json(x)) for k, x in v)
    if kind == "any":
        if isinstance(v, dict):
            return FMap((k, from_json(x)) for k, x in v.items())
        return freeze(v)
    raise FvError("unknown observable type: " + str(kind))


def show(v):
    return json.dumps(to_json(v), ensure_ascii=False, sort_keys=True)


def canonical(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(data):
    return "sha256:" + hashlib.sha256(canonical(data)).hexdigest()


def sha_bytes(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def value_digest(v):
    return sha_bytes(repr(ckey(v)).encode("utf-8"))
