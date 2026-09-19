#!/usr/bin/env python3
"""
dos_closure.py — one definition of "what a DOS term resolves to".

`/issue --dos`, `lint_cards.py --dos` and `verify_vocabulary.py` all close the operator's
vocabulary over `dos.yaml`. Both consumers used to resolve a term against the `objects`
mapping keys ONLY, so a DOS that records the team's real word as a synonym — the canonical
`卡`/`Card` living under an object keyed `WorkUnit`, the imported qanat vocabulary
`Territory`/`Run`/`MemoryAsset` — failed closure on the very words the docs use.

v0.11.0 widened the closure a second time, for the opposite failure. A DOS is two layers:
the **core model** (`objects`, ≤7 aggregates, plus `composition` and `rules`) and the
**ubiquitous language** (`vocabulary`: every other term the team says — values, enum
members, artifacts, roles, processes, terms owned by a neighbouring context). Before
`vocabulary` existed, the ~40 real terms Judgment 1 sorted into "value" / "enum" /
"composition" / "external" lived only in `decisions.md` prose, so a card that said `AC`,
`Fingerprint` or `Finding` failed closure — or, worse, the drift sensor dropped it as
"uncorroborated" and nobody noticed. Closure now resolves the whole language:

    from dos_closure import load_closure
    c = load_closure("dos.yaml")
    c.resolve_object("Card")     -> "WorkUnit"   (object, via synonym)
    c.resolve_object("AC")       -> "AC"         (vocabulary term, kind value, of Contract)
    c.resolve_object("判据")      -> "AC"         (vocabulary synonym)
    c.resolve_object("TopicNode")-> "Topic"      (a declared *rejected* name — resolves, flagged)
    c.resolve_object("环")        -> None         (declared on Ring AND Loop: ambiguous, must qualify)
    c.resolve_rule("R001")       -> "R001"
    c.describe("判据")            -> {"canonical": "AC", "kind": "value", "layer": "vocabulary",
                                     "via": "synonym", "of": "Contract"}
    c.why_unresolved("环")        -> "ambiguous: 环 → Loop | Ring — qualify the term"
    c.unresolved(["Card", "Xyz"], kind="object")  -> ["Xyz"]

Resolution order for an object term (first hit wins; a hit in two places is AMBIGUOUS
and resolves to nothing — the closure refuses to guess which one you meant):
  1. a key of `objects`                                   (canonical, layer core)
  2. a key of `composition`                               (canonical, layer core)
  3. a key of `vocabulary`                                (canonical, layer vocabulary)
  4. a member of some entry's `synonyms:` list            (alias -> canonical)
  5. a member of some entry's `rejected_names:` list      (alias -> canonical, via=rejected;
                                                           the SKOS hiddenLabel: it closes so
                                                           the reader learns the right word,
                                                           and consumers flag it)
For a rule term:
  1. a `rules[].id`                                       (canonical)
  2. a member of that rule's `aliases:` list              (alias -> canonical id)

Synonyms are declared, never inferred: nothing here does fuzzy matching. A word that
is not written down does not resolve, which is the point of a closure check.
"""

from __future__ import annotations

# The closed set of `vocabulary.<term>.kind` values. verify_dos.py rejects anything else.
#   value     — an attribute / value object that lives on an owner (`of` required): AC, Fingerprint, Lock
#   enum      — a member of a closed set or a discriminator value (`of` required): fail, psl, card_test_fail
#   artifact  — a file / record the process produces that is not itself a composition: spec.md, g1-record.md
#   role      — a participant kind or actor: implementer, evaluator, human signer
#   process   — a named activity the team refers to as a noun: reflow, escalation, archive
#   external  — a concept OWNED by a neighbouring bounded context and referenced here (`context` required):
#               Finding, Verdict, PR, PSL
#   event     — a domain event the team names as a thing (EventStorming orange): escape defect, reflow
#   command   — an intent / instruction with a name of its own (EventStorming blue): advance, --force
#   policy    — a "whenever X, do Y" the team refers to by name (EventStorming lilac): 缺省从严
#   concept   — an abstraction that is none of the above and not an object: 三档, static_only
# Repositories / factories / services are ROLES of code, not concepts (Evans): they do not get entries.
VOCABULARY_KINDS = ("value", "enum", "event", "command", "policy", "artifact", "role", "process",
                    "external", "concept")
VOCABULARY_STATUSES = ("active", "deprecated", "proposed")


