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

## Removal — ⚠️ OPEN FINDING: no confirmed removal route for agent-provenance skills

Two candidates were each tried **exactly once** against the throwaway. Neither
removed it.

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

### Consequence

The correct removal mechanism for `provenance: "agent"` skills is **not yet
known** — it is likely a different route (a `skill_manage` action, or a
DELETE/POST shape not present in the dashboard bundle) and needs its own probe
before any real deletion is attempted. Until then, the rebuild's delete phase
cannot be trusted, and the update-in-place plan (which needs no deletes for the
three mappable skills) is the safer path.

### Left behind by this probe

`zz-throwaway-rebuild-test` is **still live on the host** because neither
removal route worked. It is inert (`enabled: true`, `usage: 0`, category
`testing`) and harmless, but should be cleaned up once a working removal route
is found. Per the test's no-retry rule, no further removal attempts were made.

---

## Desk integrity after the probe

Baseline before: **76 skills**. After create: **77** (the throwaway only).
All 8 trading skills unchanged throughout:
`apollo, atlas, desk-coordinator, hephaestus, hermes-execution, hydra, lumen,
mnemosyne`. No real skill was sent to any mutating call (enforced by a guard
that aborts on any non-throwaway name).

## Summary table

| Op | Route | Method | Success | Notes |
|----|-------|--------|---------|-------|
| Create | `/api/skills` | POST | 200 | `{name, content, description, category}` |
| Read   | `/api/skills/content?name=` | GET | 200 | only route returning `content` |
| List   | `/api/skills` | GET | 200 | metadata only; `name=` filter ignored |
| Update | `/api/skills/content` | PUT | 200 | `{name, content}`; full rewrite |
| Delete | `/api/skills/<name>` | DELETE | **405** | not a real route — script must stop using it |
| Uninstall | `/api/skills/hub/uninstall` | POST | 200 | **hub-only**; no-op for `provenance: agent` |
