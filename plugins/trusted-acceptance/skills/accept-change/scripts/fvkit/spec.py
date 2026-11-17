"""Load and statically check fv-contract and fv-model documents.

The contract is the authoritative rule set (observables, assumptions, properties). The
model is a state machine plus a refinement mapping (`observables`) from its internal state
onto the contract vocabulary. Properties are evaluated ONLY over that vocabulary, so a model
can be refactored without touching the rules, and nobody can make a check green by editing
the model's notion of "sold".
"""
import json
from pathlib import Path

from .expr import RESERVED, check_identifier, compile_expr
from .values import FvError, digest, freeze, require

MAX_DOC_BYTES = 2 * 1024 * 1024
PROPERTY_KINDS = ("invariant", "transition", "reachable", "leads_to", "eventually", "infinitely_often")
LIVENESS_KINDS = ("leads_to", "eventually", "infinitely_often")
OBS_TYPES = ("int", "bool", "str", "set", "seq", "map", "any")
DISPOSITIONS = ("not_formalizable", "out_of_scope", "covered_by_tests", "covered_by_other_module")
MUTATION_OPS = ("set_guard", "set_update", "drop_update", "drop_action", "add_action", "set_init",
                "drop_fairness", "set_observable", "set_constant")


def _no_dupes(pairs):
    out = {}
    for k, v in pairs:
        require(k not in out, "duplicate key in document: %r" % (k,))
        out[k] = v
    return out


def load_document(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), "not a regular file: %s" % path)
    data = path.read_bytes()
    require(len(data) <= MAX_DOC_BYTES, "document exceeds 2 MiB: %s" % path)
    return parse_document(data, path.suffix, str(path))


def parse_document(data, suffix, where="document"):
    """JSON always; YAML when PyYAML is importable. Duplicate keys, floats and tags are refused."""
    require(len(data) <= MAX_DOC_BYTES, "document exceeds 2 MiB: %s" % where)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise FvError("document is not UTF-8: %s" % where) from None
    if suffix.lower() in (".yaml", ".yml"):
        try:
            import yaml
        except ImportError:
            raise FvError("PyYAML is required for YAML documents; install it or use the JSON form: %s" % where) from None

        class Loader(yaml.SafeLoader):
            pass

        def mapping(loader, node, deep=False):
            loader.flatten_mapping(node)
            return _no_dupes((loader.construct_object(k, deep=deep), loader.construct_object(v, deep=deep))
                             for k, v in node.value)
        Loader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)
        try:
            doc = yaml.load(text, Loader=Loader)  # noqa: S506 - SafeLoader subclass
        except yaml.YAMLError as error:
            raise FvError("invalid YAML in %s: %s" % (where, str(error)[:300])) from None
    else:
        try:
            doc = json.loads(text, object_pairs_hook=_no_dupes,
                             parse_constant=lambda c: (_ for _ in ()).throw(FvError("non-finite number")))
        except ValueError as error:
            raise FvError("invalid JSON in %s: %s" % (where, error)) from None
    _plain(doc, where)
    return doc


def _plain(v, where):
    """Only JSON data types (no floats, dates or YAML tags) may reach a digest."""
    if v is None or type(v) in (bool, int, str):
        return
    if isinstance(v, list):
        for x in v:
            _plain(x, where)
        return
    if isinstance(v, dict):
        for k, x in v.items():
            require(type(k) is str, "%s: object keys must be strings" % where)
            _plain(x, where)
        return
    raise FvError("%s: unsupported value of type %s (floats/dates are not allowed)" % (where, type(v).__name__))


def _keys(obj, required, optional, where):
    require(isinstance(obj, dict), where + " must be an object")
    missing = [k for k in required if k not in obj]
    unknown = [k for k in obj if k not in required and k not in optional]
    require(not missing, "%s is missing %s" % (where, missing))
    require(not unknown, "%s has unknown fields %s" % (where, unknown))


def _text(v, where):
    require(isinstance(v, str) and v.strip(), where + " must be a nonempty string")
    return v


