#!/usr/bin/env python3
"""
Rebuild the Hermes Desk skills via browser automation (headless Playwright).

Phases, in order. Each is opt-in; the default run is READ-ONLY recon.

  1. recon   (always)  log in, enumerate every existing skill, back up its full
                       content to disk, and report which of the 7 off-spec
                       skills are actually present. Mutates nothing.
  2. delete  (--delete)  remove the 7 off-spec skills.
  3. create  (--create)  create the 4 specialists + the Hermes coordinator from
                         docs/desk-skills/*.md.
  4. verify  (always, after any mutation)  re-enumerate and diff against intent.

Credentials are prompted for interactively (the password via getpass, so it is
never echoed and never lands in shell history). Nothing is hardcoded or logged.
For non-interactive runs (CI, cron) HERMES_USER / HERMES_PASS are honored if
set, but prefer the prompt on a workstation.

Usage:
  python3 scripts/hermes_desk_rebuild.py                    # recon only
  python3 scripts/hermes_desk_rebuild.py --delete --create  # full rebuild
  python3 scripts/hermes_desk_rebuild.py --headed           # watch it run

Note on case: the skills being deleted are lowercase ("atlas") and several of
the skills being created differ only in case ("Atlas"). Deletes therefore run
to completion before any create starts, so a case-insensitive backend cannot
collide a create against a not-yet-deleted skill.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import Page, TimeoutError as PWTimeout, sync_playwright

BASE = "https://hermes-agent-07ie.srv1842904.hstgr.cloud"

REPO = Path(__file__).resolve().parent.parent
DOCS = REPO / "docs" / "desk-skills"

# The 7 off-spec skills to remove.
OFF_SPEC = [
    "atlas",
    "lumen",
    "hydra",
    "hermes-execution",
    "apollo",
    "hephaestus",
    "mnemosyne",
]

# The real desk: 4 specialists + the coordinator. (display name -> source doc)
TARGET = [
    ("Atlas", "atlas-skill.md"),
    ("Helios", "helios-skill.md"),
    ("Apollo", "apollo-skill.md"),
    ("Hephaestus", "hephaestus-skill.md"),
    ("Hermes", "hermes-coordinator.md"),
]


def log(msg: str) -> None:
    print(f"[{datetime.now(timezone.utc):%H:%M:%S}] {msg}", flush=True)


def outdir() -> Path:
    d = REPO / ".hermes-rebuild" / f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}"
    d.mkdir(parents=True, exist_ok=True)
    return d


# --------------------------------------------------------------------------
# auth
# --------------------------------------------------------------------------

def get_credentials() -> tuple[str, str]:
    """Prompt for credentials, falling back to the environment.

    The password is read with getpass so it is never echoed to the terminal
    and never recorded in shell history. Env vars exist only so this can run
    unattended; they are read but never printed.
    """
    user = os.environ.get("HERMES_USER") or ""
    password = os.environ.get("HERMES_PASS") or ""
    if user and password:
        log(f"using credentials from environment for {user!r}")
        return user, password

    if not sys.stdin.isatty():
        raise SystemExit(
            "No TTY to prompt on and HERMES_USER/HERMES_PASS are unset — "
            "run this in an interactive terminal."
        )

    print(f"Sign in to {BASE}")
    if not user:
        user = input("  username: ").strip()
    if not password:
        password = getpass.getpass("  password (not echoed): ")

    if not user or not password:
        raise SystemExit("username and password are both required")
    return user, password


def login(page: Page, user: str, password: str) -> None:
    """Sign in via the basic username/password provider on /login."""
    page.goto(f"{BASE}/login", wait_until="domcontentloaded")

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
        raise SystemExit(f"Login failed{': ' + err.strip() if err.strip() else ''}")

    log(f"authenticated as {user!r} -> {page.url}")


# --------------------------------------------------------------------------
# recon
# --------------------------------------------------------------------------

def api(page: Page, path: str, method: str = "GET", payload: dict | None = None):
    """Call the app's JSON API reusing the browser's authenticated session.

    Returns (status, parsed_or_text). The API is preferred over DOM clicking
    where it works; DOM is the fallback.
    """
    opts = {"method": method}
    if payload is not None:
        opts["data"] = payload
    r = page.request.fetch(f"{BASE}{path}", **opts)
    try:
        return r.status, r.json()
    except Exception:
        return r.status, r.text()


def discover_skills(page: Page, out: Path) -> tuple[list[dict], str | None]:
    """Enumerate existing skills. Tries the JSON API first, then the DOM.

    Returns (skills, api_path_that_worked).
    """
    for path in ("/api/skills", "/api/v1/skills", "/api/agents/skills"):
        status, body = api(page, path)
        log(f"probe {path} -> {status}")
        if status == 200 and isinstance(body, (list, dict)):
            items = body if isinstance(body, list) else (
                body.get("skills") or body.get("items") or body.get("data") or []
            )
            if isinstance(items, list) and items:
                (out / "skills_api_raw.json").write_text(json.dumps(body, indent=2))
                return items, path

    # DOM fallback: dump the skills page for selector discovery.
    log("no usable JSON API; falling back to DOM scrape")
    for path in ("/skills", "/settings/skills", "/"):
        page.goto(f"{BASE}{path}", wait_until="networkidle")
        if "/login" in page.url:
            continue
        (out / f"dom{path.replace('/', '_') or '_root'}.html").write_text(page.content())
        page.screenshot(path=str(out / f"dom{path.replace('/', '_') or '_root'}.png"),
                        full_page=True)

    names = page.locator("[data-skill-name], [data-skill-id], .skill-card, .skill-item")
    found = []
    for i in range(names.count()):
        el = names.nth(i)
        found.append({
            "name": (el.get_attribute("data-skill-name") or el.inner_text()).strip(),
            "id": el.get_attribute("data-skill-id"),
        })
    return found, None


def skill_name(s: dict) -> str:
    for k in ("name", "slug", "title", "id"):
        v = s.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def recon(page: Page, out: Path) -> dict:
    skills, api_path = discover_skills(page, out)
    present = {skill_name(s).lower(): s for s in skills}

    report = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "api_path": api_path,
        "total_existing": len(skills),
        "existing": [skill_name(s) for s in skills],
        "off_spec_present": [n for n in OFF_SPEC if n.lower() in present],
        "off_spec_missing": [n for n in OFF_SPEC if n.lower() not in present],
        "targets_already_present": [n for n, _ in TARGET if n.lower() in present],
    }

    # Full-content backup before anything is destroyed.
    backup = out / "backup"
    backup.mkdir(exist_ok=True)
    for s in skills:
        n = skill_name(s) or "unnamed"
        safe = re.sub(r"[^A-Za-z0-9._-]", "_", n)
        (backup / f"{safe}.json").write_text(json.dumps(s, indent=2))

    (out / "recon.json").write_text(json.dumps(report, indent=2))
    return report


# --------------------------------------------------------------------------
# mutations
# --------------------------------------------------------------------------

def delete_skill(page: Page, skill: dict, api_path: str | None) -> bool:
    ident = skill.get("id") or skill.get("slug") or skill_name(skill)
    if api_path:
        status, body = api(page, f"{api_path}/{ident}", method="DELETE")
        ok = status in (200, 202, 204)
        log(f"  DELETE {ident} -> {status} {'ok' if ok else body}")
        return ok
    raise SystemExit(
        "DOM delete path not yet implemented — run recon first and wire the "
        "selectors from .hermes-rebuild/*/dom_*.html"
    )


def create_skill(page: Page, name: str, content: str, api_path: str | None) -> bool:
    if api_path:
        status, body = api(page, api_path, method="POST",
                           payload={"name": name, "content": content})
        ok = status in (200, 201)
        log(f"  CREATE {name} ({len(content)} chars) -> {status} {'ok' if ok else body}")
        return ok
    raise SystemExit(
        "DOM create path not yet implemented — run recon first and wire the "
        "selectors from .hermes-rebuild/*/dom_*.html"
    )


# --------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--delete", action="store_true", help="delete the 7 off-spec skills")
    ap.add_argument("--create", action="store_true", help="create the 4 specialists + coordinator")
    ap.add_argument("--headed", action="store_true", help="run with a visible browser")
    args = ap.parse_args()

    # Fail before prompting for a password if any source doc is missing.
    missing = [f for _, f in TARGET if not (DOCS / f).exists()]
    if args.create and missing:
        print(f"missing source docs: {missing}", file=sys.stderr)
        return 2

    user, password = get_credentials()

    out = outdir()
    log(f"artifacts -> {out}")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not args.headed)
        page = browser.new_context().new_page()

        login(page, user, password)

        log("=== PHASE 1: recon (read-only) ===")
        report = recon(page, out)
        log(f"  {report['total_existing']} skills present: {report['existing']}")
        log(f"  off-spec present : {report['off_spec_present']}")
        log(f"  off-spec missing : {report['off_spec_missing']}")
        log(f"  targets already there: {report['targets_already_present']}")

        if not (args.delete or args.create):
            log("recon-only run (pass --delete --create to mutate). Nothing changed.")
            browser.close()
            return 0

        skills, api_path = discover_skills(page, out)
        by_name = {skill_name(s).lower(): s for s in skills}

        if args.delete:
            log("=== PHASE 2: delete off-spec ===")
            for n in OFF_SPEC:
                s = by_name.get(n.lower())
                if not s:
                    log(f"  skip {n} (not present)")
                    continue
                delete_skill(page, s, api_path)

        if args.create:
            log("=== PHASE 3: create real desk ===")
            for name, fname in TARGET:
                create_skill(page, name, (DOCS / fname).read_text(), api_path)

        log("=== PHASE 4: verify ===")
        final = recon(page, out / "post")
        log(f"  now present: {final['existing']}")
        leftover = final["off_spec_present"]
        absent = [n for n, _ in TARGET if n not in final["existing"]]
        if leftover:
            log(f"  WARNING off-spec still present: {leftover}")
        if absent:
            log(f"  WARNING target skills missing: {absent}")
        browser.close()
        return 1 if (leftover or absent) else 0


if __name__ == "__main__":
    raise SystemExit(main())
