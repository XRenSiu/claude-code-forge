#!/usr/bin/env bash
# 回放取锁的两臂对照（I-104）。$1 = 仓库根，$2 = delete_lock | no_lock_history
set -u
SRC="$1"; MODE="$2"
# $1 可以是仓库根（有 plugins/ai-dlc/）也可以是插件根本身。变异自检把插件复制成
# <tmp>/mutant/ai-dlc/，那里没有 plugins/ 这一层——写死仓库布局会让基线在副本里必红，
# 而一次红基线上的变异证明什么都证明不了（smoke.sh 自己会拒绝跑）。2026-09-06。
if [ -d "$SRC/plugins/ai-dlc" ]; then PLUGIN="$SRC/plugins/ai-dlc"; else PLUGIN="$SRC"; fi
T="$(cd "$(mktemp -d)" && pwd -P)"; cd "$T" || exit 9
git init -q .; git config user.email t@t; git config user.name t
RA="plugins/ai-dlc/dogfood/ring-audit"
mkdir -p "$RA/cards" plugins/ai-dlc/skills/commit/scripts
cp "$PLUGIN/dogfood/ring-audit/replay_card_commits.sh" "$RA/"
cp "$PLUGIN/skills/commit/scripts/verify_commit.py" plugins/ai-dlc/skills/commit/scripts/
printf 'card: CARD-01\nallowed_files:\n  - "gate.py"\n  - ".done_when.lock"\n' > "$RA/cards/CARD-01.yaml"
echo "print('gate')" > gate.py
git add -A; git commit -qm "chore: base"
if [ "$MODE" = "delete_lock" ]; then
  python3 - "$RA" <<'PY'
import hashlib, json, sys
ra = sys.argv[1]
h = hashlib.sha256(open("gate.py", "rb").read()).hexdigest()
json.dump({"stage": "l5", "signed_by": "t", "signer_kind": "human",
           "signed_at": "2026-01-01T00:00:00Z",
           "files": [{"path": "gate.py", "sha256": h, "role": "gate"}]},
          open(f"{ra}/.done_when.lock", "w"), indent=2)
PY
  git add -A; git commit -qm "chore: lock it"
  git checkout -q -b feat/x
  echo "print('gate REWRITTEN')" > gate.py
  git rm -q "$RA/.done_when.lock"
  git commit -qam "fix(x): rewrite the locked gate and delete the lock

Card: CARD-01"
else
  git checkout -q -b feat/x
  echo "print('gate touched, no lock ever')" > gate.py
  git commit -qam "fix(x): touch gate with no lock in history

Card: CARD-01"
fi
git branch -q -f main "$(git rev-list --max-parents=0 HEAD)"
bash "$RA/replay_card_commits.sh" 2>&1 | python3 -c "
import json, sys
t = sys.stdin.read(); i = t.index('{'); d = json.loads(t[i:])
sys.exit(0 if d.get('ok') else 1)"
