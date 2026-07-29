#!/usr/bin/env python3
"""
Mutate the Hermes Desk skills via the confirmed Skills API (headless Playwright
supplies the authenticated session; all calls go through it).

The routes and their exact semantics are documented — and were probed live — in
docs/hermes-api-contract.md, which is ground truth for this script.

Phases, in order. The default run is READ-ONLY recon; every mutating phase is
opt-in AND explicitly targeted.

  1. recon    (always)   log in, enumerate every skill, back up full content to
                         disk, report counts / names / enabled state. Mutates
                         nothing.
  2. create   (--create) create each --only skill (POST /api/skills).
  3. update   (--update) full-rewrite each --only skill in place
                         (PUT /api/skills/content).
  4. disable  (--disable) disable each --only skill (PUT /api/skills/toggle).
  5. enable   (--enable)  enable each --only skill (PUT /api/skills/toggle).
  6. verify   (always, after any mutation)  re-enumerate.

READ-BACK IS MANDATORY. A 200 / ok:true response is treated as *nothing* until a
follow-up GET proves the change landed:

  * create / update -> GET /api/skills/content?name= returns 200 and the content
    matches what was written;
  * disable / enable -> the skill's `enabled` flag in GET /api/skills matches.

This is deliberate. The Hermes API returns success-shaped responses for
operations that do not take effect — e.g. POST /api/skills/hub/uninstall returns
`{ok:true, pid:...}` yet removes nothing for an agent-provenance skill. The
response alone is never trusted; see the contract doc.

REMOVAL IS INTENTIONALLY NOT HERE. There is no API route that removes an
agent-provenance skill: DELETE /api/skills/<name> is 405 (not a real route) and
hub/uninstall is a no-op. Removal is filesystem-level (`docker exec … rm -rf`)
over SSH with by-eye path safeguards, and lives entirely outside this HTTP flow.
See "Confirmed removal mechanism" in docs/hermes-api-contract.md. This script
never deletes.

TARGETING IS EXPLICIT. There are no hardcoded skill-name lists. Every mutation
acts only on the names passed via --only (repeatable). Any mutating phase with
no --only target refuses to run, so a stray --create can never touch a skill it
was not pointed at.

Content for create / update comes from --content-file (single target) or from
--content-dir/<name>.md (one file per target; default docs/desk-skills).

Credentials are resolved in this order, and are never hardcoded or logged:

  1. HERMES_USER / HERMES_PASS in the environment (for unattended runs)
  2. the macOS Keychain, service "hermes-agent"
  3. an interactive prompt (password via getpass, so it is never echoed and
     never lands in shell history) — after which it offers to save to the
     Keychain so later runs need no prompt at all

Usage:
  python3 scripts/hermes_desk_rebuild.py
      # recon only (read-only; the default)
  python3 scripts/hermes_desk_rebuild.py --create --only zz-throwaway-v2 \
      --content-file /tmp/body.md --category testing --description "throwaway"
  python3 scripts/hermes_desk_rebuild.py --update --only zz-throwaway-v2 \
      --content-file /tmp/body2.md
  python3 scripts/hermes_desk_rebuild.py --disable --only zz-throwaway-v2
  python3 scripts/hermes_desk_rebuild.py --enable  --only zz-throwaway-v2
  python3 scripts/hermes_desk_rebuild.py --headed        # watch it run
  python3 scripts/hermes_desk_rebuild.py --no-keychain   # ignore the Keychain
  python3 scripts/hermes_desk_rebuild.py --forget        # drop the saved entry
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import re
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import Page, TimeoutError as PWTimeout, sync_playwright

BASE = "https://hermes-agent-07ie.srv1842904.hstgr.cloud"

REPO = Path(__file__).resolve().parent.parent
DEFAULT_CONTENT_DIR = REPO / "docs" / "desk-skills"

# Confirmed routes (docs/hermes-api-contract.md). Mutations use these fixed
# paths, not a discovered one — the contract is ground truth.
LIST_ROUTE = "/api/skills"                 # GET  -> metadata array (incl. enabled)
CONTENT_ROUTE = "/api/skills/content"      # GET  ?name= -> {content}; PUT -> full rewrite
CREATE_ROUTE = "/api/skills"               # POST {name, content, description, category}
TOGGLE_ROUTE = "/api/skills/toggle"        # PUT  {name, enabled, profile}


def log(msg: str) -> None:
    print(f"[{datetime.now(timezone.utc):%H:%M:%S}] {msg}", flush=True)


def outdir() -> Path:
    d = REPO / ".hermes-rebuild" / f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}"
    d.mkdir(parents=True, exist_ok=True)
    return d


# --------------------------------------------------------------------------
# auth
# --------------------------------------------------------------------------

KEYCHAIN_SERVICE = "hermes-agent"
_KC_NOT_FOUND = 44  # `security` exit code for "item not found"


def _security(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(["security", *argv], capture_output=True, text=True)


def keychain_available() -> bool:
    return sys.platform == "darwin"


def keychain_load(service: str = KEYCHAIN_SERVICE) -> tuple[str, str] | None:
    """Return (username, password) from the Keychain, or None if absent.

    The username is stored as the item's account attribute, so a single
    Keychain entry carries both halves of the credential.
    """
    if not keychain_available():
        return None

    probe = _security("find-generic-password", "-s", service)
    if probe.returncode != 0:  # 44 = no such item; anything else = denied/locked
        if probe.returncode != _KC_NOT_FOUND:
            log(f"keychain lookup failed (rc={probe.returncode}); falling back to prompt")
        return None

    m = re.search(r'"acct"<blob>="([^"]*)"', probe.stdout)
    if not m or not m.group(1):
        return None
    user = m.group(1)

    got = _security("find-generic-password", "-s", service, "-a", user, "-w")
    if got.returncode != 0:
        return None
    # `-w` emits the secret followed by a single newline.
    return user, got.stdout.rstrip("\n")


def keychain_save(user: str, password: str, service: str = KEYCHAIN_SERVICE) -> bool:
    """Store the credential, replacing any existing entry for this service.

    Caveat: `security` cannot read a password from stdin (with no value it
    prompts on the TTY and demands a retype), so the secret is passed in argv
    and is briefly visible via `ps` to other processes owned by this same user
    during the one-time save. That is a narrower exposure than shell history,
    which is what prompted using the Keychain in the first place, but it is not
    zero — hence --no-keychain for anyone who would rather just retype.
    """
    if not keychain_available():
        return False
    r = _security("add-generic-password", "-U", "-s", service, "-a", user,
                  "-w", password, "-l", f"Hermes Agent ({service})")
    if r.returncode != 0:
        log(f"could not save to keychain: {r.stderr.strip()}")
        return False
    return True


def keychain_forget(service: str = KEYCHAIN_SERVICE) -> None:
    if not keychain_available():
        print("Keychain is macOS-only; nothing to forget.")
        return
    r = _security("delete-generic-password", "-s", service)
    print("Removed the saved Hermes credential." if r.returncode == 0
          else "No saved Hermes credential to remove.")


def get_credentials(use_keychain: bool = True) -> tuple[str, str, str]:
    """Resolve credentials: environment, then Keychain, then prompt.

    The password is read with getpass so it is never echoed and never recorded
    in shell history. Values are read but never printed.
    """
    user = os.environ.get("HERMES_USER") or ""
    password = os.environ.get("HERMES_PASS") or ""
    if user and password:
        log(f"using credentials from environment for {user!r}")
        return user, password, "env"

    if use_keychain:
        found = keychain_load()
        if found:
            log(f"using credentials from keychain for {found[0]!r}")
            return found[0], found[1], "keychain"

    if not sys.stdin.isatty():
        raise SystemExit(
            "No TTY to prompt on, no keychain entry, and HERMES_USER/HERMES_PASS "
            "are unset — run this in an interactive terminal."
        )

    print(f"Sign in to {BASE}")
    if not user:
        user = input("  username: ").strip()
    if not password:
        password = getpass.getpass("  password (not echoed): ")
    if not user or not password:
        raise SystemExit("username and password are both required")

    # Only offer to persist once we know the credential actually works, so a
    # typo never gets cached — see the call site in main().
    return user, password, "prompt"


def dump_state(page: Page, out: Path, tag: str) -> None:
    """Best-effort forensic snapshot of the current page.

    Every failure path calls this. A run that dies must never leave an empty
    artifact directory — without a screenshot and the DOM there is nothing to
    diagnose from, only a guess.
    """
    try:
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{tag}.url.txt").write_text(page.url)
        (out / f"{tag}.html").write_text(page.content())
        page.screenshot(path=str(out / f"{tag}.png"), full_page=True)
        log(f"  state dumped -> {tag}.{{png,html,url.txt}}")
    except Exception as e:  # never let diagnostics mask the original error
        log(f"  (could not dump state: {e})")


def login(page: Page, user: str, password: str, out: Path) -> None:
    """Sign in via the basic username/password provider on /login."""
    page.goto(f"{BASE}/login", wait_until="domcontentloaded", timeout=45_000)

    form = page.locator('form[data-provider="basic"]')
    form.locator('input[name="username"]').fill(user)
    form.locator('input[name="password"]').fill(password)
    form.locator('button[type="submit"]').click()

    try:
        page.wait_for_url(lambda u: "/login" not in u, timeout=20_000)
    except PWTimeout:
        # Still on /login: surface the app's own error text rather than a
        # generic timeout, so a bad password is obvious.
        err = " ".join(page.locator(".error, .alert, [role=alert]").all_text_contents())
        dump_state(page, out, "login-failed")
        raise SystemExit(f"Login failed{': ' + err.strip() if err.strip() else ''}")

    log(f"authenticated as {user!r} -> {page.url}")
    dump_state(page, out, "post-login")


# --------------------------------------------------------------------------
# transport + reads
# --------------------------------------------------------------------------

def api(page: Page, path: str, method: str = "GET", payload: dict | None = None):
    """Call the app's JSON API reusing the browser's authenticated session.

    Returns (status, parsed_or_text).
    """
    opts = {"method": method}
    if payload is not None:
        opts["data"] = payload
    try:
        r = page.request.fetch(f"{BASE}{path}", **opts)
    except Exception as e:
        # A transport-level failure is a probe result, not a reason to abort
        # the whole run — the caller decides how to handle it.
        return 0, f"request failed: {e}"
    try:
        return r.status, r.json()
    except Exception:
        return r.status, r.text()


def skill_name(s: dict) -> str:
    for k in ("name", "slug", "title", "id"):
        v = s.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def list_skills(page: Page) -> tuple[int, list[dict]]:
    """GET /api/skills -> (status, metadata list). Empty list on any non-array."""
    status, body = api(page, LIST_ROUTE)
    if status == 200 and isinstance(body, list):
        return status, body
    return status, []


def read_content(page: Page, name: str) -> tuple[int, str | None, str | None]:
    """GET /api/skills/content?name= -> (status, content, path).

    A 404 here is the canonical proof that a skill is absent (there is no
    per-skill detail route; this query form is the only route that returns a
    body). content/path are None unless status is 200.
    """
    status, body = api(page, f"{CONTENT_ROUTE}?name={quote(name, safe='')}")
    if status == 200 and isinstance(body, dict):
        return status, body.get("content"), body.get("path")
    return status, None, None


def read_meta(page: Page, name: str) -> tuple[int, dict | None]:
    """Return the list-metadata dict for `name`, filtered client-side.

    The list route's `name=` filter is ignored server-side, so we always fetch
    the full list and match here.
    """
    status, items = list_skills(page)
    if status != 200:
        return status, None
    for s in items:
        if skill_name(s) == name:
            return status, s
    return status, None


def content_matches(read_back: str | None, written: str) -> bool:
    """True if the read-back body equals what we wrote.

    Storage is verbatim (the contract confirms a full-rewrite PUT reads back
    exactly), so this is an exact comparison — modulo a single trailing newline,
    which some editors/servers normalise and which carries no meaning here.
    """
    return (read_back or "").rstrip("\n") == (written or "").rstrip("\n")


# --------------------------------------------------------------------------
# recon
# --------------------------------------------------------------------------

def recon(page: Page, out: Path) -> dict:
    """Read-only enumeration + full-content backup. Mutates nothing."""
    status, skills = list_skills(page)
    if status != 200:
        log(f"  WARNING list route {LIST_ROUTE} -> HTTP {status}")

    names = sorted(skill_name(s) for s in skills)
    enabled_map = {skill_name(s): s.get("enabled") for s in skills}

    report = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "list_status": status,
        "total_existing": len(skills),
        "existing": names,
        "enabled": enabled_map,
    }

    # Full-content backup before any mutation. The list endpoint returns
    # metadata only, so pull each skill's actual body too — a backup without the
    # content is not a backup you could restore from. Reads only; safe.
    backup = out / "backup"
    backup.mkdir(parents=True, exist_ok=True)
    for s in skills:
        n = skill_name(s) or "unnamed"
        safe = re.sub(r"[^A-Za-z0-9._-]", "_", n)
        cstatus, content, path = read_content(page, n)
        if cstatus == 200 and content is not None:
            s = {**s, "content": content, "path": path}
        else:
            log(f"  WARNING no content retrieved for {n!r} (status {cstatus})")
        (backup / f"{safe}.json").write_text(json.dumps(s, indent=2))

    (out / "recon.json").write_text(json.dumps(report, indent=2))
    (out / "skills_list_raw.json").write_text(json.dumps(skills, indent=2))
    return report


# --------------------------------------------------------------------------
# mutations — each confirmed by read-back, never by the response alone
# --------------------------------------------------------------------------

def create_skill(page: Page, name: str, content: str, description: str,
                 category: str, profile: str | None = None) -> bool:
    """POST /api/skills, then confirm by reading the content back."""
    payload = {"name": name, "content": content,
               "description": description, "category": category}
    if profile:
        payload["profile"] = profile
    status, body = api(page, CREATE_ROUTE, method="POST", payload=payload)
    log(f"  CREATE {name!r} ({len(content)} chars, category={category!r}) "
        f"-> HTTP {status}")

    # A 200 here counts as NOTHING until read-back confirms (see module docstring
    # and the hub/uninstall no-op in the contract doc).
    rstatus, rcontent, rpath = read_content(page, name)
    if rstatus != 200 or rcontent is None:
        log(f"  READ-BACK {name!r} -> HTTP {rstatus}: create NOT confirmed "
            f"(response was {body!r})")
        return False
    if not content_matches(rcontent, content):
        log(f"  READ-BACK {name!r} -> HTTP 200 but content differs from what was "
            f"written: create NOT confirmed")
        return False
    log(f"  READ-BACK {name!r} -> HTTP 200, content matches "
        f"({len(rcontent)} chars) at {rpath}")
    return True


def update_skill(page: Page, name: str, content: str,
                 profile: str | None = None) -> bool:
    """PUT /api/skills/content (full rewrite), then confirm by read-back."""
    payload = {"name": name, "content": content}
    if profile:
        payload["profile"] = profile
    status, body = api(page, CONTENT_ROUTE, method="PUT", payload=payload)
    log(f"  UPDATE {name!r} ({len(content)} chars, full rewrite) -> HTTP {status}")

    rstatus, rcontent, rpath = read_content(page, name)
    if rstatus != 200 or rcontent is None:
        log(f"  READ-BACK {name!r} -> HTTP {rstatus}: update NOT confirmed "
            f"(response was {body!r})")
        return False
    if not content_matches(rcontent, content):
        log(f"  READ-BACK {name!r} -> HTTP 200 but content still differs from the "
            f"new body: update NOT confirmed")
        return False
    log(f"  READ-BACK {name!r} -> HTTP 200, new content confirmed "
        f"({len(rcontent)} chars) at {rpath}")
    return True


def set_enabled(page: Page, name: str, enabled: bool,
                profile: str | None = None) -> bool:
    """PUT /api/skills/toggle, then confirm the `enabled` flag via the list."""
    payload = {"name": name, "enabled": enabled}
    if profile:
        payload["profile"] = profile
    status, body = api(page, TOGGLE_ROUTE, method="PUT", payload=payload)
    verb = "ENABLE" if enabled else "DISABLE"
    log(f"  {verb} {name!r} -> HTTP {status}")

    rstatus, meta = read_meta(page, name)
    if rstatus != 200 or meta is None:
        log(f"  READ-BACK {name!r} -> not found in list (HTTP {rstatus}): "
            f"toggle NOT confirmed (response was {body!r})")
        return False
    actual = meta.get("enabled")
    if actual != enabled:
        log(f"  READ-BACK {name!r} -> enabled={actual!r}, expected {enabled!r}: "
            f"toggle NOT confirmed")
        return False
    log(f"  READ-BACK {name!r} -> enabled={actual!r} confirmed")
    return True


# --------------------------------------------------------------------------
# content resolution for create / update targets
# --------------------------------------------------------------------------

def resolve_content_path(name: str, args) -> Path:
    if args.content_file:
        return Path(args.content_file)
    return Path(args.content_dir) / f"{name}.md"


def preflight_content(names: list[str], args) -> list[str]:
    """Return a list of human-readable problems with the content sources."""
    problems = []
    if args.content_file and len(names) > 1:
        problems.append(
            f"--content-file takes a single body but {len(names)} --only targets "
            f"were given; use --content-dir with one <name>.md per target instead"
        )
    for n in names:
        p = resolve_content_path(n, args)
        if not p.exists():
            problems.append(f"missing content for {n!r}: {p}")
    return problems


# --------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", action="append", metavar="NAME", default=[],
                    help="explicit mutation target (repeatable); required for any "
                         "mutating phase")
    ap.add_argument("--create", action="store_true",
                    help="create each --only skill (POST /api/skills)")
    ap.add_argument("--update", action="store_true",
                    help="full-rewrite each --only skill (PUT /api/skills/content)")
    ap.add_argument("--disable", action="store_true",
                    help="disable each --only skill (PUT /api/skills/toggle)")
    ap.add_argument("--enable", action="store_true",
                    help="enable each --only skill (PUT /api/skills/toggle)")
    ap.add_argument("--content-file", metavar="PATH",
                    help="body for create/update of a single --only target")
    ap.add_argument("--content-dir", metavar="DIR", default=str(DEFAULT_CONTENT_DIR),
                    help="dir of <name>.md bodies for create/update "
                         f"(default {DEFAULT_CONTENT_DIR})")
    ap.add_argument("--description", default="",
                    help="description metadata for --create")
    ap.add_argument("--category", default=None,
                    help="on-disk category for --create (required with --create)")
    ap.add_argument("--profile", default=None,
                    help="optional profile passed to mutating calls")
    ap.add_argument("--headed", action="store_true", help="run with a visible browser")
    ap.add_argument("--no-keychain", action="store_true",
                    help="ignore the macOS Keychain and never offer to save")
    ap.add_argument("--forget", action="store_true",
                    help="delete the saved Keychain credential and exit")
    args = ap.parse_args()

    if args.forget:
        keychain_forget()
        return 0

    mutating = args.create or args.update or args.disable or args.enable

    # Explicit-targeting guard: a mutating phase with no --only refuses to run.
    if mutating and not args.only:
        print("refusing to mutate without an explicit target: pass --only <name> "
              "(repeatable). The default run is read-only recon.", file=sys.stderr)
        return 2

    if args.create and not args.category:
        print("--create requires --category (it sets the on-disk path); supply it.",
              file=sys.stderr)
        return 2

    # Fail before prompting for a password if a create/update body is missing.
    if args.create or args.update:
        problems = preflight_content(args.only, args)
        if problems:
            for p in problems:
                print(p, file=sys.stderr)
            return 2

    user, password, source = get_credentials(use_keychain=not args.no_keychain)

    out = outdir()
    log(f"artifacts -> {out}")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not args.headed)
        page = browser.new_context().new_page()
        try:
            return run(page, args, user, password, source, out)
        except SystemExit:
            raise  # already diagnosed and dumped by the raiser
        except Exception:
            # Any unhandled failure still leaves a screenshot, the DOM and a
            # traceback behind. An empty artifact directory is not a usable
            # bug report.
            (out / "traceback.txt").write_text(traceback.format_exc())
            dump_state(page, out, "crash")
            log(f"run failed — diagnostics in {out}")
            raise
        finally:
            browser.close()


def run(page: Page, args, user: str, password: str, source: str, out: Path) -> int:
    """The actual session. The browser is closed by main()'s finally block."""
    login(page, user, password, out)

    # Offer to persist only now that the server has actually accepted the
    # credential — caching a typo would be worse than not caching at all.
    if source == "prompt" and not args.no_keychain and keychain_available():
        if input("  save to keychain for next time? [y/N] ").strip().lower() in ("y", "yes"):
            if keychain_save(user, password):
                log("saved; future runs will not prompt (--forget to undo)")

    log("=== PHASE 1: recon (read-only) ===")
    report = recon(page, out)
    log(f"  {report['total_existing']} skills present: {report['existing']}")

    mutating = args.create or args.update or args.disable or args.enable
    if not mutating:
        log("recon-only run (pass a mutating phase with --only to change anything). "
            "Nothing changed.")
        log(f"artifacts written to {out}")
        return 0

    # Guard is enforced in main(), but re-assert here so run() is safe on its own.
    if not args.only:
        raise SystemExit("refusing to mutate without --only targets")

    ok = True

    if args.create:
        log(f"=== PHASE 2: create {args.only} ===")
        for n in args.only:
            content = resolve_content_path(n, args).read_text()
            ok = create_skill(page, n, content, args.description, args.category,
                              args.profile) and ok

    if args.update:
        log(f"=== PHASE 3: update {args.only} ===")
        for n in args.only:
            content = resolve_content_path(n, args).read_text()
            ok = update_skill(page, n, content, args.profile) and ok

    if args.disable:
        log(f"=== PHASE 4: disable {args.only} ===")
        for n in args.only:
            ok = set_enabled(page, n, False, args.profile) and ok

    if args.enable:
        log(f"=== PHASE 5: enable {args.only} ===")
        for n in args.only:
            ok = set_enabled(page, n, True, args.profile) and ok

    log("=== PHASE 6: verify (re-enumerate) ===")
    final = recon(page, out / "post")
    log(f"  now {final['total_existing']} skills present")
    log(f"artifacts written to {out}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
