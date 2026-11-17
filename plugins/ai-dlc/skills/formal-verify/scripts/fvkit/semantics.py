"""Operational semantics of an fv-model: states, initial states, action instances, observables.

A state is a tuple of values ordered by variable name. A label is (action, ((param, value), ...)).
Updates are simultaneous (every right-hand side reads the pre-state); unlisted variables keep
their value. An instance whose successor equals its pre-state is a stuttering step: it never
counts as "taken" or "enabled" for fairness, exactly like <A>_vars in TLA+.
"""
import itertools

from .expr import _items, truth
from .values import FMap, FvError, ckey, require, to_json

MAX_PERMUTATIONS = 720


class Semantics:
    def __init__(self, model, symmetry=True):
        self.model = model
        self.vars = model.variables
        self.consts = dict(model.constants)
        self.obs_names = sorted(model.observables)
        self.perms = self._permutations() if symmetry and model.symmetry else None
        self.coverage = {a.name: {"enabled": 0, "fired": 0, "state_changing": 0} for a in model.actions}

    # ---- symmetry -------------------------------------------------------------------
    def _permutations(self):
        groups = []
        for name in self.model.symmetry:
            members = sorted(self.consts[name], key=ckey)
            groups.append([dict(zip(members, p)) for p in itertools.permutations(members)])
        total = 1
        for g in groups:
            total *= len(g)
        require(total <= MAX_PERMUTATIONS, "symmetry group too large (%d permutations)" % total)
        perms = []
        for combo in itertools.product(*groups):
            m = {}
            for part in combo:
                m.update(part)
            perms.append(m)
        return perms

    @staticmethod
    def rename(v, m):
        if type(v) is str:
            return m.get(v, v)
        if type(v) is tuple:
            return tuple(Semantics.rename(x, m) for x in v)
        if type(v) is frozenset:
            return frozenset(Semantics.rename(x, m) for x in v)
        if type(v) is FMap:
            return FMap((Semantics.rename(k, m), Semantics.rename(x, m)) for k, x in v.items())
        return v

    def canon(self, state):
        """-> (canonical representative, permutation mapping state -> representative)."""
        if not self.perms:
            return state, None
        best, best_key, best_perm = None, None, None
        for perm in self.perms:
            cand = tuple(self.rename(v, perm) for v in state)
            k = ckey(cand)
            if best_key is None or k < best_key:
                best, best_key, best_perm = cand, k, perm
        return best, best_perm

    # ---- evaluation -----------------------------------------------------------------
    def env(self, state):
        e = dict(self.consts)
        e.update(zip(self.vars, state))
        for name, expr in self.model.definitions:
            e[name] = expr(e)
        return e

    def observe(self, env):
        return {k: self.model.observables[k](env) for k in self.obs_names}

    def initial_states(self, limit):
        cenv = dict(self.consts)
        choices = []
        for v in self.vars:
            kind, expr = self.model.init[v]
            val = expr(cenv)
            if kind == "in":
                options = list(_items(val))
                require(options, "init_in of %s is empty" % v)
                choices.append(options)
            else:
                choices.append([val])
        out, count = [], 0
        for combo in itertools.product(*choices):
            count += 1
            require(count <= max(limit, 1) * 4 + 1000, "too many candidate initial states")
            state = tuple(combo)
            if self.model.init_constraint is not None:
                env = self.env(state)
                if not truth(self.model.init_constraint(env), self.model.init_constraint.source):
                    continue
            out.append(state)
        require(out, "the model has no initial state")
        return out

    def bindings(self, action, env):
        params = action.params
        if not params:
            yield ()
            return

        def rec(i, scope, acc):
            if i == len(params):
                yield tuple(acc)
                return
            name, dom = params[i]
            for value in list(_items(dom(scope))):
                scope2 = dict(scope)
                scope2[name] = value
                yield from rec(i + 1, scope2, acc + [(name, value)])
        yield from rec(0, env, [])

    def apply(self, action, binding, state, env):
        """-> successor state or None when the guard is false."""
        scope = env
        if binding:
            scope = dict(env)
            scope.update(binding)
        if action.guard is not None and not truth(action.guard(scope), action.guard.source):
            return None
        if not action.updates:
            return state
        new = dict(zip(self.vars, state))
        for var, expr in action.updates.items():
            new[var] = expr(scope)
        return tuple(new[v] for v in self.vars)

    def successors(self, state, env, count=True):
        for action in self.model.actions:
            for binding in self.bindings(action, env):
                nxt = self.apply(action, binding, state, env)
                if nxt is None:
                    continue
                if count:
                    c = self.coverage[action.name]
                    c["enabled"] += 1
                    c["fired"] += 1
                    if ckey(nxt) != ckey(state):
                        c["state_changing"] += 1
                yield (action.name, binding), nxt

    def action(self, name):
        for a in self.model.actions:
            if a.name == name:
                return a
        raise FvError("unknown action: " + name)

    def step(self, state, label):
        """Replay one labelled step; FvError if it is not enabled."""
        name, binding = label
        action = self.action(name)
        env = self.env(state)
        allowed = list(self.bindings(action, env))
        require(any(ckey(b) == ckey(binding) for b in allowed),
                "parameters %s are outside the domain of %s" % (label_json(label)["params"], name))
        nxt = self.apply(action, binding, state, env)
        require(nxt is not None, "action %s is not enabled here" % label_str(label))
        return nxt

    def state_json(self, state):
        return {v: to_json(x) for v, x in zip(self.vars, state)}

    def obs_json(self, obs):
        return {k: to_json(obs[k]) for k in self.obs_names}

    def map_label(self, label, perm):
        if not perm:
            return label
        name, binding = label
        return name, tuple((p, self.rename(v, perm)) for p, v in binding)


def label_json(label):
    name, binding = label
    return {"name": name, "params": {p: to_json(v) for p, v in binding}}


def label_str(label):
    name, binding = label
    if not binding:
        return name
    return "%s(%s)" % (name, ", ".join("%s=%s" % (p, to_json(v)) for p, v in binding))


def invert(perm):
    return {v: k for k, v in perm.items()} if perm else None