class Closure:
    def __init__(self, objects: dict, object_aliases: dict,
                 rules: set, rule_aliases: dict, source: str,
                 compositions: dict | None = None, terms: dict | None = None,
                 rejected: dict | None = None, ambiguous: dict | None = None,
                 alias_kind: dict | None = None):
        self.objects = objects                # canonical object name -> body
        self.object_aliases = object_aliases  # synonym -> canonical (objects only; kept for callers)
        self.rules = rules                    # canonical rule ids
        self.rule_aliases = rule_aliases      # alias -> canonical rule id
        self.source = source
        self.compositions = compositions or {}  # canonical composition name -> body
        self.terms = terms or {}              # canonical vocabulary term -> body
        self.rejected = rejected or {}        # rejected name -> canonical
        self.ambiguous = ambiguous or {}      # label -> sorted list of canonicals claiming it
        # every alias (synonym or rejected) -> canonical, across all three layers
        self._alias = dict(object_aliases)
        for k, v in (alias_kind or {}).items():
            self._alias.setdefault(k, v)

    # -- resolution ---------------------------------------------------------
    def _canonical(self, t):
        if t in self.objects or t in self.compositions or t in self.terms:
            return t
        return None

    def resolve_object(self, term):
        t = str(term).strip()
        if t in self.ambiguous:
            return None
        c = self._canonical(t)
        if c is not None:
            return c
        c = self._alias.get(t)
        if c is not None:
            return c
        return self.rejected.get(t)

    def resolve_rule(self, term):
        t = str(term).strip()
        if t in self.rules:
            return t
        return self.rule_aliases.get(t)

    def resolve(self, term, kind="object"):
        return self.resolve_object(term) if kind == "object" else self.resolve_rule(term)

    def unresolved(self, terms, kind="object"):
        return [t for t in terms if self.resolve(t, kind) is None]

    def why_unresolved(self, term, kind="object"):
        """A one-line reason for a None resolution — `ambiguous: …` or `undeclared`."""
        t = str(term).strip()
        if kind == "object" and t in self.ambiguous:
            return f"ambiguous: {t} → {' | '.join(self.ambiguous[t])} — qualify the term"
        return "undeclared"

    def via_synonym(self, term, kind="object"):
        """True when the term resolved only because a synonym (or rejected name) was declared."""
        t = str(term).strip()
        if kind == "object":
            return self._canonical(t) is None and (t in self._alias or t in self.rejected)
        return t not in self.rules and t in self.rule_aliases

    def via_rejected(self, term):
        """True when the term is a declared *rejected* name — it closes, but should not be used."""
        t = str(term).strip()
        return self._canonical(t) is None and t not in self._alias and t in self.rejected

    def layer_of(self, canonical):
        if canonical in self.objects:
            return "objects"
        if canonical in self.compositions:
            return "composition"
        if canonical in self.terms:
            return "vocabulary"
        return None

    def kind_of(self, canonical):
        if canonical in self.objects:
            return "object"
        if canonical in self.compositions:
            return "composition"
        body = self.terms.get(canonical)
        if isinstance(body, dict):
            return str(body.get("kind") or "concept")
        return None

    def describe(self, term):
        """Everything a consumer needs to say WHY a word closed (or did not).

        {"canonical", "layer", "kind", "via": canonical|synonym|rejected|None, "of", "status"}
        `canonical` is None when the word does not close; `why` then carries the reason.
        """
        t = str(term).strip()
        canon = self.resolve_object(t)
        if canon is None:
            return {"term": t, "canonical": None, "layer": None, "kind": None, "via": None,
                    "of": None, "status": None, "why": self.why_unresolved(t)}
        via = "canonical" if self._canonical(t) == canon else ("rejected" if self.via_rejected(t) else "synonym")
        body = self.terms.get(canon) if canon in self.terms else None
        return {"term": t, "canonical": canon, "layer": self.layer_of(canon),
                "kind": self.kind_of(canon), "via": via,
                "of": (body or {}).get("of") if isinstance(body, dict) else None,
                "status": (body or {}).get("status", "active") if isinstance(body, dict) else "active",
                "why": None}

    def vocabulary(self, kind="object"):
        """The declared vocabulary as `label -> (canonical, kind)` — canonical names AND aliases.

        `resolve_*` answers "does this word close?"; this answers "which words ARE the
        contract?". `verify_vocabulary.py` needs the second question to say what an
        unresolved term is CLOSE TO, and to report ontology entries no artifact uses.
        Keeping it here means both questions read the same `objects` / `composition` /
        `vocabulary` / `rules` shape — a second parser living in the sensor is how the
        sensor and the gate start disagreeing about what a term is.

        kind values in the result: "object" (objects layer), "composition", the term's
        declared vocabulary kind (value / enum / …), or "rule". Rejected names are included
        (they are words the contract knows about) under their canonical's kind.
        """
        out = {}
        if kind in ("object", "both"):
            for name in self.objects:
                out[name] = (name, "object")
            for name in self.compositions:
                out.setdefault(name, (name, "composition"))
            for name in self.terms:
                out.setdefault(name, (name, self.kind_of(name)))
            for alias, canon in self._alias.items():
                out.setdefault(alias, (canon, self.kind_of(canon)))
            for alias, canon in self.rejected.items():
                out.setdefault(alias, (canon, self.kind_of(canon)))
        if kind in ("rule", "both"):
            for rid in self.rules:
                out[rid] = (rid, "rule")
            for alias, canon in self.rule_aliases.items():
                out.setdefault(alias, (canon, "rule"))
        return out

    def variants_of(self, canonical):
        """canonical + every declared synonym / rejected name that resolves to it."""
        out = [canonical]
        out += [a for a, c in self._alias.items() if c == canonical and a not in out]
        out += [a for a, c in self.rejected.items() if c == canonical and a not in out]
        return out

    @property
    def object_names(self):
        return set(self.objects)

    @property
    def rule_ids(self):
        return set(self.rules)

    @property
    def term_names(self):
        return set(self.terms)


