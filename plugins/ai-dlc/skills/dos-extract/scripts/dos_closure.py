#!/usr/bin/env python3
"""
dos_closure.py — one definition of "what a DOS term resolves to".

`/issue --dos` and `lint_cards.py --dos` both close the operator's vocabulary over
`dos.yaml`. Both used to resolve a term against the `objects` mapping keys ONLY, so a
DOS that records the team's real word as a synonym — the canonical `卡`/`Card` living
under an object keyed `WorkUnit`, the imported qanat vocabulary `Territory`/`Run`/
`MemoryAsset` — failed closure on the very words the docs use, and the operator had to
either rename the domain or point the linter at a different file by hand.

This module is the single resolver both consumers import, so "closure" means the same
thing on both sides of the seam. It is import-only; it has no CLI.

    from dos_closure import load_closure
    c = load_closure("dos.yaml")
    c.resolve_object("Card")     -> "WorkUnit"   (canonical name, or None)
    c.resolve_rule("R001")       -> "R001"
    c.unresolved(["Card", "Xyz"], kind="object")  -> ["Xyz"]

Resolution order for an object term:
  1. a key of `objects`                                   (canonical)
  2. a member of some object's `synonyms:` list           (alias -> canonical)
For a rule term:
  1. a `rules[].id`                                       (canonical)
  2. a member of that rule's `aliases:` list              (alias -> canonical id)

Synonyms are declared, never inferred: nothing here does fuzzy matching. A word that
is not written down does not resolve, which is the point of a closure check.
"""

from __future__ import annotations


class Closure:
    def __init__(self, objects: dict, object_aliases: dict,
                 rules: set, rule_aliases: dict, source: str):
        self.objects = objects              # canonical name -> object body
        self.object_aliases = object_aliases  # synonym -> canonical name
        self.rules = rules                  # canonical rule ids
        self.rule_aliases = rule_aliases    # alias -> canonical rule id
        self.source = source

    # -- resolution ---------------------------------------------------------
    def resolve_object(self, term):
        t = str(term).strip()
        if t in self.objects:
            return t
        return self.object_aliases.get(t)

    def resolve_rule(self, term):
        t = str(term).strip()
        if t in self.rules:
            return t
        return self.rule_aliases.get(t)

    def resolve(self, term, kind="object"):
        return self.resolve_object(term) if kind == "object" else self.resolve_rule(term)

    def unresolved(self, terms, kind="object"):
        return [t for t in terms if self.resolve(t, kind) is None]

    def via_synonym(self, term, kind="object"):
        """True when the term resolved only because a synonym was declared."""
        t = str(term).strip()
        if kind == "object":
            return t not in self.objects and t in self.object_aliases
        return t not in self.rules and t in self.rule_aliases

    def vocabulary(self, kind="object"):
        """The declared vocabulary as `label -> (canonical, kind)` — canonical names AND synonyms.

        `resolve_*` answers "does this word close?"; this answers "which words ARE the
        contract?". `verify_vocabulary.py` needs the second question to say what an
        unresolved term is CLOSE TO, and to report ontology entries no artifact uses.
        Keeping it here means both questions read the same `objects` / `rules` shape —
        a second parser living in the sensor is how the sensor and the gate start
        disagreeing about what a term is.
        """
        out = {}
        if kind in ("object", "both"):
            for name in self.objects:
                out[name] = (name, "object")
            for alias, canon in self.object_aliases.items():
                out.setdefault(alias, (canon, "object"))
        if kind in ("rule", "both"):
            for rid in self.rules:
                out[rid] = (rid, "rule")
            for alias, canon in self.rule_aliases.items():
                out.setdefault(alias, (canon, "rule"))
        return out

    @property
    def object_names(self):
        return set(self.objects)

    @property
    def rule_ids(self):
        return set(self.rules)


def closure_from_dos(dos: dict, source: str = "<dict>") -> Closure:
    dos = dos or {}
    raw_objects = dos.get("objects") or {}
    objects, object_aliases = {}, {}
    if isinstance(raw_objects, dict):
        items = list(raw_objects.items())
    else:
        items = [(o.get("name"), o) for o in raw_objects if isinstance(o, dict)]
    for name, body in items:
        if not name:
            continue
        name = str(name)
        objects[name] = body if isinstance(body, dict) else {}
        for syn in (objects[name].get("synonyms") or []):
            if syn:
                object_aliases.setdefault(str(syn).strip(), name)

    rules, rule_aliases = set(), {}
    for r in (dos.get("rules") or []):
        if isinstance(r, dict):
            rid = r.get("id")
            if not rid:
                continue
            rid = str(rid).strip()
            rules.add(rid)
            for al in (r.get("aliases") or []):
                if al:
                    rule_aliases.setdefault(str(al).strip(), rid)
        elif isinstance(r, str):
            rules.add(r.strip())
    return Closure(objects, object_aliases, rules, rule_aliases, source)


def load_closure(path) -> Closure:
    import yaml
    with open(path, encoding="utf-8") as f:
        return closure_from_dos(yaml.safe_load(f) or {}, str(path))