class Property:
    __slots__ = ("id", "kind", "expr", "from_", "to", "forall", "source", "sources", "text")

    def __init__(self, raw, where):
        _keys(raw, ["id", "kind"], ["expr", "from", "to", "forall", "source", "text"], where)
        require(isinstance(raw["id"], str) and raw["id"] and all(c.isascii() and (c.isalnum() or c in "-_.") for c in raw["id"]),
                where + ": property id must be [A-Za-z0-9._-]")
        self.id = raw["id"]
        self.kind = raw["kind"]
        require(self.kind in PROPERTY_KINDS, "%s: kind must be one of %s" % (where, PROPERTY_KINDS))
        src = raw.get("source")
        require(src is None or isinstance(src, str) or (isinstance(src, list) and src and all(isinstance(x, str) for x in src)),
                where + ": source must be a requirement id or a list of ids")
        self.source = src
        self.sources = [] if src is None else [src] if isinstance(src, str) else list(src)
        self.text = raw.get("text")
        if self.kind == "leads_to":
            require("from" in raw and "to" in raw and "expr" not in raw, where + ": leads_to needs from/to (no expr)")
            self.from_, self.to, self.expr = compile_expr(raw["from"]), compile_expr(raw["to"]), None
        else:
            require("expr" in raw and "from" not in raw and "to" not in raw, where + ": %s needs expr (no from/to)" % self.kind)
            self.expr, self.from_, self.to = compile_expr(raw["expr"]), None, None
        forall = raw.get("forall") or {}
        require(isinstance(forall, dict), where + ": forall must map names to domain expressions")
        self.forall = []
        for name, dom in forall.items():
            check_identifier(name, "forall")
            self.forall.append((name, compile_expr(dom)))

    def exprs(self):
        return [e for e in (self.expr, self.from_, self.to) if e is not None]


class Contract:
    def __init__(self, doc, path=None):
        _keys(doc, ["schema_version", "kind", "id", "version", "observables", "properties"],
              ["title", "sources", "parameters", "assumptions", "description", "requirements", "dispositions"], "contract")
        require(doc["schema_version"] == 1 and doc["kind"] == "fv-contract", "unsupported contract (need schema_version 1, kind fv-contract)")
        require(type(doc["version"]) is int and doc["version"] >= 1, "contract version must be a positive integer")
        self.doc, self.path, self.id, self.version = doc, path, _text(doc["id"], "contract.id"), doc["version"]
        self.parameters = list(doc.get("parameters") or [])
        for p in self.parameters:
            check_identifier(p, "parameter")
        obs = doc["observables"]
        require(isinstance(obs, dict) and obs, "contract.observables must be a nonempty object")
        self.observables = {}
        for name, spec in obs.items():
            check_identifier(name, "observable")
            require(name not in self.parameters, "observable %r collides with a parameter" % name)
            _keys(spec, ["type"], ["description", "domain"], "observable " + name)
            require(spec["type"] in OBS_TYPES, "observable %s: type must be one of %s" % (name, OBS_TYPES))
            dom = compile_expr(spec["domain"]) if spec.get("domain") is not None else None
            if dom is not None:
                require(dom.names <= set(self.parameters), "observable %s: domain may only use parameters" % name)
            self.observables[name] = {"type": spec["type"], "domain": dom, "description": spec.get("description")}
        self.assumptions = list(doc.get("assumptions") or [])
        for i, a in enumerate(self.assumptions):
            _keys(a, ["id", "text"], ["kind", "source"], "assumption[%d]" % i)
        self.requirements_ref = doc.get("requirements")
        require(self.requirements_ref is None or (isinstance(self.requirements_ref, str) and self.requirements_ref.strip()),
                "contract.requirements must be a path to an fv-requirements document")
        self.dispositions = list(doc.get("dispositions") or [])
        for i, d in enumerate(self.dispositions):
            _keys(d, ["requirement", "status", "reason"], [], "disposition[%d]" % i)
            require(d["status"] in DISPOSITIONS, "disposition[%d].status must be one of %s" % (i, DISPOSITIONS))
            _text(d["reason"], "disposition[%d].reason" % i)
        props = doc["properties"]
        require(isinstance(props, list) and props, "contract.properties must be a nonempty list")
        self.properties = [Property(p, "property[%d]" % i) for i, p in enumerate(props)]
        ids = [p.id for p in self.properties]
        require(len(set(ids)) == len(ids), "duplicate property ids")
        vocab = set(self.parameters) | set(self.observables)
        for p in self.properties:
            bound = {n for n, _ in p.forall}
            for _, dom in p.forall:
                require(dom.names <= set(self.parameters), "property %s: forall domains may only use parameters" % p.id)
            for e in p.exprs():
                allowed = vocab | bound | ({"pre", "post"} if p.kind == "transition" else set())
                unknown = e.names - allowed
                require(not unknown, "property %s uses names outside the contract vocabulary: %s" % (p.id, sorted(unknown)))
                if p.kind == "transition":
                    import ast
                    for node in ast.walk(e.tree):
                        if isinstance(node, ast.Attribute):
                            require(node.attr in self.observables, "property %s: pre/post.%s is not an observable" % (p.id, node.attr))
        # A location-only reference (where the requirements file sits) is not part of the rules' identity:
        # a candidate under candidates/ and the adopted copy next to the model must share one digest.
        self.digest = digest({k: v for k, v in doc.items() if k != "requirements"})
        self.properties_digest = digest({"observables": doc["observables"], "properties": doc["properties"],
                                         "assumptions": doc.get("assumptions") or [], "parameters": self.parameters})

    def property(self, pid):
        for p in self.properties:
            if p.id == pid:
                return p
        raise FvError("unknown property: " + pid)

    def identity(self):
        return {"id": self.id, "version": self.version, "digest": self.digest,
                "properties_digest": self.properties_digest, "property_ids": [p.id for p in self.properties]}


