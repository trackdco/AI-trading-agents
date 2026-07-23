# Hermes Agent — Skills API contract (confirmed by live probe)

Host: `https://hermes-agent-07ie.srv1842904.hstgr.cloud`
Backend: FastAPI + uvicorn. Skills are server-side files at
`/opt/data/skills/<category>/<name>/SKILL.md`.

Every route below was exercised **live** against a throwaway skill
(`zz-throwaway-rebuild-test`, `category: testing`) on 24 Jul 2026 — no real
desk skill was touched. Auth is the normal session cookie from
`POST /auth/password-login` (see the recon notes); all calls reuse it.

Verbs marked ✅ are confirmed working with the exact payloads shown. The removal
verbs (⚠️) are the open finding.

---

## Create — ✅ `POST /api/skills`

Request body (JSON):

```json
{
  "name": "zz-throwaway-rebuild-test",
  "description": "Throwaway skill for API contract testing. Safe to delete.",
  "category": "testing",
  "content": "---\nname: zz-throwaway-rebuild-test\ndescription: ...\n---\n\nLINE ONE ...\n"
}
```

- `name`, `content` are the essentials; `description` and `category` set the
  metadata and the on-disk path. Omitting `category` defaults it (untested —
  supply it).
- `profile` is accepted (from the dashboard bundle: `{...skill, profile}`) but
  was not needed; omit for the default profile.

Response — **HTTP 200**:

```json
{
  "success": true,
  "message": "Skill 'zz-throwaway-rebuild-test' created.",
  "path": "testing/zz-throwaway-rebuild-test",
  "skill_md": "/opt/data/skills/testing/zz-throwaway-rebuild-test/SKILL.md",
  "_change": { "description": "..." },
  "category": "testing"
}
```

Note: success is **200**, not 201. A create/update helper should accept 200.

---

## Read — ✅ `GET /api/skills/content?name=<name>`

Optional `&profile=<profile>`. Response — **HTTP 200**:

```json
{
  "name": "zz-throwaway-rebuild-test",
  "content": "---\nname: ...\n---\n\nLINE ONE ...\n",
  "path": "/opt/data/skills/testing/zz-throwaway-rebuild-test/SKILL.md"
}
```

This is the ONLY route that returns a skill's body. `GET /api/skills/<name>`
returns **404** — there is no per-skill detail route; use the query form.
A non-existent name returns 404 here too, which is how you confirm removal.

## List — ✅ `GET /api/skills`

Returns a JSON array of **metadata only** (no `content`). Each item:

```json
{ "name": "...", "description": "...", "category": "...",
  "enabled": true, "usage": 0, "provenance": "agent" }
```

`?query` filters are accepted by the route but a `name=` filter is **ignored** —
it returns the full list regardless. Filter client-side.

---

## Update (in place) — ✅ `PUT /api/skills/content`

Request body (JSON):

```json
{ "name": "zz-throwaway-rebuild-test", "content": "<full new SKILL.md text>" }
```

Optional `profile`. This is a **full rewrite**, not a patch — send the entire
content. Response — **HTTP 200**:

```json
{
  "success": true,
  "message": "Skill 'zz-throwaway-rebuild-test' updated (full rewrite).",
  "path": "/opt/data/skills/testing/zz-throwaway-rebuild-test",
  "_change": { "description": "..." }
}
```

Verified: reading back after the PUT returned the new content (a second line
that was not in the original). This is the route the eventual "update the three
mappable skills in place" plan should use — it preserves the skill's identity
and usage history.

---

## Removal — RESOLVED: no API route exists; removal is filesystem-level

**There is no HTTP API that removes an `agent`-provenance skill.** The whole
skill-management surface in the dashboard bundle is: `createSkill` (POST),
`updateSkillContent` (PUT), `toggleSkill` (PUT `/api/skills/toggle` — disable
only, does not remove), and the `*FromHub` family (hub-installed skills only).
No `delete`/`remove`/`archive`/`destroy` route or token exists anywhere in the
bundle. The two API candidates below were each tried once and neither removed
the throwaway (kept for the record). Removal is done on the filesystem instead —
see "Confirmed removal mechanism" below.

### `DELETE /api/skills/<name>` — **HTTP 405 Method Not Allowed**

```json
{ "detail": "Method Not Allowed" }
```

The path exists but does not accept DELETE. **This is the route the current
`hermes_desk_rebuild.py` delete path calls** — so that path is broken as
written and must be replaced. It was never a real route; it was assumed.

### `POST /api/skills/hub/uninstall` — **HTTP 200, but a no-op here**

```json
{ "ok": true, "pid": 1416, "name": "skills-uninstall-zz-throwaway-rebuild-test-6a49cb54" }
```

Returns `ok: true` with a background-job pid — but **the skill was still present
afterwards**: reading it back returned 200 with full content, and the skill list
still contained it. The reason is in the metadata:

