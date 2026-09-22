#!/usr/bin/env python3
"""sync_issue.py 的对账变异证明：九个场景，每一个都必须按预期给出 / 不给出漂移。

为什么要变异证明而不是跑一次看看：这道对账是「issue 说的还是不是真的」的**唯一**机械检查，
它最容易坏成两种样子——报一切（人学会忽略它）或什么都不报（人以为在同步）。
两种坏法从一次成功的运行里都看不出来。

用法：sync_issue_reconcile.py <sync_issue.py 的路径>   # exit 0 = 九个场景全对
"""
import importlib.util as iu
import os
import subprocess
import sys
import tempfile

SHA = "abcdef1234567890" + "0" * 48


def main():
    if len(sys.argv) != 2:
        sys.stderr.write(__doc__)
        return 2
    spec = iu.spec_from_file_location("sync_issue", sys.argv[1])
    m = iu.module_from_spec(spec)
    spec.loader.exec_module(m)

    repo = tempfile.mkdtemp()
    run = lambda *c: subprocess.run(c, cwd=repo, capture_output=True)
    run("git", "init", "-q")
    run("git", "config", "user.email", "t@t")
    run("git", "config", "user.name", "t")
    with open(os.path.join(repo, "c.yaml"), "w") as f:
        f.write("x: 1\n")
    run("git", "add", "c.yaml")
    run("git", "commit", "-qm", "c")
    with open(os.path.join(repo, "untracked.yaml"), "w") as f:  # 存在但没入库
        f.write("x: 1\n")

    dw = {"acceptance": [{"id": "AC-001-a", "req": "REQ-001"}, {"id": "AC-002-a", "req": "REQ-001"}]}
    lock = {"files": [{"path": "c.yaml", "sha256": SHA, "role": "contract"}]}
    lock_untracked = {"files": [{"path": "untracked.yaml", "sha256": SHA, "role": "contract"}]}
    paths = {"repo": repo}

    cases = [
        # 对得上的：一条漂移都不许报，否则人会学会忽略这道检查
        ("in-sync, 8-char hash prefix", "AC-001-a AC-002-a c.yaml `abcdef12…`", lock, [], 0),
        ("in-sync, full 64-char hash", "AC-001-a AC-002-a c.yaml `%s`" % SHA, lock, [], 0),
        # 冻结前的旧哈希：明说了是旧值就是变更史，没说就是会误导人的现值
        ("stale hash presented as current", "AC-001-a AC-002-a c.yaml `79cf0ebe…`", lock, [], 1),
        ("stale hash marked superseded", "AC-001-a AC-002-a c.yaml `abcdef12…`（原签字版 `79cf0ebe…` 已被 supersede）", lock, [], 0),
        # 判据两侧的 AC 集合必须一致，任一方向的差都是「两份说法」
        ("body names an AC the contract lacks", "AC-001-a AC-002-a AC-009-z c.yaml `abcdef12…`", lock, [], 1),
        ("contract has an AC the body lacks", "AC-001-a c.yaml `abcdef12…`", lock, [], 1),
        # 最重的一条：被签住的东西不入库，那个签名没人能核对
        ("a locked file is not in git", "AC-001-a AC-002-a untracked.yaml `abcdef12…`", lock_untracked, [], 1),
        ("the cards dir is not in git", "AC-001-a AC-002-a c.yaml `abcdef12…`", lock, ["untracked.yaml"], 1),
        # 读不到 = 没检，不是通过
        ("the issue body could not be read", None, lock, [], 1),
    ]
    bad = 0
    for name, body, lk, extra, want in cases:
        drift, notes = m.reconcile(body, dw, lk, paths, extra)
        got = 1 if drift else 0
        if got != want:
            bad += 1
            sys.stderr.write("FAIL %s — want drift=%d got %d: %s\n" % (name, want, got, drift[:2]))
    if bad:
        sys.stderr.write("sync_issue reconcile: %d/%d 场景不符\n" % (bad, len(cases)))
        return 1
    print("sync_issue reconcile: %d/%d 场景全对" % (len(cases), len(cases)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
