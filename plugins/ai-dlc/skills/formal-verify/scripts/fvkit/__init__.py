"""fvkit — self-contained formal verification kit (Python standard library only).

Canonical source: plugins/trusted-acceptance/skills/accept-change/scripts/fvkit.
AI-DLC ships a byte-identical copy (plugins/ai-dlc/skills/formal-verify/scripts/fvkit) so
each installed plugin closes its own loop. Results are local_advisory evidence; they never
grant acceptance, merge or release authority by themselves.
"""
VERSION = "1.4.1"