- The throwaway (like all 8 desk skills) has **`provenance: "agent"`**.
- `hub/uninstall` is for **hub-installed** skills only. For an agent-authored
  skill the job runs and reports `ok` but removes nothing.

So `ok: true` from this route does **not** mean the skill is gone — it must
always be confirmed with a read-back (expect 404), never trusted on the
response alone.

### Confirmed removal mechanism (probed live, 24 Jul 2026)

Skills are files inside the Hermes **Docker container**, not on the host
filesystem. The `path` the API returns (`/opt/data/skills/<category>/<name>/`)
is a container-internal path — it does **not** exist on the VPS host directly.

- Host access: `ssh deploy-vps` (config already present: user `deploy`, host
  `srv1842904` / 187.127.208.203).
- Container: `hermes-agent-07ie-hermes-agent-1`, image
  `ghcr.io/hostinger/hvps-hermes-agent:latest`. Reached via `docker exec`.
- Layout inside the container: `/opt/data/skills/<category>/<name>/SKILL.md`,
  owned `hermes:hermes`. Trading skills live under `…/trading/`; the throwaway
  was under `…/testing/` — categories are separate directories.

Removal that worked — delete the skill's own directory, then confirm via API:

```bash
C=hermes-agent-07ie-hermes-agent-1
ssh deploy-vps "docker exec $C rm -rf /opt/data/skills/testing/zz-throwaway-rebuild-test"
# then verify from the API side:
#   GET /api/skills                    -> throwaway absent
#   GET /api/skills/content?name=...    -> 404
```

**The API reflects the deletion immediately — no service restart or reload was
needed.** After the `rm`, `GET /api/skills` dropped the skill and
`GET /api/skills/content?name=zz-throwaway-rebuild-test` returned 404, with no
restart of the Hermes container. (If a future removal does NOT show up in the
API, that implies a cache and would need a reload — do not restart the service
without an explicit decision; a restart interrupts the live desk.)

**Danger — this is `rm -rf` against a real, irreversible path.** Safeguards used,
and mandatory before ever pointing this at a real skill:

1. Verify the exact directory exists and its `SKILL.md` content matches the
   intended skill BEFORE the `rm` (a wrong name here is unrecoverable — there is
   no undo, no soft-delete).
2. Never interpolate a name into the `rm` from a list or variable that could
   hold a real skill; the path must be the literal throwaway/target, checked by
   eye. Real desk skills live under `…/trading/`; a removal command must never
   reference that directory or any of the 8 names.
3. Confirm the parent category dir isolates the target (here `testing/` held
   only the throwaway) so a mistyped path can't glob a sibling.

This mechanism is **filesystem-level and outside the API**, so it is NOT
something the `hermes_desk_rebuild.py` HTTP flow can do. The script's invented
`DELETE /api/skills/<name>` path (405, below) must be removed; if the rebuild
ever needs to delete rather than update-in-place, it has to shell out over SSH
with the safeguards above — which is a good reason to prefer update-in-place
(`PUT /api/skills/content`) and delete nothing.

### The throwaway (cleaned up)

`zz-throwaway-rebuild-test` was created, read, updated, and **removed** by this
probe. Final state confirmed: skill count back to 76 (baseline), throwaway
absent from the API list and 404 on read, gone from disk, all 8 trading skills
present. The now-empty `testing/` category directory was left in place (removing
it was out of scope — "remove that one directory").

---

## Desk integrity after the probe

Baseline before: **76 skills**. After create: **77** (the throwaway only).
After filesystem removal: back to **76** — final set exactly equals baseline
(zero net added, zero removed). All 8 trading skills unchanged throughout:
`apollo, atlas, desk-coordinator, hephaestus, hermes-execution, hydra, lumen,
mnemosyne`. No real skill was sent to any mutating call or destructive command
(enforced by a guard that aborts on any non-throwaway name, plus by-eye
verification of the `rm` path against live `SKILL.md` content).

## Summary table

| Op | Route / mechanism | Method | Result | Notes |
|----|-------|--------|---------|-------|
| Create | `/api/skills` | POST | 200 | `{name, content, description, category}` |
| Read   | `/api/skills/content?name=` | GET | 200 | only route returning `content` |
| List   | `/api/skills` | GET | 200 | metadata only; `name=` filter ignored |
| Update | `/api/skills/content` | PUT | 200 | `{name, content}`; full rewrite |
| Disable | `/api/skills/toggle` | PUT | — | `{name, enabled, profile}`; disables, does NOT remove |
| Delete (API) | `/api/skills/<name>` | DELETE | **405** | not a real route — script must stop using it |
| Uninstall | `/api/skills/hub/uninstall` | POST | 200 | **hub-only**; no-op for `provenance: agent` |
| **Remove (real)** | `docker exec … rm -rf …/<cat>/<name>` | SSH | ✓ | filesystem only; API reflects it immediately, no restart |
