"""Two-party arming tests (src/live/arming.py + the armed spine assembly).

What is pinned: the token hash check, the certified-commit provenance rule (only
config/arming.yaml may differ between the certified commit and HEAD), fail-closed loading,
and that build_shadow_instrument's armed variant actually arms ONLY on the exact token.
The DTC logon leg is on-box territory (dtc_surface_forcetest) — not re-proven here.
"""
from __future__ import annotations

import hashlib

import pytest

from src.live.arming import (
    ArmingAuthorization,
    ArmingError,
    load_authorization,
    provenance_error,
    token_matches,
)
from src.live.route_b import build_shadow_instrument

WORD = "correct horse battery staple"
AUTH = ArmingAuthorization(token_sha256=hashlib.sha256(WORD.encode()).hexdigest(),
                           armed_sha="a" * 40, account="LUCID-FUNDED-1")


# ---- token ------------------------------------------------------------------
def test_token_exact_match_only():
    assert token_matches(WORD, AUTH)
    assert not token_matches(WORD + " ", AUTH)
    assert not token_matches("wrong", AUTH)
    assert not token_matches("", AUTH)


# ---- provenance -------------------------------------------------------------
def test_head_at_certified_commit_is_clean():
    assert provenance_error(AUTH, head="a" * 40, changed_files=[]) == ""


def test_authorization_commit_alone_is_tolerated():
    assert provenance_error(AUTH, head="b" * 40,
                            changed_files=["config/arming.yaml"]) == ""


def test_any_code_after_certification_refuses():
    err = provenance_error(AUTH, head="b" * 40,
                           changed_files=["config/arming.yaml", "src/canon/spine.py"])
    assert "spine.py" in err and "re-certify" in err


# ---- loading (fail closed) ---------------------------------------------------
def test_missing_authorization_file_refuses(tmp_path):
    with pytest.raises(ArmingError, match="not issued one"):
        load_authorization(tmp_path / "arming.yaml")


def test_incomplete_authorization_refuses(tmp_path):
    p = tmp_path / "arming.yaml"
    p.write_text(f"token_sha256: {AUTH.token_sha256}\narmed_sha: {'a' * 40}\n")  # no account
    with pytest.raises(ArmingError, match="account"):
        load_authorization(p)


def test_roundtrip_load(tmp_path):
    p = tmp_path / "arming.yaml"
    p.write_text(f"token_sha256: {AUTH.token_sha256}\n"
                 f"armed_sha: {AUTH.armed_sha}\naccount: {AUTH.account}\n")
    assert load_authorization(p) == AUTH


# ---- the armed assembly ------------------------------------------------------
class _MockBroker:
    def submit_bracket(self, i):
        return "ref-1"

    def order_status(self, ref):
        return {}

    def position(self, account):
        return 0

    def flatten(self, account):
        pass

    def cancel_all(self, account):
        pass


def test_armed_instrument_arms_only_on_the_exact_token(tmp_path):
    inst = build_shadow_instrument(tmp_path, account=AUTH.account,
                                   broker=_MockBroker(), arm_token=WORD)
    assert inst.spine.armed is False                     # boots disarmed even with a broker
    assert inst.spine.arm("wrong") is False and inst.spine.armed is False
    assert inst.spine.arm(WORD) is True and inst.spine.armed is True


def test_default_build_remains_shadow_and_cannot_route(tmp_path):
    inst = build_shadow_instrument(tmp_path)             # no broker, no token: unchanged
    assert inst.spine.armed is False
    with pytest.raises(AssertionError):                  # _NoBroker: structurally orderless
        inst.spine.broker.submit_bracket(None)


# ---- working tree (the box-edit hole) ---------------------------------------
# `git diff <sha>..HEAD` compares COMMITS. A tracked file edited on the box and never
# committed leaves HEAD == armed_sha, so the commit provenance check passes while the
# process runs code nobody certified. These pin the closure against REAL git rather than
# a mock, because the bug lived in exactly the gap between what git reports and what was
# assumed it reported.
import subprocess

from src.live.arming import verify_for_arming, working_tree_changes


def _repo(tmp_path):
    def g(*a):
        subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True)
    g("init", "-q")
    g("config", "user.email", "t@t")
    g("config", "user.name", "t")
    (tmp_path / "code.py").write_text("THRESHOLD = 2\n")
    (tmp_path / ".gitignore").write_text("output/\n")
    g("add", "-A")
    g("commit", "-qm", "base")
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmp_path,
                         capture_output=True, text=True).stdout.strip().lower()
    return g, sha


def test_clean_tree_reports_nothing(tmp_path):
    _repo(tmp_path)
    assert working_tree_changes(tmp_path) == []


def test_uncommitted_edit_to_tracked_file_is_seen(tmp_path):
    _repo(tmp_path)
    (tmp_path / "code.py").write_text("THRESHOLD = 20\n")     # the box edit
    assert working_tree_changes(tmp_path) == ["code.py"]


def test_untracked_file_is_not_a_refusal(tmp_path):
    _repo(tmp_path)
    (tmp_path / "scratch.log").write_text("noise\n")
    assert working_tree_changes(tmp_path) == []


def test_staged_but_uncommitted_is_seen(tmp_path):
    g, _ = _repo(tmp_path)
    (tmp_path / "code.py").write_text("THRESHOLD = 20\n")
    g("add", "code.py")
    assert working_tree_changes(tmp_path) == ["code.py"]


def test_dirty_tree_refuses_even_at_the_certified_commit():
    """The exact hole: HEAD IS the certified commit, so the old check passed."""
    err = provenance_error(AUTH, head="a" * 40, changed_files=[],
                           dirty_files=["src/canon/spine.py"])
    assert "uncommitted" in err and "spine.py" in err


def test_dirty_authorization_file_gets_no_exemption():
    """config/arming.yaml may differ as a COMMIT; uncommitted it means a hash typed on the
    box, which is the two-party mechanic being bypassed."""
    err = provenance_error(AUTH, head="a" * 40, changed_files=[],
                           dirty_files=["config/arming.yaml"])
    assert "uncommitted" in err


def test_verify_refuses_end_to_end_on_a_box_edit(tmp_path):
    g, sha = _repo(tmp_path)
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "arming.yaml").write_text(
        f'token_sha256: "{AUTH.token_sha256}"\narmed_sha: "{sha}"\naccount: "X"\n')
    g("add", "-A")
    g("commit", "-qm", "authorize")
    auth_path = tmp_path / "config" / "arming.yaml"
    verify_for_arming(WORD, repo=tmp_path, path=auth_path)      # clean -> arms
    (tmp_path / "code.py").write_text("THRESHOLD = 20\n")       # now edit on the box
    with pytest.raises(ArmingError, match="uncommitted"):
        verify_for_arming(WORD, repo=tmp_path, path=auth_path)
