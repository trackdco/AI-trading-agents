# HANDOFF — Angus's session, 2026-07-27 (boot a fresh chat from this file)

**You are talking to ANGUS** — strategy authority and final say. He makes rulings; Claude
measures and builds and NEVER changes strategy unilaterally. Pat builds the engine and runs
the VPS/Sierra box (Pat now drives the prior session's chat). Brake handles data. Angus is
in AEST (UTC+10) — convert times for him, he calls out sloppy timezone math. He wants
things explained plainly ("explain like I'm an idiot" is a standing request, not an insult
to him or you), step-by-step when he's executing, and he reads consistency (months green)
before totals. Screenshots are how he shows you the box/phone; read them carefully.

---

## 1. WHERE THINGS STAND (launch day)

The bot goes LIVE on the funded Lucid 50k at TODAY'S NY session (pre-market 08:00 ET =
22:00 AEST) if the last human steps land. As of commit `7a0b6b7`:

- **Arming reference:** +$55,989.81 / 383 trades (`output/baseline_book_news.parquet`),
  13/13 months green, maxDD $1,357. Certified on the box twice today, 383/383 exact.
  London book +$21,506/136, untouched by all corrections.
- **Everything code-level is GREEN and on-box verified:** order surface vs live Rithmic
  paper (A7/B7/B8 "all checks passed"), spine rules 11/11 (C5), both kill switches (C4),
  feed lag median 2.79s (B6), news sentinel fully automated, DD ramp + −4R daily halt
  signed and shipped. Eight real bugs were found on the box today and fixed — that was
  the point of the gates.
- **Right now:** the runner is DISARMED, shadowing the London session (03:00–05:50 ET =
  17:00–19:50 AEST), journaling every would-be decision. The kill listener runs as its
  own process. Nothing can place an order yet.
- **Remaining sequence:** after London → C2/C3 drills (kill+restart runner, feed-stall) →
  final cert at the FINAL commit → **Pat's written confirmation** (gates checked against
  artifacts; must name the 383/+$55,989.81 numbers and the commit SHA) → **Angus's
  arming token** (§2) → `canon_run --arm` on the box → NY trades autonomously.

## 2. ANGUS'S PENDING ACTIONS — the things only he can do

1. **The arming token (the big one).** When Pat's written confirmation arrives:
   - Angus invents a passphrase (any words) and gives THIS chat: the phrase + the commit
     SHA from Pat's confirmation + the funded account name (exact Rithmic string).
   - This chat then writes `config/arming.yaml` with THREE fields — `token_sha256`
     (SHA-256 hex of the exact phrase; the phrase itself NEVER enters the repo),
     `armed_sha` (the certified commit), `account` — commits ONLY that file on top of the
     certified commit, and pushes. Template and enforcement live in `src/live/arming.py`;
     the runner refuses to arm if the phrase doesn't hash to the file, if HEAD differs
     from armed_sha by anything except arming.yaml, or if the DTC logon fails.
   - Angus sends Pat JUST the phrase. Pat runs `python -m scripts.canon_run --arm`, types
     it → 🔴 ARMED alert in Telegram names the commit. Neither of them can arm alone.
2. **Day-one posture (PROMOTION-GATE §F):** watch Telegram with /kill one tap away, judge
   NOTHING by P&L — a losing day that followed the rules is a pass; only gate breaches
   matter (§D halts fire automatically either way). No touching, no tweaking.
3. **Rulings parked for AFTER launch** (each needs the freeze → two-way OOS → sign-off →
   new book pipeline): post_open_min_stop=10 (his own 20-Jul rule — verification says it
   deletes +14.1R of winners, needs his call), the 10-min dead-trade cut (3→10min layer),
   early-golden d15∧wall refinement (blind-OOS confirmed), partial+trail exit family,
   walk_menu target clamp + fill-time min-stop recheck.

## 3. HIS STANDING RULINGS (the law of the repo — never relitigate silently)

- **Mechanical only** (docs/RULING-mechanical-only.md, verbatim ruling): no agent
  discretion in the trade path while the engine is profitable; agents follow the rulebook.
  Discretionary improvements are a LATER project, after live journals accumulate.
- **Consistency is the objective function** — months green > total P&L.
- **Adopted:** pre-open news blackout (block entries before pre-9:30 promoted-high
  releases; post-print entries fine; fail closed with no snapshot); 09:55–10:00 dead-zone
  cut; −4R daily halt INDEXED to the day's base_dollar; DD ramp $1,500→$0 at $100
  (replaced the $250 cliff); keep FOMC days; no paper period (the eval IS the test);
  09:30–09:40 stays cut by doctrine ("I wait to see what the open gives me").
- **Retracted after adversarial check:** rr_floor 1.5 (a single freak fill drove it; the
  floor stays 2.0). Lesson he holds us to: "independent confirmations" must use disjoint
  substrates. Also killed: −2R day halt, $400 DD buffer, late-a fade subset, loss-count
  halts.
- Raw market data never goes to GitHub. Branch `claude/getting-started-6lwnvs` only, no
  PRs unasked.

## 4. WHAT PAT'S CHAT IS DOING (so this chat doesn't collide)

Pat drives the box session: London-shadow evidence, C2/C3 drills, final cert, the written
confirmation, and next the **2023/2024 out-of-regime random-days test** (brief in
docs/HANDOFF-pat-session-2026-07-27.md). Code pushes to the trade path are FROZEN until
the certified commit is armed (the provenance check refuses to arm past uncertified
changes). This chat's lane: Angus-side decisions, the arming.yaml commit, rulings,
strategy questions, and reading results Pat's chat produces.

## 5. RESEARCH THREADS ANGUS OWNS (context for future asks)

- **Walk-forward chained agent run** — designed, not yet built: Pat's agents replayed
  day-by-day from June 2025, journals immutable, delta vs the mechanical anchor,
  adaptation curve. Angus's caveat on record: remove-only agents likely hurt (win rate
  already good); "avoided losers is obviously the goal"; discretion is for later.
- **Golden window** — his personal edge (docs/GOLDEN-WINDOW-DISSECTION.md): canon captures
  5 of his 45 hand-logged trades / 14% of his P&L; 70% dies at the engine layer. The
  frequency gap is the big open question for after launch.
- Key docs: PROMOTION-GATE.md (authoritative gate), STATUS-go-live-checklist.md,
  GO-NOGO-2026-07-27.md, HEADLINE-NUMBERS.md, RULING-daily-loss-limit.md,
  FINDING-rr-floor-study.md, LONG-WALK-2023-2026.md.

## 6. NUMBERS HE QUOTES FROM MEMORY (don't contradict them without evidence)

+$55,989.81 / 383 (arming reference) · London +$21,506/136 · 13/13 months green · maxDD
$1,357 · 1R = $200 floor · −4R = −$800 at today's cushion · ramp $1,500→$0 at $100 ·
win 52.2% · canon fires ~3.8 trades/week · feed lag 2.79s median · NQ data symbol
NQU6.CME, orders MNQU6.CME at price_scale 100 · paper account LFE050-9YSC047M-TEST001.
