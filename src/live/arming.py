"""Two-party arming — the mechanism behind PROMOTION-GATE's "neither party arms alone".

The gate doc's sign-off is procedural (Pat's written confirmation, then Angus's token). This
module is the MECHANICAL half, built so neither procedure can be skipped or faked:

  * ANGUS's side lives in GIT: `config/arming.yaml` carries the SHA-256 of the arming token
    phrase, the exact COMMIT that was certified, and the funded account string. Angus's agent
    commits it only after Pat's written confirmation; Pat never knows the phrase from the repo
    (only its hash is on the box).
  * PAT's side lives on the BOX: `canon_run --arm` prompts for the phrase (or reads ARM_TOKEN
    from the environment) and presents it. Without Angus's word, the hash cannot be matched;
    without Pat at the box, the word is inert.
  * The COMMIT is enforced, not trusted: the running HEAD must be the certified commit, or
    differ from it ONLY in `config/arming.yaml` itself (the authorization commit necessarily
    lands after the certified one). Any other file in that diff means code changed after
    certification -> refuse to arm (PROMOTION-GATE §E: any code change is a stop-and-review).
  * The WORKING TREE is enforced too. `git diff <sha>..HEAD` compares COMMITS, so a tracked
    file edited on the box and never committed is invisible to it: HEAD still equals
    armed_sha, the provenance check passes, and the process arms while running code nobody
    certified. Python loads the edited file at import, so the edit IS what trades. This is
    the one path by which uncertified code could reach an armed run, and it is closed here
    (`working_tree_changes`) rather than left to operator discipline.

    Scope, stated rather than implied: this refuses on any change to a TRACKED file
    (modified, staged, deleted, renamed, unmerged). Untracked files are NOT a refusal —
    build outputs, logs and journals are untracked by design on the box and refusing on
    them would make the check so noisy an operator would route around it. A new untracked
    module that shadows an import therefore remains a residual hole; it is a much narrower
    one than editing a tracked file in place, and closing it belongs with a packaging
    change, not here.

Every check fails CLOSED with a distinct, human-readable reason. A refused arm never falls
back to a shadow run — an operator who typed --arm must not believe a disarmed process is
armed, so refusal is a hard exit in the caller.
"""
from __future__ import annotations

import hashlib
import hmac
import subprocess
from dataclasses import dataclass
from pathlib import Path

ARMING_FILE = Path("config/arming.yaml")
#: the only path allowed to differ between the certified commit and the running HEAD
_ALLOWED_POST_CERT_PATHS = {"config/arming.yaml"}


class ArmingError(RuntimeError):
    """Raised when arming must be refused. The message is the reason, verbatim."""


@dataclass(frozen=True)
class ArmingAuthorization:
    token_sha256: str          # hex digest of the token phrase Angus issued
    armed_sha: str             # the certified commit the token authorizes
    account: str               # the funded trade account the armed run must use


def load_authorization(path: str | Path = ARMING_FILE) -> ArmingAuthorization:
    """Read Angus's committed authorization. Missing file or field = no authorization exists
    = arming refused — absence is the disarmed state, never a default."""
    import yaml
    p = Path(path)
    if not p.exists():
        raise ArmingError(f"no arming authorization on file ({p}) — Angus has not issued one")
    raw = yaml.safe_load(p.read_text()) or {}
    missing = [k for k in ("token_sha256", "armed_sha", "account") if not raw.get(k)]
    if missing:
        raise ArmingError(f"arming authorization incomplete — missing {missing}")
    return ArmingAuthorization(token_sha256=str(raw["token_sha256"]).strip().lower(),
                               armed_sha=str(raw["armed_sha"]).strip().lower(),
                               account=str(raw["account"]).strip())


def token_matches(token: str, auth: ArmingAuthorization) -> bool:
    """Constant-time comparison of the presented phrase against the committed hash."""
    presented = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return hmac.compare_digest(presented, auth.token_sha256)


# --------------------------------------------------------------------------- git provenance
def _git(args: list[str], repo: Path) -> str:
    r = subprocess.run(["git", *args], capture_output=True, text=True, cwd=repo, timeout=15)
    if r.returncode != 0:
        raise ArmingError(f"git {' '.join(args)} failed: {r.stderr.strip() or 'unknown error'}")
    return r.stdout.strip()


def head_sha(repo: str | Path = ".") -> str:
    return _git(["rev-parse", "HEAD"], Path(repo)).lower()


def files_changed_since(sha: str, repo: str | Path = ".") -> list[str]:
    out = _git(["diff", "--name-only", f"{sha}..HEAD"], Path(repo))
    return [line.strip() for line in out.splitlines() if line.strip()]


def working_tree_changes(repo: str | Path = ".") -> list[str]:
    """Tracked files that differ from HEAD right now — staged, unstaged, deleted or renamed.

    `git status --porcelain` reports `XY <path>`; `??` is untracked and is deliberately
    excluded (see the module docstring). Renames appear as `R  old -> new`; the destination
    is the informative half, so that is what is reported.

    Parsed by SPLITTING, not by column offset: `_git` strips its stdout, which silently eats
    the leading space of an unstaged `' M path'` line and shifts every column by one. A
    fixed-offset parse looks correct against staged changes and truncates unstaged ones."""
    out = _git(["status", "--porcelain"], Path(repo))
    changed: list[str] = []
    for line in out.splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or parts[0] == "??":
            continue
        path = parts[1].strip()
        if " -> " in path:                      # rename: report the destination
            path = path.split(" -> ", 1)[1].strip()
        changed.append(path.strip('"'))
    return changed


def provenance_error(auth: ArmingAuthorization, *, head: str,
                     changed_files: list[str], dirty_files: list[str] | None = None) -> str:
    """'' when the running code IS the certified code; otherwise the refusal reason.

    head == armed_sha is the clean case FOR THE COMMIT. Otherwise the only tolerated
    difference is the authorization file itself — the commit that carries Angus's token hash
    necessarily lands after the certified commit, and must touch nothing else.

    `dirty_files` is checked FIRST and admits no exemption, not even config/arming.yaml: an
    uncommitted authorization means someone typed a hash into the box, which is precisely the
    two-party mechanic being bypassed. A clean commit history says nothing about what is on
    disk, and what is on disk is what Python imports and trades."""
    dirty = list(dirty_files or [])
    if dirty:
        return (f"the working tree has uncommitted changes to {len(dirty)} tracked file(s): "
                f"{dirty[:10]} — the running code is NOT the certified commit even though "
                f"HEAD says {head[:12]}. Commit and re-certify, or `git checkout --` them")
    if head == auth.armed_sha:
        return ""
    smuggled = [f for f in changed_files if f not in _ALLOWED_POST_CERT_PATHS]
    if smuggled:
        return (f"HEAD {head[:12]} is not the certified commit {auth.armed_sha[:12]} and the "
                f"diff touches code, not just the authorization: {smuggled[:10]} — "
                "re-certify at this commit or check out the certified one")
    return ""


def verify_for_arming(token: str, *, repo: str | Path = ".",
                      path: str | Path = ARMING_FILE) -> ArmingAuthorization:
    """The one call the runner makes. Returns the authorization when EVERY check passes;
    raises ArmingError with the exact reason otherwise."""
    auth = load_authorization(path)
    if not token_matches(token, auth):
        raise ArmingError("token phrase does not match the committed authorization")
    head = head_sha(repo)
    err = provenance_error(auth, head=head,
                           changed_files=files_changed_since(auth.armed_sha, repo),
                           dirty_files=working_tree_changes(repo))
    if err:
        raise ArmingError(err)
    return auth
