#!/usr/bin/env bash
# sync_issue.py 的发帖纪律，用一个假的 gh 记账来证，不靠读源码：
#   ① 不给 --post 时，一次网络写都不许发生（发帖是对外副作用，默认不发）
#   ② 给了 --post 发一条
#   ③ 再给一次 --post 是**改那条**，不是再发一条（否则每次 advance 都灌一层楼）
# 用法：sync_issue_post_optin.sh <sync_issue.py 的路径>
set -u
SI="${1:?用法: sync_issue_post_optin.sh <sync_issue.py>}"
# run() 会 cd 进临时仓库，相对路径在那里就不成立了
SI="$(cd "$(dirname "$SI")" && pwd)/$(basename "$SI")"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
LOG="$T/gh.calls"; STORE="$T/comments.json"; : > "$LOG"; echo '[]' > "$STORE"

mkdir -p "$T/bin"
cat > "$T/bin/gh" <<'STUB'
#!/usr/bin/env bash
# 假 gh：记每一次调用，并把「发过的评论」存在 $GH_STORE 里，好让改帖那一路有东西可改。
echo "$*" >> "$GH_LOG"
last="${@: -1}"
case "$1 $2" in
  "repo view")    echo "o/r" ;;
  "issue view")   echo "AC-001-a 见 c.yaml" ;;
  "issue comment")
      # 形如 issue comment 1 --repo o/r --body-file <f>；正文按真的读文件，不走环境变量
      python3 -c "
import json,sys
store, bf = sys.argv[1], sys.argv[2]
d = json.load(open(store))
d.append({'id': 101, 'body': open(bf, encoding='utf-8').read()})
json.dump(d, open(store, 'w'))
" "$GH_STORE" "$last"
      echo "https://example/comment/101" ;;
  "api repos/o/r/issues/1/comments")
      # --jq 形如 `.[] | select(.body | contains("<marker>")) | .id`
      python3 -c "
import json,re,sys
d = json.load(open(sys.argv[1])); jq = sys.argv[2]
m = re.search(r'contains\((\".*?\")\)', jq)
needle = json.loads(m.group(1)) if m else None
for c in d:
    if needle and needle in c['body']: print(c['id'])
" "$GH_STORE" "$last" ;;
  "api -X")       echo "https://example/comment/101" ;;
  *)              : ;;
esac
STUB
chmod +x "$T/bin/gh"

R="$T/repo"; mkdir -p "$R/.aidlc/s"
git -C "$R" init -q; git -C "$R" config user.email t@t; git -C "$R" config user.name t
cat > "$R/.aidlc/s/state.json" <<'J'
{"version":1,"slug":"s","title":"t","track":"task","stage":"cards","gates":{},"intake":{"size":"M"}}
J
printf 'schema: 2\nfeature: f\nacceptance:\n  - {id: AC-001-a, req: REQ-001, kind: mechanical, observe: "route:GET /x"}\n' \
  > "$R/.aidlc/s/done_when.yaml"

run() { ( cd "$R" && GH_LOG="$LOG" GH_STORE="$STORE" PATH="$T/bin:$PATH" python3 "$SI" 1 --repo o/r --root .aidlc --slug s "$@" ); }

fail() { echo "FAIL: $1" >&2; exit 1; }

# ① 裸跑：不许有任何写
run --out "$T/a.md" >/dev/null 2>&1
grep -q "issue comment" "$LOG" && fail "没给 --post 却发了帖"
grep -q "\-X PATCH" "$LOG"     && fail "没给 --post 却改了帖"
[ -s "$T/a.md" ] || fail "--out 没写出正文"
grep -q "aidlc:sync slug=s stage=cards" "$T/a.md" || fail "正文里没有 stage 标记"

# ② 第一次 --post：发一条
run --post >/dev/null 2>&1
grep -q "issue comment" "$LOG" || fail "--post 没发帖"
n1=$(grep -c "issue comment" "$LOG")
[ "$n1" = 1 ] || fail "第一次 --post 发了 ${n1} 条"

# ③ 第二次 --post：改，不是再发
run --post >/dev/null 2>&1
n2=$(grep -c "issue comment" "$LOG")
[ "$n2" = 1 ] || fail "第二次 --post 又发了一条（共 ${n2}），没走改帖"
grep -q "\-X PATCH" "$LOG" || fail "第二次 --post 没改帖"

echo "sync_issue post: 裸跑零写 · 首次发帖 · 再跑改帖"
