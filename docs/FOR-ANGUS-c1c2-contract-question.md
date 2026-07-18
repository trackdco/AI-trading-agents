# FOR ANGUS — C1/C2 learning loop vs the "agent never sees outcomes" contract

**Decision needed from you (strategy authority) before I wire the C1/C2 feedback.**

## The tension

Your v0.4 design (docs/PROPOSED-AGENT-ADJUSTMENTS-v0.4.md) includes:
- **C1** — each morning's briefing shows the agent its own running read-accuracy by
  miss class ("your event_risk calls: 2/9 correct").
- **C2** — regret lines: every intervention's counterfactual cost fed into the notes.

Both require putting the agent's **own past outcomes / P&L-derived numbers** into its
briefing. The frozen v0.3 desk contract (docs/agent-blueprint.md §, and the acceptance
criteria in TASK-FOR-PAT) says the opposite: *the agent never sees P&L, trade outcomes,
win rates, or account state, and must not infer them.* The reason that rule exists: an
agent shown its own scoreboard can develop account-preservation bias / tilt — it starts
managing its stats instead of reading the tape. C1/C2 deliberately relax that. Only you
can authorize the relaxation.

## What I have already built (safe, no ruling needed)

- **Analog block (A1)** — in the briefing now. This is *other* days' realized book P&L,
  used as retrieval context. It is not the agent's own record and carries no
  account-preservation incentive, so I judged it inside the contract and shipped it.
- **Scorecard + regret, computed to a LEDGER** (output/v04/<arm>_ledger.csv, _divergence.csv).
  Pure measurement for us — never shown to the agent. This needs no ruling.

## What I did NOT build (needs your ruling)

Feeding C1/C2 numbers back into the agent's briefing/notes. Options:

1. **Full C1+C2** — show read-accuracy AND per-intervention regret. Max learning signal,
   max contract departure and tilt risk.
2. **C1 only, framed as calibration not P&L** — show read-accuracy by miss class
   (a skill metric), withhold dollar regret. Learning signal without dollar-anchored
   loss-aversion. My lean if you want to relax the contract at all.
3. **Neither — keep the ledger external** — the analog block already injects the
   historical base rates the agent was missing; measure whether A1 alone closes the read
   gap before adding a self-referential loop. My lean if the June v0.4 result (below)
   shows the analog block moving reads on its own.

## Recommendation

Hold C1/C2 wiring until the **June v0.4 chain** (running now: analog block + fresh-eyes
panel, no C1/C2) is scored. If reads jump from the 38% v0.3 baseline toward your 60%+
target on the analog block alone, option 3 — the self-referential loop isn't worth the
contract departure. If reads stall, option 2 is the measured next step. Either way the
fresh-eyes divergence ledger will tell us whether memory is helping or entrenching, which
also bears on how much C1/C2 memory-feedback we want.

Your call on which option, and whether to wait for the June v0.4 number first.
