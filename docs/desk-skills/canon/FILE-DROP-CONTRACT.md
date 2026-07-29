# Canon desk — file-drop contract (corrected) + open wiring question

Records how Hermes connects to the trading pipeline **under the canon**, after the desk
swap (8 judgment skills disabled; `hermes-router`, `canon-relay`, `desk-journaler`,
`hermes-risk` created). The correction below matters because the existing Python receiver
(`src/desk/receiver.py`) was built for the *old* LLM-Hermes and its direction is now
reversed.

## The old contract (LLM-Hermes) — now obsolete

`src/desk/receiver.py` header: *"Hermes (third-party) writes one verdict JSON file per
candidate into a watched directory; this receiver reads each new file, runs it through
`validate_verdict` (the Python trust boundary — re-checks Hermes's arithmetic), risk-gates,
and journals."* Direction: **LLM-Hermes → verdict → Python validates/gates/journals.**
`src/desk/verdict.py` exists precisely because *an LLM produced the numbers and Python could
not trust them.*

## The corrected contract (canon) — Python decides, Hermes narrates

Under the authoritative canon ruling (`docs/FOR-ANGUS-desk-spec-questions.md:262`,
`docs/LIVE-STACK.md:169`), the **verdict is frozen deterministic Python** — the canon
scorers (`scripts/canon_mechanical.py`, `scripts/london_canon.py`, which passed PARITY-CHECK
400/400, +$56,065.18), the feature ingestor, the dollar-risk sizer, and the safety spine.
There is **no LLM in the trade path**. So the drop **reverses**:

```
Python canon (route → checks → score → OF stack → size → safety spine)
        │  produces the verdict + the full journal record
        ▼
   verdict drop (atomic write into a watched dir)
        ▼
   canon-relay   → relays the verdict verbatim to the order path (yes-only; no validation,
                    no re-derivation, no veto — the numbers are already trusted, being Python's)
   desk-journaler→ mirrors/narrates the Python journal record (source of record stays Python)
   hermes-risk   → watches feed/heartbeat/spine; can only halt/flatten via output/live/KILL
   (Telegram narration fires from the Vault/Python side per the architecture invariant —
    docs/telegram-setup.md §"Architecture boundary" — never from an agent)
```

Consequences for the existing code:
- **`verdict.py`'s arithmetic re-check is no longer load-bearing for trust** — the numbers
  are Python's own, not an LLM's. Keep the schema/validation as a cheap integrity check on
  the drop, but it is no longer *the* trust boundary.
- **`receiver.py`'s risk-gate + journal roles stay** — every order still passes the same
  deterministic guards and lands in the same journal. Only the "distrust the producer" framing
  goes away.
- **Hermes is optional to the trade path** (`docs/LIVE-STACK.md:181`: "Optional Claude Agent
  SDK for orchestration/journaling — not per-tick"). If the desk agent is down, the Python
  pipeline still routes, sizes, guards, journals, and (once armed) executes. Hermes adds
  narration/journaling/watchdog *around* it, never *in* it.

## Open wiring question for Angus

The docs attribute **routing** and **journaling** to both sides and this is not pinned down:

- `docs/LIVE-STACK.md:96` — *"Router + brain (Hermes)"*; `docs/FOR-ANGUS-desk-spec-questions.md:271`
  — *"Session routing (Hermes)"* → attribute routing/journaling to the **agent**.
- `docs/LIVE-STACK.md:180` (stack table, row 6) — the **Python stack** owns *"router …
  journaler"*; row 7 makes the agent runtime *"optional … not per-tick."*

**Decision needed:** does the load-bearing **session router** and the **system-of-record
journal** run as **Python** (with `hermes-router`/`desk-journaler` as thin narration mirrors),
or as **Hermes skills** that Python falls back to? The decision-**authority** is unambiguous
either way — it is the frozen canon, no LLM — but *where the router/journaler physically
execute* changes the wiring and the failure model (a Hermes outage must never stop the trade
path, which argues for Python-owns / Hermes-mirrors).

Recommended default until Angus rules: **Python owns router + journal + the verdict; Hermes
mirrors/narrates/watches.** This keeps the trade path alive without the agent and matches
"no LLM in the trade path." Nothing about arming changes — live order submission stays gated
behind the human sign-off chain (parity ✓ + reconciliation + shadow + spine force-tests).