class Action:
    __slots__ = ("name", "params", "guard", "updates", "description")

    def __init__(self, name, raw):
        check_identifier(name, "action")
        _keys(raw, [], ["params", "guard", "update", "description"], "action " + name)
        self.name, self.description = name, raw.get("description")
        params = raw.get("params") or {}
        require(isinstance(params, dict), "action %s: params must be an object" % name)
        compiled = {}
        for p, dom in params.items():
            check_identifier(p, "parameter of " + name)
            compiled[p] = compile_expr(dom)
        # Enumeration order: dependencies first, then by name (deterministic from content).
        order, pending = [], dict(compiled)
        while pending:
            ready = sorted(p for p, e in pending.items() if not (e.names & set(pending) - {p}))
            require(ready, "action %s: cyclic parameter domains" % name)
            require(not any(p in compiled[p].names for p in ready), "action %s: a parameter domain refers to itself" % name)
            order.append(ready[0])
            del pending[ready[0]]
        self.params = [(p, compiled[p]) for p in order]
        self.guard = compile_expr(raw["guard"]) if raw.get("guard") is not None else None
        upd = raw.get("update") or {}
        require(isinstance(upd, dict), "action %s: update must map variables to expressions" % name)
        self.updates = {v: compile_expr(e) for v, e in sorted(upd.items())}


