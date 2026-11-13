# Discovery

Survey is read-only. It enumerates tracked and nonignored untracked files in Git repositories; filesystem fallback excludes dependency/build folders. Output includes scan bounds, package-manager conflicts, project instruction/configuration paths and content hashes. It does not execute package scripts, follow external symlinks or initialize dependencies/submodules. No default package manager is invented when a lock or declaration is absent.

Read inventory sources selectively: root and module instructions, native lint/test configs, CI matrices, reusable components/services, existing feature and issue workflows. Inventory lists assets; the model explains how they relate. Do not promote an observed dependency into an architectural rule without project instructions or a confirmed decision.

The candidate digest includes Git-visible regular files and symlink targets. Installed dependencies, ignored files and submodule contents are explicitly excluded. Node/environment metadata and lockfiles supplement the digest; this is not a hermetic build attestation. Resolve unreadable configuration and truncation before treating absent assets as facts.

Use the existing document hierarchy and task system. An empty usage log means insufficient observation. Static references cannot prove a host event fired. Preserve facts, inferences and unresolved decisions in the adoption report.
