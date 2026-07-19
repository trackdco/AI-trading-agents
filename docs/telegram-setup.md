# Telegram Alerting — Setup Notes (Phase 4 prep)

Status: **bot + group created (2026-07-17). Not wired to code yet** — the Vault
live loop (Phase 4) consumes this. Recorded here so Phase 4 builds it correctly.

## What exists

- **Bot:** `@brucewaynemrcrabs_bot` (created via @BotFather).
- **Group:** small group ("NQ Desk Alerts") containing Pat, Angus, and the bot.
- **Token:** lives ONLY in `.env` as `TELEGRAM_BOT_TOKEN` (gitignored). Never commit it.
  - Token history: the original BotFather token appeared in screenshots shared during
    setup (team chat 2026-07-17; setup session 2026-07-19). Rotation was recommended;
    **Pat's ruling (2026-07-19, reaffirmed): keep the existing token** — all
    screenshots stayed within the team (Pat + Angus), so it is judged not compromised.
    Recorded here so the decision and its context are auditable. Standing rules
    unchanged: the token lives ONLY in `.env` (gitignored), never in the
    repo/commits; if it ever leaks beyond the team, `/revoke` at @BotFather and
    rotate `.env`. Worst-case blast radius of this token is messaging-as-the-bot —
    it grants no trading control (inbound commands are locked to allowed Telegram
    user IDs, and the kill switch can only ADD safety).
  - Setup hazard hit in practice (2026-07-19): impostor "user info" bots. Pat messaged
    two bots whose display names mimicked @userinfobot and @RawDataBot but whose real
    usernames were @OTUSSSBOT / @OH_RawDataBot — neither replies, both are copycats
    (only harmless text was sent; chats deleted). Team rule: never use third-party
    info bots to find a user id — DM OUR bot and run
    `python -m src.live.telegram --whoami` instead.
- **Group chat ID:** `-5356314891` (basic group — no `-100` supergroup prefix; if
  Telegram later upgrades it to a supergroup the ID changes to a `-100…` form and must
  be re-read). Goes in `.env` as `TELEGRAM_CHAT_ID`. Not a secret on its own — useless
  without the bot token — so recorded here; Phase 4 copies it into `.env`.
- **Angus's personal user ID:** needed for the command lock below. TODO: obtain from
  @userinfobot, store as `TELEGRAM_ANGUS_USER_ID` in `.env`.

## Architecture boundary (NON-NEGOTIABLE — strategy §11, architecture invariant 6)

**Alerts fire from the VAULT only, after the risk check. No LLM/agent touches Telegram.**

```
Engine → Desk (Atlas/Helios/Apollo/Hephaestus → Hermes)  →  Vault (Python)  →  Telegram
                        proposes only                          risk-gates, then sends
```

- Hermes has **no outbound channel**. It hands a Verdict to the Vault and stops.
- The Vault is the only module importing the Telegram client. It has **no import path
  from any module that calls an LLM** (enforced in code + tests).
- This differs on purpose from the "Hermes → Telegram" shortcut some setups use: routing
  every message through the Vault guarantees nothing reaches a phone (or later, a broker)
  without passing max-trades/day, daily-loss halt, and the kill-switch.

## Direction rules

- **Outbound (alerts): broadcast to the group** (`TELEGRAM_CHAT_ID`). Everyone sees them.
- **Inbound (`/status` `/pause` `/flatten`): accept ONLY from Angus's user ID**
  (strategy §11 — "locked to Angus's chat ID"). In a group, anyone can type a command,
  so the handler must check the sender's user ID against `TELEGRAM_ANGUS_USER_ID` and
  ignore everyone else. This lock is a Phase-4 requirement, not optional.

## `.env` keys (see `.env.example`)

| Key | Value | Status |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | bot token from @BotFather (existing token retained — Pat ruling 19 Jul, reaffirmed) | pending |
| `TELEGRAM_CHAT_ID` | `-5356314891` (basic group) | captured ✅ |
| `TELEGRAM_ANGUS_USER_ID` | Angus's personal user ID from @userinfobot | pending |

## When this gets built

Phase 4 (Vault live loop). Nothing here runs until then. Creating the bot/group now
just means it's ready — cheap to do early per `context/next-tasks.md`.