class Model:
    def __init__(self, doc, path=None, contract=None):
        _keys(doc, ["schema_version", "kind", "id", "variables", "actions"],
              ["title", "contract", "constants", "definitions", "init_constraint", "fairness", "terminal",
               "deadlock", "observables", "model_invariants", "symmetry", "bounds", "mutants", "description",
               "assumptions"], "model")
        require(doc["schema_version"] == 1 and doc["kind"] == "fv-model", "unsupported model (need schema_version 1, kind fv-model)")
        self.doc, self.path, self.id = doc, path, _text(doc["id"], "model.id")
        self.digest = digest({k: v for k, v in doc.items() if k != "contract"})   # location-only reference excluded
        self.contract_ref = doc.get("contract")
        consts = doc.get("constants") or {}
        require(isinstance(consts, dict), "constants must be an object")
        self.constants = {}
        for k, v in consts.items():
            check_identifier(k, "constant")
            self.constants[k] = freeze(v, "constants." + k)
        variables = doc["variables"]
        require(isinstance(variables, dict) and variables, "variables must be a nonempty object")
        self.variables = sorted(variables)
        self.init = {}
        for v in self.variables:
            check_identifier(v, "variable")
            spec = variables[v]
            _keys(spec, [], ["init", "init_in", "description"], "variable " + v)
            require(("init" in spec) != ("init_in" in spec), "variable %s needs exactly one of init / init_in" % v)
            self.init[v] = ("in", compile_expr(spec["init_in"])) if "init_in" in spec else ("det", compile_expr(spec["init"]))
        defs = doc.get("definitions") or {}
        require(isinstance(defs, dict), "definitions must be an object")
        compiled = {}
        for k, e in defs.items():
            check_identifier(k, "definition")
            compiled[k] = compile_expr(e)
        self.definitions, pending = [], dict(compiled)
        while pending:
            ready = sorted(k for k, e in pending.items() if not (e.names & set(pending)))
            require(ready, "cyclic definitions: %s" % sorted(pending))
            for k in ready:
                self.definitions.append((k, compiled.pop(k)))
                del pending[k]
        actions = doc["actions"]
        require(isinstance(actions, dict) and actions, "actions must be a nonempty object")
        self.actions = [Action(n, actions[n]) for n in sorted(actions)]
        self.init_constraint = compile_expr(doc["init_constraint"]) if doc.get("init_constraint") else None
        self.terminal = compile_expr(doc["terminal"]) if doc.get("terminal") else None
        self.deadlock = doc.get("deadlock", "check")
        require(self.deadlock in ("check", "allow"), "deadlock must be check|allow")
        self.fairness = []
        for i, f in enumerate(doc.get("fairness") or []):
            _keys(f, ["action", "kind"], ["per_params", "reason"], "fairness[%d]" % i)
            require(f["kind"] in ("weak", "strong"), "fairness kind must be weak|strong")
            require(f["action"] in {a.name for a in self.actions}, "fairness refers to unknown action %s" % f["action"])
            self.fairness.append({"action": f["action"], "kind": f["kind"], "per_params": bool(f.get("per_params", False))})
        obs = doc.get("observables") or {}
        require(isinstance(obs, dict), "observables must map contract observables to expressions")
        self.observables = {k: compile_expr(e) for k, e in sorted(obs.items())}
        self.model_invariants = []
        for i, inv in enumerate(doc.get("model_invariants") or []):
            _keys(inv, ["id", "expr"], ["text"], "model_invariants[%d]" % i)
            self.model_invariants.append((inv["id"], compile_expr(inv["expr"])))
        self.symmetry = list(doc.get("symmetry") or [])
        bounds = doc.get("bounds") or {}
        _keys(bounds, [], ["max_states", "max_depth", "time_seconds"], "bounds")
        self.bounds = bounds
        self.mutants = list(doc.get("mutants") or [])
        self._names_check()
        if contract is not None:
            self.bind(contract)

    def _names_check(self):
        groups = {"constant": set(self.constants), "variable": set(self.variables),
                  "definition": {k for k, _ in self.definitions}}
        seen = {}
        for kind, names in groups.items():
            for n in names:
                require(n not in seen, "%s %r collides with %s %r" % (kind, n, seen.get(n), n))
                seen[n] = kind
        consts, state = set(self.constants), set(self.constants) | set(self.variables)
        for v, (_, e) in self.init.items():
            unknown = e.names - consts
            require(not unknown, "init of %s may only use constants; unknown %s" % (v, sorted(unknown)))
        defined = set()
        for k, e in self.definitions:
            unknown = e.names - state - defined
            require(not unknown, "definition %s uses unknown names %s" % (k, sorted(unknown)))
            defined.add(k)
        base = state | defined
        for a in self.actions:
            known = set(base)
            for p, dom in a.params:
                require(p not in base, "action %s: parameter %s shadows a constant/variable/definition" % (a.name, p))
                unknown = dom.names - known
                require(not unknown, "action %s: domain of %s uses unknown names %s" % (a.name, p, sorted(unknown)))
                known.add(p)
            for e in ([a.guard] if a.guard else []) + list(a.updates.values()):
                unknown = e.names - known
                require(not unknown, "action %s uses unknown names %s" % (a.name, sorted(unknown)))
            unknown_vars = set(a.updates) - set(self.variables)
            require(not unknown_vars, "action %s updates unknown variables %s" % (a.name, sorted(unknown_vars)))
        for label, e in [("init_constraint", self.init_constraint), ("terminal", self.terminal)] + \
                [("observable " + k, e) for k, e in self.observables.items()] + \
                [("model invariant " + k, e) for k, e in self.model_invariants]:
            if e is not None:
                unknown = e.names - base
                require(not unknown, "%s uses unknown names %s" % (label, sorted(unknown)))
        for name in self.symmetry:
            require(name in self.constants, "symmetry names an unknown constant %s" % name)
            members = self.constants[name]
            require(type(members) in (tuple, frozenset) and all(type(m) is str for m in members) and len(set(members)) == len(members),
                    "symmetry set %s must be a collection of distinct strings" % name)
            literals = set()
            for e in self._all_exprs():
                literals |= e.constants()
            clash = literals & set(members)
            require(not clash, "symmetry set %s members appear as string literals %s; symmetry would be unsound" % (name, sorted(clash)))
        ids = [i for i, _ in self.model_invariants]
        require(len(set(ids)) == len(ids), "duplicate model invariant ids")
        require(not (set(self.constants) & RESERVED), "constants collide with reserved names")

    def _all_exprs(self):
        out = [e for _, e in self.init.values()] + [e for _, e in self.definitions] + list(self.observables.values())
        out += [e for _, e in self.model_invariants] + [x for x in (self.init_constraint, self.terminal) if x]
        for a in self.actions:
            out += [d for _, d in a.params] + ([a.guard] if a.guard else []) + list(a.updates.values())
        return out

    def bind(self, contract):
        missing = set(contract.observables) - set(self.observables)
        extra = set(self.observables) - set(contract.observables)
        require(not missing, "model %s does not map contract observables %s" % (self.id, sorted(missing)))
        require(not extra, "model maps observables the contract does not declare: %s" % sorted(extra))
        params = set(contract.parameters) - set(self.constants)
        require(not params, "model %s does not define contract parameters %s" % (self.id, sorted(params)))
        self.contract = contract

    def identity(self):
        return {"id": self.id, "digest": self.digest}


def load_contract(path):
    return Contract(load_document(path), str(path))


def load_model(path, contract=None, contract_path=None):
    doc = load_document(path)
    if contract is None:
        ref = contract_path or doc.get("contract")
        require(ref, "model has no contract reference; pass --contract")
        cpath = Path(ref) if contract_path else Path(path).parent / ref
        contract = load_contract(cpath)
    return Model(doc, str(path), contract)


def model_from_doc(doc, contract):
    return Model(doc, None, contract)