def _items(mapping_or_list):
    if isinstance(mapping_or_list, dict):
        return [(str(k), v if isinstance(v, dict) else {}) for k, v in mapping_or_list.items() if k]
    out = []
    for o in (mapping_or_list or []):
        if isinstance(o, dict) and o.get("name"):
            out.append((str(o["name"]), o))
    return out


def closure_from_dos(dos: dict, source: str = "<dict>") -> Closure:
    dos = dos or {}
    objects = dict(_items(dos.get("objects") or {}))
    compositions = dict(_items(dos.get("composition") or {}))
    terms = dict(_items(dos.get("vocabulary") or {}))

    # label -> set of canonicals claiming it, across the three layers and both alias fields.
    claims: dict[str, set] = {}
    rejected_claims: dict[str, set] = {}
    object_aliases: dict[str, str] = {}

    def claim(label, canon, rejected=False):
        label = str(label).strip()
        if not label:
            return
        (rejected_claims if rejected else claims).setdefault(label, set()).add(canon)

    for layer in (objects, compositions, terms):
        for name, body in layer.items():
            for syn in (body.get("synonyms") or []):
                if syn:
                    claim(syn, name)
                    if layer is objects:
                        object_aliases.setdefault(str(syn).strip(), name)
            for rej in (body.get("rejected_names") or []):
                if rej:
                    claim(rej, name, rejected=True)

    canonical_names = set(objects) | set(compositions) | set(terms)
    ambiguous: dict[str, list] = {}
    alias_kind: dict[str, str] = {}
    rejected: dict[str, str] = {}
    for label, canons in claims.items():
        if label in canonical_names:
            # a synonym that is also somebody's canonical key: the key wins, the synonym is a
            # conflict for verify_dos.py to report, not for the closure to arbitrate
            if canons != {label}:
                ambiguous[label] = sorted(canons | {label})
            continue
        if len(canons) > 1:
            ambiguous[label] = sorted(canons)
        else:
            alias_kind[label] = next(iter(canons))
    for label, canons in rejected_claims.items():
        if label in canonical_names or label in alias_kind:
            continue  # a word cannot be both the right name and a rejected one; verify_dos reports it
        if len(canons) > 1 or label in ambiguous:
            ambiguous[label] = sorted(canons | set(ambiguous.get(label, [])))
        else:
            rejected[label] = next(iter(canons))
    # an object alias that turned out ambiguous is not an object alias
    for label in list(object_aliases):
        if label in ambiguous:
            del object_aliases[label]

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
    return Closure(objects, object_aliases, rules, rule_aliases, source,
                   compositions=compositions, terms=terms, rejected=rejected,
                   ambiguous=ambiguous, alias_kind=alias_kind)


def load_closure(path) -> Closure:
    import yaml
    with open(path, encoding="utf-8") as f:
        return closure_from_dos(yaml.safe_load(f) or {}, str(path))
