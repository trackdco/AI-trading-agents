# Telegram Alerting — Setup Notes (Phase 4 prep)

Status: **bot + group created (2026-07-17). Not wired to code yet** — the Vault
live loop (Phase 4) consumes this. Recorded here so Phase 4 builds it correctly.

## What exists

- **Bot:** `@brucewaynemrcrabs_bot` (created via @BotFather).
- **Group:** small group ("NQ Desk Alerts") containing Pat, Angus, and the bot.
- **Token:** lives ONLY in `.env` as `TELEGRAM_BOT_TOKEN` (gitignored). Never commit it.
  - ⚠️ The original BotFather token was shown in a screenshot in chat — **regenerate
    it via @BotFather `/revoke` before go-live** and put the fresh token in `.env`.
- **Group chat ID:** goes in `.env` as `TELEGRAM_CHAT_ID` (a negative number, e.g.
  `-100…`). Obtained from @getidsbot. TODO: paste value into `.env`.
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
| `TELEGRAM_BOT_TOKEN` | bot token from @BotFather (regenerate before go-live) | pending |
| `TELEGRAM_CHAT_ID` | group chat ID from @getidsbot (negative number) | pending |
| `TELEGRAM_ANGUS_USER_ID` | Angus's personal user ID from @userinfobot | pending |

## When this gets built

Phase 4 (Vault live loop). Nothing here runs until then. Creating the bot/group now
just means it's ready — cheap to do early per `context/next-tasks.md`.
