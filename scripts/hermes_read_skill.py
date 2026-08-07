#!/usr/bin/env python3
"""Read-only: fetch the full stored content of named Hermes skills.

Strictly GET-only — it authenticates through the normal login form, probes for
whichever detail endpoint the app exposes, and saves what it finds. It never
writes to the server.

  python3 scripts/hermes_read_skill.py atlas apollo hephaestus
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))

from playwright.sync_api import sync_playwright  # noqa: E402

from hermes_desk_rebuild import (  # noqa: E402
    BASE, REPO, api, get_credentials, login,
)

# The real route, recovered from the dashboard bundle:
#   getSkillContent: GET /api/skills/content?name=<name>[&profile=<profile>]
ROUTES = ("/api/skills/content?name={n}",)


def main(names: list[str]) -> int:
    user, password, _ = get_credentials()
    out = REPO / ".hermes-rebuild" / "skill-content"
    out.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_context().new_page()
        try:
            login(page, user, password, out)
            for name in names:
                n = quote(name, safe="")
                print(f"\n--- {name} ---")
                for tpl in ROUTES:
                    path = tpl.format(n=n)
                    status, body = api(page, path)
                    print(f"  GET {path} -> {status}")
                    if status != 200 or not body:
                        continue
                    text = body if isinstance(body, str) else json.dumps(body, indent=2)
                    (out / f"{name}.json").write_text(text)
                    print(f"    saved {len(text)} chars -> {out / (name + '.json')}")
                    break
                else:
                    print(f"  !! nothing served content for {name!r}")
        finally:
            browser.close()

    print(f"\ncontent in {out}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1:]))
