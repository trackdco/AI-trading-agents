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
    verify_for_arming,
)
from src.live.route_b import build_shadow_instrument

WORD = "correct horse battery staple"
AUTH = ArmingAuthorization(token_sha256=hashlib.sha256(WORD.encode()).hexdigest(),
                           armed_sha="a" * 40, account="LUCID-FUNDED-1",
                           entrypoint="scripts.ny_run")


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
    p.write_text(f"token_sha256: {AUTH.token_sha256}\narmed_sha: {'a' * 40}\n"
                 f"entrypoint: scripts.ny_run\n")  # no account
    with pytest.raises(ArmingError, match="account"):
        load_authorization(p)


def test_authorization_without_an_entrypoint_refuses(tmp_path):
    """2026-08-03 audit: entrypoint is required, no default — an old-shape file (from
    before this fix) must refuse rather than silently arm on an unscoped basis."""
    p = tmp_path / "arming.yaml"
    p.write_text(f"token_sha256: {AUTH.token_sha256}\n"
                 f"armed_sha: {AUTH.armed_sha}\naccount: {AUTH.account}\n")
    with pytest.raises(ArmingError, match="entrypoint"):
        load_authorization(p)


def test_roundtrip_load(tmp_path):
    p = tmp_path / "arming.yaml"
    p.write_text(f"token_sha256: {AUTH.token_sha256}\n"
                 f"armed_sha: {AUTH.armed_sha}\naccount: {AUTH.account}\n"
                 f"entrypoint: {AUTH.entrypoint}\n")
    assert load_authorization(p) == AUTH


# ---- entrypoint scoping (2026-08-03 audit) -----------------------------------
def test_verify_for_arming_refuses_a_different_entrypoint(tmp_path, monkeypatch):
    """The concrete incident this closes: canon_run.py and ny_run.py share this file.
    A phrase Angus wrote for one must not arm the other, even with a matching token and
    a HEAD that happens to equal armed_sha."""
    p = tmp_path / "arming.yaml"
    p.write_text(f"token_sha256: {AUTH.token_sha256}\n"
                 f"armed_sha: {head_sha_for_test()}\naccount: {AUTH.account}\n"
                 f"entrypoint: scripts.ny_run\n")
    with pytest.raises(ArmingError, match="scripts.canon_run.*scripts.ny_run|issued for"):
        verify_for_arming(WORD, entrypoint="scripts.canon_run", path=p)


def test_verify_for_arming_succeeds_for_the_matching_entrypoint(tmp_path):
    p = tmp_path / "arming.yaml"
    p.write_text(f"token_sha256: {AUTH.token_sha256}\n"
                 f"armed_sha: {head_sha_for_test()}\naccount: {AUTH.account}\n"
                 f"entrypoint: scripts.ny_run\n")
    auth = verify_for_arming(WORD, entrypoint="scripts.ny_run", path=p)
    assert auth.entrypoint == "scripts.ny_run"


def head_sha_for_test() -> str:
    from src.live.arming import head_sha
    return head_sha(".")


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
