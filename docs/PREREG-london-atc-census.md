# PRE-REGISTRATION — LDN-ATC-01 — census of the pre-London pullback

**Committed BEFORE any data is pulled or scored.** Greenlit by Brakey 2026-08-05 off
`research/candidates/london-asian-trend-continuation.md`. Source: Tradesharpe
(`ci24AdpcRaA`), spec quoted in the candidate file.

Census only. **No P&L is computed at this stage and none may kill** (§5.9.1 as tightened:
census kills are reserved for structural absence alone).

## Hypothesis

The taught sequence occurs often enough to be a strategy: an Asian-session trend, then a
pullback against it in the hour before London open, then a multi-timeframe close back in
the trend direction.

## Mechanism

Through Asia, price trends in a thin book. In the hour before the London cash open it
retraces — the participants who pushed it are done, and there is no new size yet. Then
London opens, real European size arrives on the original side, and the retracement is
run over. **The trapped counterparty is whoever read the pre-London pullback as a
reversal** and is positioned against the session trend when the open arrives with no room
to be right.

**Mechanism family:** overnight structure / session-handoff continuation.

## Windows — declared in Europe/London, converted per day (DST-correct)

The source never gives clock times; he uses a TradingView session indicator and the phrase
*"an hour before London open"*. These are my mechanisations, frozen here:

| element | window (Europe/London) |
|---|---|
| Asian session | **00:00–07:00** |
| Last half of Asian (the bias window) | **03:30–07:00** |
| Pre-London pullback window | **07:00–08:00** |
| Trigger evaluation | 15m closes from **07:00 to 09:00** |
| Hard flat | **10:00** (`LDN-WIN-01`: 10:00–11:00 London is the worst hour in the session) |

## Definitions — frozen, and flagged where they are mine not his

1. **Asian trend (bias).** Split 03:30–07:00 into two halves. **Bearish** if the second
   half's high AND low are both below the first half's; **bullish** if both above;
   otherwise **no bias and no signal**. This is "lower highs and lower lows" in its
   simplest unambiguous form. *Mine, not his — he says the words and draws it by eye.*
2. **Pullback.** In 07:00–08:00, price trades against the bias beyond the 07:00 price.
   No minimum size — he states none, and adding one would be tuning at census.
3. **LTA (low traffic area).** His rule is mechanical: *"when a candle closes bearish and
   the next one closes bullish, that creates a support; when a candle closes bullish and
   the next closes bearish, that creates a resistance."* A stretch with neither is an
   LTA. So: **≥2 consecutive 15m closes in the pullback direction** inside 07:00–08:00.
   *The translation from his words to "≥2 consecutive" is mine and is flagged in the
   verdict.*
4. **Trigger (default).** A 15m close AND its containing 30m close, both in the bias
   direction, at any 15m boundary in 07:00–09:00. First occurrence per day.
5. **Trigger (declared fallback arm, not the default).** 30m AND 1h both closing in the
   bias direction, even if one 15m closed weakly against — as he states.

## Census kill line (§5.9.1) — structural absence only

**LDN-ATC-01 dies at census ONLY if the taught sequence does not happen:** the full chain
(bias → pullback → aligned trigger) completing on **< 15% of sessions in either era**.

**Raw profitability is not computed and cannot kill here.** Ugly economics send this to
the variable search; they do not close the family.

## Reported as a funnel with terminal statuses (§5.12.1)

Every session gets a terminal status and the distribution is reported, no silent drops:
`no_bias` / `bias_no_pullback` / `pullback_no_lta` / `lta_no_trigger` / `triggered`.

## Declared up front, so later rungs cannot be accused of inventing them

- **Event-universe sensitivity (§5.11.2):** first-trigger-per-day is the default;
  **all-triggers** is reported alongside at census so the frequency ceiling is known
  before any economics exist.
- **Half-year reporting (§5.11.5):** every table split 2025H1/H2, 2026H1/H2 as well as by
  era. Calendar-year pooling has hidden a losing half twice in this programme.
- **Lookahead audit (§5.11.7):** every element above reads only bars that closed at or
  before the decision minute. The bias window ends at 07:00 and the trigger is evaluated
  on closed candles only. To be certified in the run, not assumed.
- **Basis stamp (§5.12.13):** NQ 1-minute bars from `nq_1m_master.parquet` +
  `nq_1m_feb_jul2026.parquet`, sessions with ≥ 200 one-minute bars in 00:00–10:00 London.
- **Feature semantics (§5.12.15):** the "LTA" column will be cross-tabbed against what it
  actually computes before any verdict cites it. I mis-described `W` this way three hours
  ago; the check is now mandatory for me, not optional.

## Spans

Discover **2025**, validate **2026** (to 2026-07-15). **2023/24 NOT TOUCHED. Holdout
look: NO.**

## Known limits, stated before the run

- **Instrument.** The source demonstrates on gold and claims forex. He never names NQ.
  NQ applicability is an assumption and the verdict says so either way.
- **His no-trade rule is dropped.** *"If it's going to range like this, I'm not
  interested"* is not same-time computable. Every signal is counted. **The tested spec is
  therefore stricter than the taught one**, and that is recorded rather than quietly
  ignored.
- **Three definitions above are mine, not his** (bias split, pullback, ≥2-consecutive
  LTA). A census that passes on my mechanisation is evidence about my mechanisation.

## Artifacts

`scripts/london_atc_census.py`, `output/london_atc_census.md`, trials to
`output/trial_ledger.parquet`, card in `research/FUNNEL.md` per §5.10.
