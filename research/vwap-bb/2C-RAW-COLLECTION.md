# 2C — RAW MECHANICAL COLLECTION (no adjudication)

**Written 2026-08-08, overnight queue, item 7 SPLIT — mechanical half only.**
**No disagreement below has been classified. No isolation verdict has been rendered. No
resolution in `AMBIGUITIES.md` has been checked against its cited clause. That is explicitly
reserved for the morning.**

Detector pinned to commit `bab2e0364db9e8cf315027e5cddc9bb37b4a03af` (`bab2e03`), via a detached
`git worktree`, because A14/A15 are about to be written into `spec_current.py` and diffing
against a moving detector would make every disagreement pure A14/A15 noise rather than evidence
about the blind build. `strategy-definition-v1.0.md` inside that worktree hashes to
`42d6f0f68ed35bef0280be782c58f72059333222047841473ab74d5b9fbd83bf` — the same spec the blind
build worked from, confirmed below.

The blind build's own bar-data cache (`_nq_frontmonth.pkl`) is gitignored, so it was symlinked
(not copied) into the worktree; both paths hash identically, confirmed below. No source file was
otherwise modified in the worktree.

Rerunning `diff_2c.py` inside the pinned worktree reproduced byte-identical summary statistics to
the unpinned run performed earlier the same session, which is expected since no detector commit
separates the two — recorded so the numbers below are not mistaken for a second, different
measurement.

---

## 0. Pin verification

```
worktree HEAD                         : bab2e0364db9e8cf315027e5cddc9bb37b4a03af
strategy-definition-v1.0.md (worktree): 42d6f0f68ed35bef0280be782c58f72059333222047841473ab74d5b9fbd83bf
_nq_frontmonth.pkl (worktree symlink) : 1dc566edf998bb181f4313f3350c2deddae312402916b3d7e6a8c01a48d30abe
_nq_frontmonth.pkl (main tree)        : 1dc566edf998bb181f4313f3350c2deddae312402916b3d7e6a8c01a48d30abe
```

## 1. Raw diff summary

```
detector trades (pinned bab2e03)         : 1,472
blind build trades (blind_trades.json)   : 1,583
present in BOTH (exact key match)        : 20
detector only                            : 1,452
blind only                               : 1,563
key match, geometry differs (tol 0.01)   : 20
TOTAL DIFF                               : 3,035
```

Key = `(session_date, signal_minute, entry_tf, direction)`. Geometry compared =
`(fill_price, stop_price, target_price)`, tolerance 0.01.

**detector-only, by (entry_tf, direction):**
`{(3, 'short'): 164, (5, 'long'): 106, (3, 'long'): 175, (2, 'short'): 150, (2, 'long'): 180, (1, 'long'): 288, (1, 'short'): 307, (5, 'short'): 82}`

**blind-only, by (entry_tf, direction):**
`{(2, 'short'): 154, (5, 'long'): 92, (1, 'long'): 407, (5, 'short'): 83, (2, 'long'): 183, (3, 'short'): 120, (1, 'short'): 376, (3, 'long'): 148}`

**geometry diffs by field (of the 20 key-matches with a difference > 0.01):**
`{'entry': 20, 'stop': 20, 'target': 20}` — every one of the 20 key-matches disagrees on all
three of entry, stop and target simultaneously; none agrees on any one field while differing on
another.

Full raw lists (not reproduced inline — too large to be useful as prose):

| file | rows | content |
|---|---|---|
| `data/2c-raw/only_detector_full.txt` | 1,452 | every `(date, minute, tf, direction)` present in the detector's list and absent from the blind build's |
| `data/2c-raw/only_blind_full.txt` | 1,563 | the mirror |
| `data/2c-raw/geometry_full.txt` | 20 | every key-match, with both sides' (entry, stop, target) |
| `data/2c-raw/diff_2c_result.json` | — | the complete machine-readable diff, superset of the above |
| `data/2c-raw/blind_trades.json` | 1,583 | the blind build's full output, copied verbatim |

## 2. Widened identifier and magic-number grep

Ran against `blind_impl.py` and `sensitivity.py`. Full output, verbatim, also saved at
`data/2c-raw/identifier_and_magic_number_grep.txt`:

```
=== NARROW IDENTIFIER GREP (names) ===
  RunningVWAP : 0
  cluster_levels : 0
  tie_break : 0
  def trig : 0
  trig( : 0
  LOC_BAND : 0
  FRONT_RUN_F : 7
  B_MIN : 3
  QUARTILE : 3
  MIN_STOP : 0
  RR_FLOOR : 2
  POC_BIN : 4
  FRACTAL_N : 8
  NY_VWAP_ANCHOR : 0
  FIRST_SIG : 2
  EOD_FLATTEN : 2
  htf_flag : 2
  signal_candidates : 0
  admit_current : 0
  contract_key : 0
  spec_current : 0
  stage2_smoke : 0
  vwapbb_signals : 0
  vwapbb_opportunity : 0
  vwapbb_a7_selector : 0
  alpha_data : 0
  _nq_frontmonth : 0

=== MAGIC NUMBERS ABSENT FROM THE SPEC (checked against SPEC.md) ===
  pattern '0\.25'  in SPEC.md: 1   in blind_impl.py: 2
  pattern '0\.6\b'  in SPEC.md: 3   in blind_impl.py: 1
  pattern '0\.75\b'  in SPEC.md: 1   in blind_impl.py: 0
0
  pattern '10\.00'  in SPEC.md: 6   in blind_impl.py: 3
  pattern '1\.5\b'  in SPEC.md: 3   in blind_impl.py: 1
  pattern '2\.0\b'  in SPEC.md: 0
0   in blind_impl.py: 2
  pattern '2\.5\b'  in SPEC.md: 0
0   in blind_impl.py: 1
  pattern '3\.0\b'  in SPEC.md: 0
0   in blind_impl.py: 1
  pattern '20\b'  in SPEC.md: 18   in blind_impl.py: 6
  pattern '\bN=2\b'  in SPEC.md: 5   in blind_impl.py: 1
  pattern '0\.20\b'  in SPEC.md: 1   in blind_impl.py: 0
0
  pattern '15'  in SPEC.md: 16   in blind_impl.py: 18
  pattern '240'  in SPEC.md: 2   in blind_impl.py: 0
0
  pattern '1080'  in SPEC.md: 0
0   in blind_impl.py: 2
  pattern '930'  in SPEC.md: 0
0   in blind_impl.py: 2
  pattern '576'  in SPEC.md: 0
0   in blind_impl.py: 1
  pattern '960'  in SPEC.md: 0
0   in blind_impl.py: 0
0
  pattern '1.959964'  in SPEC.md: 0
0   in blind_impl.py: 0
0
  pattern '1\.96\b'  in SPEC.md: 0
0   in blind_impl.py: 0
0
  pattern '5\.00\b'  in SPEC.md: 9   in blind_impl.py: 2

=== FUNCTION / CONSTANT NAMES DEFINED IN blind_impl.py ===
35:TICK = 0.25                 # NQ tick.  A5: "10.00 points (40 ticks)" => tick = 0.25
36:CLUSTER_TOL = 10.00         # §3 tolerance, CALIBRATE start "~10 NQ pts"; pinned by A13
38:TOL_HALF = CLUSTER_TOL / 2  # A13 right-hand side = 5.00
41:BB_PERIOD = 20              # §2 table "Bollinger Bands | 20, SMA, close, 2σ"
42:BB_SIGMA = 2.0              # §2 (bands themselves are not §3 cluster levels; basis only)
44:ATR_PERIOD = 20             # §3 "range >= k x ATR(20)"
45:ATR_K = 1.0                 # §3 CALIBRATE start k = 1.0
46:B_MIN = 0.6                 # §3 displacement body/range, CALIBRATE start 0.6
47:EXTREME_QUARTILE = 0.25     # §3 "close within the extreme quartile of the candle's range"
49:STOP_BUFFER = 1 * TICK      # A2 "stop buffer = 1 tick beyond the wick extreme"
50:STOP_MIN = 10.00            # A5 "effective stop = max(structural stop, 10.00 pt)"
52:RR_FLOOR = 1.5              # §6.5 / A4 "first level whose front-run-adjusted distance is >= 1.5R"
53:FRONT_RUN_F = 2.5           # §6.4 F: CALIBRATE (start 2-3 NQ pts) -> midpoint  [see AMBIGUITIES A-08]
55:POC_BIN = 1.00              # A2 "volume-profile bin = 1.00 pt"
56:FRACTAL_N = 2               # A2 "15m fractal swings N=2"
57:HTF_TF = 15                 # §1 "Context TFs: 15m for HTF trend/range flag"
59:CONF_MIN_WITH_TREND = 2     # §7 "Confluence minimum: 3 counter-trend; 2 with-trend"
60:CONF_MIN_COUNTER = 3
61:SESSION_CAP = 3             # §10.1(3) / §10.2 "Max trades/day: 3"
63:ENTRY_TFS = (1, 2, 3, 5)    # §1 "Entry TFs: 1m, 2m, 3m, 5m"
66:FIRST_SIGNAL_MIN = 9 * 60 + 36    # 576  — A1 "first tradeable signal bar 09:36"
67:LAST_SIGNAL_MIN = 15 * 60 + 59    # 959  — A1 entry window ends 16:00 ET
68:NY_ANCHOR_IDX = 9 * 60 + 30 + 360   # 930 — §2 NY VWAP anchored 09:30 ET
69:EOD_FLATTEN_IDX = 15 * 60 + 55 + 360  # 1315 — §1 "default 15:55 ET"
70:LAST_FILL_IDX = 16 * 60 + 360         # 1320 — §1 entry window closes 16:00 ET
71:N_SESSION_IDX = 1380
73:SEAL_DATE = "2025-01-31"    # TASK.md — never process a session after this
85:OPT = {
95:DEBUG = {}   # diagnostics sink; never read by the strategy logic
98:def idx_of_minute(mm):
102:def _mean(xs):
110:def running_vwap(bars, anchor_idx):
145:def running_poc(bars):
176:def build_tf_bars(bars, k):
206:def attach_bb_atr(tfb):
243:def fractal_swings(b15):
267:def htf_flag(sw_h, sw_l, e):
288:def find_clusters(levels):
325:def cluster_types(cl):
333:def process_session(date, bars, prior):
653:def simulate_fill(bars, start_idx, end_idx, limit, direction):
676:def simulate_exit(bars, fill_idx, stop, target, direction):
702:def build_prior_levels(all_sessions, dates):
741:def main():

=== DETECTOR'S FUNCTION/CONSTANT NAMES, FOR COMPARISON (from the pinned worktree) ===
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_signals.py:20:NY = ZoneInfo("America/New_York")
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_signals.py:21:WORKBENCH_END = "2025-01-31"
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_signals.py:23:NY_VWAP_ANCHOR = 9 * 60 + 30
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_signals.py:24:TFS = (1, 2, 3, 5)
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_signals.py:26:CLUSTER_TOL = 10.0          # §3, CALIBRATE start ~10 NQ pts
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_signals.py:27:BB_N = 20                   # §2
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_signals.py:28:B_MIN = 0.6                 # §3, CALIBRATE start
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_signals.py:29:QUARTILE = 0.75             # §3 close in extreme quartile
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_signals.py:30:POC_BIN = 1.00              # gate 4 [FIAT]
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_signals.py:31:FRACTAL_N = 2               # gate 4 [FIAT]
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_signals.py:35:def build_sessions():
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_signals.py:53:def minute_of_day(idx: int) -> int:
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_signals.py:59:class RunningVWAP:
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_signals.py:80:def cluster_levels(levels, tol=CLUSTER_TOL):
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_signals.py:99:def htf_flag(bars15):
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_signals.py:122:def triggers(o, h, l, c, cl_lo, cl_hi, n_levels_in_body):
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_signals.py:144:def scan(rth_only_warmup: bool):
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_signals.py:265:def report(tag, per_session, total, skipped, bucket, by_year, tripwire=0.486):
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_opportunity.py:36:OUT = Path(__file__).resolve().parents[2] / "vwap-bb" / "data"
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_opportunity.py:37:SHARDS = OUT / "_shards"
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_opportunity.py:38:WORKBENCH_END = "2025-01-31"          # HARD BOUNDARY — holdout begins 2025-02-01
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_opportunity.py:40:LOC_BAND = 0.20
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_opportunity.py:41:READINGS = ("A", "B", "C", "D")
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_opportunity.py:44:class HoldoutBreach(RuntimeError):
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_opportunity.py:48:def assert_workbench(d: str):
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_opportunity.py:57:def trig(o, h, l, c, lo, hi, nib, mode):
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_opportunity.py:79:def process_session(d, bars, sym, days_to_roll, spans_roll, prev_hl, atr_d):
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_opportunity.py:289:def main():
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_a7_selector.py:31:TICK = 0.25
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_a7_selector.py:32:MIN_STOP = 10.00            # §5.4 as amended — A5
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_a7_selector.py:33:RR_FLOOR = 1.5              # §6.5
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_a7_selector.py:34:FRONT_RUN_F = 2.0           # §6.4 "start 2-3"; low end, most permissive
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_a7_selector.py:35:MAX_TRADES_DAY = 3          # §10
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_a7_selector.py:36:LOC_BAND = 0.20             # PLACEHOLDER — "HTF range top" has no stated boundary
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_a7_selector.py:37:READINGS = ("A", "B", "C", "D")
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_a7_selector.py:38:TRIPWIRE = 0.4862
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_a7_selector.py:41:def ladder(levels, entry, direction, f):
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_a7_selector.py:53:def tie_break(cands):
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_a7_selector.py:81:def process(d, bars, prev_hl):
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/vwapbb_a7_selector.py:264:def main():
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/spec_current.py:45:NY_SIGMA_MIN_OBS = 30                                   # A8 as first written
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/spec_current.py:46:NY_SIGMA_OK_CM = NY_VWAP_ANCHOR + NY_SIGMA_MIN_OBS      # 600 = 10:00 ET
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/spec_current.py:47:CLUSTER_TOL_HALF = 5.0                                  # A13: half the 10-pt §3 tolerance
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/spec_current.py:49:SIGMA_RULE = "live"      # "live" = A13 per-instant CI test; "fixed30" = A8 as first written
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/spec_current.py:52:def ny_sigma_eligible(nmid, nsig, cm, n_bars):
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/spec_current.py:64:def htf_flag_a10(b15, n=FRACTAL_N):
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/spec_current.py:85:def signal_candidates_current(bars, prev_hl, audit=None):
/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/wt_bab2e03/research/star-trading/tools/spec_current.py:233:def admit_current(bars, cands):

=== OUTPUT COLUMN NAMES / ORDER ===
-- blind_trades.json, first record keys, in order --
['session_date', 'signal_minute', 'entry_tf', 'direction', 'entry', 'stop', 'target']
-- detector admission list (invariants_2b), first record keys, in order --
['cm', 'bar', 'tf', 'direction', 'kind', 'entry', 'stop_px', 'tgt_px', 'R_int', 'nlev', 'cl_lo', 'cl_mid', 'htf', 'counter', 'types', 'trig_high', 'trig_low', 'struct_anchor', 'rungs_skipped', 'n_rungs', 'signal_bar_idx', 'tf_bar_first_idx', 'lvl', 'n_at_minute', 'fill_px', 'fill_min', 'fill_bar', 'release_min', 'release_bar', 'session_date', 'symbols']

```

## 3. `AMBIGUITIES.md`, verbatim, in full (386 lines)

No entry below has been checked against its cited clause. No resolution has been classified as
grounded-in-text or contaminated-by-output. That classification is item 7's adjudication step,
reserved for the morning.

```markdown
# AMBIGUITIES — decisions taken while implementing SPEC.md blind

One entry per decision. Each quotes the governing spec text, states the readings available,
the reading taken, and why. Entries marked **[HIGH IMPACT]** are the ones most likely to
account for a divergence against the other implementation.

Four independent checks fell out of the build and are recorded first, because they pin
several of these decisions harder than argument could:

| check | spec says | this implementation |
|---|---|---|
| A13 NY σ̂ census, 7 rows (n = 6/10/20/30/35/50/90) | 9.23 / 11.12 / 16.00 / 19.48 / 20.91 / 24.69 / 30.10 | **identical to 0.01 on all seven**, over 537 sessions (A13 also says 537) |
| A10 fractal worked example, 2025-01-22 | 08:30 and 08:45 both print 21934.25; strict `>` falls back to 21905.00 at 06:15; A10 admits 08:30 and the flag becomes **uptrend** | 15m bars reproduce both prints and 21905.00 at 06:15; A10 rule admits 08:30; **flag at 09:50 = uptrend** |
| A5 "the 29.6% of triggers whose E1 entry falls on the wrong side of the wick extreme" | 29.6% | **29.54%** (18,154 of 61,457 triggers reaching that test) |
| A8 "completed bars behind the NY anchor at 09:50: 1m 20 · 2m 10 · 3m ~6 · 5m 4" | — | consistent only with **fixed grids anchored on 09:30**; the non-integer 3m count rules out rolling windows (see A-02) |

---

## A-01 — `signal_minute`: which minute is "the trigger bar's CLOSE"? **[HIGH IMPACT]**

> TASK.md: `"signal_minute": <int, ET minute-of-day of the trigger bar's CLOSE>`
> bars_api.py: *"Bars are OPEN-LABELLED at source: the bar stamped 09:47 covers 09:47:00-09:47:59."*

Three readings, for a TF-`k` bar whose slot is `[s, s+k-1]`:

1. **label** — `s` (the open minute)
2. **last constituent minute** — `s+k-1`, the minute during which the closing print occurs
3. **close timestamp** — `s+k`, the instant the bar completes

**Taken: reading 2.** The bars_api docstring says the 09:47 bar covers up to **09:47:59** — the
close therefore *occurs inside minute 09:47*, so the "ET minute-of-day of the close" of a 1m bar
is its own label, and reading 2 is the only one that generalises that to k>1. It is also the
direct expression `bars_api.minute_of_day(last_index_of_bar)`.

Reading 3 has a real argument on the other side: A8/A13's own convention labels an instant by the
clock time at which the preceding bars have completed ("at 09:50, 20 1m bars are complete", i.e.
bars 09:30–09:49). Under that house convention the 09:49 bar "closes at 09:50".

**Reading 3 is exactly reading 2 plus one, on every timeframe and every trade.** So if the two
implementations disagree by a uniform +1 on every `signal_minute` and agree on everything else,
this entry is the whole explanation and it should be adjudicated as one decision, not 1,583.

Reading 1 is ruled out for k>1 by the word CLOSE being emphasised at all.

## A-02 — entry-TF bar construction and grid anchor

> §1 *"Entry TFs: 1m, 2m, 3m, 5m."* — no aggregation rule stated.

Session index 930 (09:30 ET) is divisible by 1, 2, 3, 5 **and 15**, so a fixed grid anchored at
18:00 ET (index 0), at midnight ET, or at the 09:30 RTH open are all **the same grid**; that fork
does not exist. The live fork was fixed grid vs *rolling* k-minute windows recomputed every
minute. **Taken: fixed grid**, decided by A8's "completed bars behind the NY anchor at 09:50:
1m 20 · 2m 10 · **3m ~6** · 5m 4" — under rolling windows every timeframe would read 20, and the
`~` in front of 6 only makes sense for 20/3 on a fixed grid.

Bars are aggregated over the **whole Globex session from 18:00**, not just RTH, confirmed by A1's
open item (*"BB(20) and ATR(20) evaluated at 09:36 reach back into pre-open bars"*) and by A10's
worked example using 15m bars at 06:15 and 08:30.

Slots holding no 1-minute bar are skipped; a slot with a partial set is aggregated from what is
there (o = first present, h/l = extremes, c = last present). `signal_minute` always uses the
slot's **nominal** last index so signal minutes stay on a clean grid.

## A-03 — signal-window bounds

> §1/A1 *"Entry window: RTH 09:31–16:00 ET, entry blackout 09:31–09:35, first tradeable signal bar 09:36."*

**Taken: `576 <= signal_minute <= 959`** (09:36 … 15:59). The lower bound is A1 verbatim under
reading A-01.2. For the upper bound, RTH bars are those labelled 09:30…15:59 and the window
"ends at 16:00" is the close of the 15:59 bar; a trigger bar is required to lie inside RTH.
Under this bound all four timeframes share the same last signal minute (959) and the same first
grid, which is a mild independent argument for it. The alternative `<= 960` adds only bars that
begin after the cash close.

## A-04 — what "within proximity tolerance" makes a cluster **[HIGH IMPACT]**

> §3 *"Confluence cluster: ≥2 of {BB MA, NY VWAP middle/±1σ (post-9:30 only), daily VWAP middle/±1σ/±2σ/±3σ, daily POC} within proximity tolerance."*

Two standard readings: **single-linkage chaining** (consecutive sorted gap ≤ tol, yields a
partition, but a cluster can span far more than the tolerance) and **mutual proximity** (every
member within tol of every other, i.e. span ≤ tol, yields possibly-overlapping maximal windows).

**Taken: mutual proximity, maximal windows.** Under chaining, levels 30 points apart end up in
one "cluster" and are demonstrably *not* "within proximity tolerance" of each other, which
contradicts the sentence. Sensitivity to this fork is reported in NOTES.md.

Note this fork is largely invisible in the *output*: two clusters firing on the same bar and
timeframe in the same direction produce identical entry (BB MA), stop (wick extreme) and target
(ladder from entry), so §10.1(4)'s duplicate collapse merges them. That is also why tie-break
levels 3, 4 and 5 never fire here — matching A7's measurement exactly.

## A-05 — tolerance value

> §3 *"Tolerance: CALIBRATE (start ~10 NQ pts / 0.04%)."*

The two given forms disagree (0.04% of NQ ≈ 21,000 is 8.4 pts). **Taken: 10.00 points**, because
A13 pins it: *"1.95996 · σ̂ / √(2(n−1)) ≤ 5.00 points"* described as *"HALF the §3 cluster
tolerance"*. Recorded as a CALIBRATE start value used as given.

## A-06 — confluence minimum when the HTF flag is `range`

> §7 *"Confluence minimum: 3 counter-trend; 2 with-trend at reduced risk."*
> §4 *"Counter-trend raises confluence requirement (§8)."*

§7 names only two of the three flags §4 defines. **Taken: `range` requires 2.** §4 states the
relationship as counter-trend *raising* the requirement, which makes 2 the base and 3 the raised
case; `range` is not counter-trend. The alternative (only with-trend gets the relaxed 2) is
switchable as `OPT["range_conf"]`.

## A-07 — §7 invalidation: *which* ±1σ is "the opposing" one **[HIGH IMPACT]**

> §7 *"Invalidation-at-entry: trigger candle simultaneously touching the opposing ±1σ → stand down. [Hypothesis — test]"*

Two questions. **Which VWAP:** A8/A13 settle it — *"the σ bands ... may not serve as the §7
invalidation reference"* is said of the **NY** VWAP bands, so §7's reference is the NY ±1σ.
**Which sign:** taken as the band the trade is heading *into* (+1σ for a long, −1σ for a short),
on the strength of §6 rule 1 using "opposing" in exactly that sense — *"List **opposing**
structural levels **beyond entry**"*. Buying into overhead resistance is also the reading that
makes "stand down" mean something. Switchable as `OPT["invalidation"]`.

Kept as a live gate despite the `[Hypothesis — test]` tag, because A8 and A13 both describe it as
an operative rule whose *reference level* they are restricting; a rule that did not run would not
need its reference restricting. It rejects 24,837 triggers (28.8% of those reaching it), which is
large — the NY σ bands are eligible on ~71% of RTH minutes.

## A-08 — front-run F: *"start 2–3 NQ pts"* is a range, not a value **[HIGH IMPACT]**

> §6.4 *"working target = level ∓ F points (level minus F for longs). F: CALIBRATE (start 2–3 NQ pts)."*

**Taken: F = 2.5**, the midpoint, as the only neutral single value. F = 2.0 and F = 3.0 are equally
defensible; both are measured in NOTES.md. F shifts every reported `target` by the difference and
can change which ladder rung first clears the floor.

## A-09 — T_cancel is CALIBRATE with **no** start value

> §5.5 *"No fill → no chase. Order cancels if price runs T_cancel points beyond entry without filling. T_cancel: CALIBRATE."*

TASK.md instructs using the start value "where the spec ... gives a start value". §5.5 gives none.
**Taken: the cancel rule is DISABLED**, following A2's explicit precedent for an under-specified
rule (*"volatility stand-down = DISABLED for v1 [FIAT, §7 was marked OPEN with no definition]"*)
and A9's doctrine (*"A rule nobody can state is not a filter; it is a free parameter with a gate's
authority"*). Inventing a number would have been the larger sin.

**Consequence, recorded rather than hidden:** a working order therefore lives until the entry
window closes. Fill latency is 1 minute for 918 of 1,583 trades and ≤ 5 minutes for 1,251, but
**120 trades (7.6%) fill more than 30 minutes after their signal**, and those are exactly the
stale fills §5.5 exists to prevent. Any T_cancel would remove some of them.

## A-10 — fill accounting for the entry limit **[HIGH IMPACT]**

> TASK.md: *"`entry` is the price the trade actually fills at under the spec's accounting, not the intended limit."*
> §6.4 (the only fill-accounting sentence in the spec): *"Backtest counts target touched-minus-F as filled."*

**Taken: standard limit accounting — if a bar opens through the limit the fill is the (better)
open, otherwise the fill is the limit itself.** TASK.md's explicit "not the intended limit" is
otherwise inert, since a touch-fills-at-the-limit convention would make entry ≡ limit always.

This is not a rare correction: **302 of 1,583 fills (19.1%) beat the limit, median 7.52 pts.**
All 302 occur on the very next bar, and 284 of them are cases where the BB MA sits on the *far*
side of the trigger close, i.e. the E1 limit is already marketable when placed. That is a real
property of the spec, not of this implementation: §5.3 E1 says *"limit at the BB MA"* with no
requirement that the BB MA belong to the firing cluster, and A5 calls the pairing *"degenerate at
both ends"* — one end being the 29.6% wrong-side cases it declines to rescue, the other being
exactly these.

## A-11 — stop and target are computed from the **limit**, not from the fill

> §5.4/A5 *"Effective stop = max(structural stop, 10.00 pt). **The floor applies at order placement only**; once placed the stop is never widened."*

Decisive: at order placement the fill price is not yet known, so the floor — and therefore the
stop price, and therefore R, and therefore the §6.5 target ladder and the RR-floor admission test
— are all evaluated against the intended limit. **Taken: stop and target fixed at placement from
the limit; `entry` reports the fill.**

Consequence: on the 19.1% of trades that fill better than the limit, `|entry − stop|` is *not*
10.00 pt and can be as low as 0.75. That is arithmetically implied by A5's own wording and is
recorded, not smoothed over. The alternative (re-derive the bracket from the fill) would make the
pre-trade RR-floor gate and the post-fill geometry disagree instead.

## A-12 — Vault occupancy: what blocks, and what consumes the 3/session cap **[HIGH IMPACT]**

> §10.1 header: *"The Vault admits **at most one candidate at a time**, in signal-time order."*
> §10.1(2): *"**While a position is open**, later candidates are NOT admitted and are NOT queued."*
> §10.1(3): *"At most **3** candidates are admitted per session."*

The header and (2) differ on whether a *working, unfilled order* holds the slot, and (3) does not
say whether an admission that never fills burns a cap slot.

**Taken:** candidates are walked in ascending signal index with `busy_until` = the exit index of
the last *filled* trade. A candidate is discarded if `signal_index <= busy_until`; otherwise, if
fewer than 3 trades have filled, its order is simulated. A candidate whose order never fills
produces nothing, holds nothing and burns no cap slot.

Two properties this buys, both of which the spec demands:
* **no overlap is possible** — a fill is always strictly after its own signal, which is strictly
  after the previous exit, so §5.6's *"No overlapping trades ever"* holds by construction;
* an order that is still working when a later candidate fires *does* block that candidate
  (because `busy_until` is set from the eventual exit), which is the header's "one candidate at a
  time" — while a candidate that never fills cannot deadlock the rest of the session, which the
  header taken literally would allow.

The cap counting fills rather than admissions is chosen because A7 and A9 tabulate the capped
quantity as "**ADMITTED trades** / session" at 2.33–2.90 against a cap of 3.

## A-13 — target menu: which entries are computable **[HIGH IMPACT]**

> §6 *"Menu: VWAP middle; VWAP ±1σ/±2σ; POC; session extremes (Asia/London/pre-market); data extremes; prior-day H/L; weekly H/L; pullback origin (B2); HTF range extremes."*

**Included** (no invented constant needed): daily VWAP mid/±1σ/±2σ; NY VWAP mid/±1σ/±2σ; session
POC; prior-day high/low (= the preceding Globex session, which this data model makes exact);
prior-week high/low (preceding ISO week of session_end_date).

**Excluded, each for a stated reason:**
* *session extremes (Asia/London/pre-market)* — §2 names the boxes but the spec nowhere states
  their ET boundaries, and the common conventions differ by hours. A9's doctrine applies.
* *data extremes* — A13: *"The project holds no economic calendar."* Also kills §6 rule 3.
* *pullback origin (B2)* — A4: *"The A/B/B2 taxonomy of §4 is not implemented in the detector at all."*
* *HTF range extremes* — §1 assigns these to 1h/4h and states *"The 4h/1h range is RECORDED, NOT
  GATED ON"*; no lookback window for "the range" is ever defined.

Note the menu is listed under "VWAP ±1σ/±2σ" only — daily ±3σ is a §3 cluster level but **not** a
§6 target. Implemented as written.

Because A4 makes the target *the nearest rung clearing the floor*, menu membership moves targets
monotonically: a shorter menu can only push targets further out. This is the single most likely
source of `target` divergence after A-08.

## A-14 — does A13's ineligibility also bar NY σ bands from being *targets*?

> A13/§2.1 *"Below that the NY **mid** is usable and the **σ bands are not**: they may not enter a cluster (§3) and may not serve as the §7 invalidation reference."*

The general clause says "are not usable"; the colon then enumerates exactly two prohibitions,
neither of which is §6. **Taken: the restriction binds cluster membership and the §7 invalidation
only; NY σ bands remain in the §6 target menu.** The enumeration is not exhaustive of the bands'
uses (§3's over-extension test is also unlisted), so it reads as the operative specification
rather than as a gloss. The opposite reading is tenable and would push some targets outward.

## A-15 — A13's criterion carries no band multiple

> A13: *"eligible(σ̂, n) ⟺ 1.95996 · σ̂ / √(2(n−1)) ≤ 5.00"*

The stated quantity is the CI on *the ±1σ band's* distance from the mid; the ±2σ band's distance
is 2σ̂ and its CI half-width would be twice as wide. The formula as written has no k.
**Taken: one eligibility flag for all NY σ bands, exactly as written.** In practice only ±1σ is a
§3 cluster level and only ±1σ is the §7 reference, so this bites only through A-14.

`n` is the count of 1-minute bars from the 09:30 anchor **through the trigger bar inclusive**.
This is the same convention A13's own census table uses (its "n=30 / 10:00" row is bars
09:30–09:59), and reproducing that table to 0.01 on all seven rows confirms it.

## A-16 — ATR(20) smoothing

> §3 *"Optional size floor range ≥ k×ATR(20)"* — no smoothing convention given.

**Taken: simple mean of the last 20 true ranges.** The spec's house convention for a 20-period
average is SMA (§2 table: *"Bollinger Bands | 20, SMA, close, 2σ"*), and no Wilder/RMA seeding
rule is stated anywhere. Wilder's is switchable as `OPT["atr"]`; sensitivity in NOTES.md.

## A-17 — is the ATR size floor on?

> §3 *"**Optional** size floor range ≥ k×ATR(20): CALIBRATE (start k=1.0)."*

"Optional" pulls one way; a stated CALIBRATE start value pulls the other, and TASK.md says to use
start values where given. **Taken: ENABLED at k = 1.0**, decided by A1's open item, which lists
*"BB(20) **and ATR(20)** evaluated at 09:36"* among the quantities the detector actually computes
on the first tradeable bars. It applies to displacement only, which is where §3 puts it.

## A-18 — volume profile construction

> §2 *"Volume profile | Session + daily ... POC, VAH/VAL, HVN/LVN"*; A2 *"volume-profile bin = 1.00 pt"*; A8 *"The volume profile likewise uses 1-minute bars."*

Bin size, feed and anchor are given; the *distribution rule* is not. **Taken: each 1-minute bar's
volume spread uniformly across the 1.00-pt bins its [low, high] spans**, which is what a volume
profile built from OHLCV normally means; the alternative (all volume at the bar's typical price)
would make the profile a histogram of typical prices instead. POC is reported at the **bin
midpoint** (`floor(p) + 0.5`); ties go to the **lowest bin** for determinism. In this data model
the Globex session *is* the day, so "session profile" and "daily POC" (§3) are the same object,
accumulated from index 0 to the trigger bar.

## A-19 — the exact geometry of a rejection block

> §3 *"entry-TF candle that (a) trades into the cluster, (b) CLOSES back on the trade side of all cluster levels, (c) leaves a wick through/into them."*

**Taken**, for a long against a cluster spanning `[lmin, lmax]`, with `body_low = min(o,c)`:
`low <= lmax` (a) **and** `close > lmax` (b, "all cluster levels") **and** `low < body_low`
(a wick exists) **and** `body_low >= lmin` (c, the wick — not the body — is what penetrated).
Mirrored for shorts. The last condition is what "**a wick** through/into them" adds beyond (a):
if the body's own low is below the whole cluster, the wick lies entirely below the cluster and
penetrates nothing. This is corroborated indirectly: the wrong-side rate it produces is 29.54%
against A5's 29.6%.

## A-20 — displacement: "body closes through ≥2 cluster levels"

**Taken:** the candle must be in the trade's direction (`close > open` for a long) and a level
counts as crossed when `open < level < close` (strict both sides; mirrored for shorts). Strictness
matters only for a level exactly at the open or the close, which is essentially unreachable for a
VWAP level and rare for a 1.00-pt-binned POC. Body/range uses `|close − open| / (high − low)` and
requires `high > low`. "Extreme quartile" is `close >= low + 0.75·range` for longs.

## A-21 — "wrong side of the wick extreme"

> A5 *"A trigger whose E1 entry falls on the wrong side of the wick extreme remains invalid — the floor does not rescue it."*

**Taken:** invalid unless `entry > low` for a long / `entry < high` for a short — compared against
the **wick extreme itself**, not the buffered structural stop. Equality is treated as invalid
(an entry exactly on the extreme carries no structural stop distance at all); it is unreachable in
practice. Rate produced: 29.54% vs A5's stated 29.6%.

## A-22 — HTF fractal series scope

> A2 *"HTF classification = 15m fractal swings N=2, HH+HL ⇒ uptrend / LH+LL ⇒ downtrend / else range."*

**Taken: the 15m series is session-local**, built from index 0 (18:00 ET) of the session being
processed, with no carry-over from the previous session. A10's worked example is entirely inside
one session (06:15 and 08:30 on 2025-01-22) and reproduces exactly under this scope. A swing is
usable only once bar `i+N` has completed, i.e. from 1-minute index `last(i+N)`. Trend uses the
last two confirmed highs and the last two confirmed lows; fewer than two of either ⇒ `range`.

This is *not* the same object as A9's `range_pos_swing`, whose quoted 1,733-point width on
2025-01-22 cannot come from a single session. A9 makes that a recorded covariate and gates on
nothing, and TASK.md's output schema has no column for it, so it is not computed here.

## A-23 — §6 rules the amendments leave unimplemented

Rule 2's pattern-conditioned defaults are **not** implemented — A4 states plainly that they
*"remain unimplemented and ambiguous ... **Open, needs Angus**"* and that the A/B/B2 taxonomy is
*"not implemented in the detector at all"*. Rule 3 (news-day override) is unimplementable without
a calendar (A13). Rule 6 (alignment bonus) is a *"prefer"* with no rule attached and is
contradicted by A4's "take the **first** level that clears the floor"; not implemented.
Target selection is therefore rule 1 + rule 4 + rule 5-as-amended, only.

## A-24 — out of scope by TASK.md, implemented as no-ops

§8 management variants (V0/V1/V2/V4) — TASK.md forbids computing outcomes. §9 sizing/conviction —
no output column. §10.2 daily halt after 2 losses / −2R — **requires outcomes**, so it cannot be
applied without violating TASK.md; not applied. A9's `range_pos_swing` / `range_pos_blocks` and
A11's `entry_tf_1m` boolean are output-only fields the JSON schema does not carry (`entry_tf`
already records 1m). §7 volatility stand-down: DISABLED per A2.

## A-25 — tie-break order, and duplicate collapse

> §10.1(4) *"Applied in order; the first level that separates them decides."*

**Taken literally:** level 1 (highest entry TF) runs first, and level 2 (long+short ⇒ stand down)
only arbitrates among candidates that *share* the top timeframe. A7's measured split (level 1
resolves 15.7–19.1% of admissions, level 2 fires on 0.2%) only makes sense in that order.
Duplicates are collapsed *before* tie-breaking, on `(entry_tf, direction, entry, stop, target)`
per §10.1(4). Levels 3, 4 and 5 are implemented and, exactly as A7 reports, **never fire** (0 of
6,917 ties here; 6,702 resolved at level 1, 215 stood down at level 2).

## A-26 — exit simulation (used **only** to release the one-position lock)

No outcome is recorded anywhere. For lock purposes a position ends on the first 1-minute bar
whose range reaches the stop or the target, **stop checked first** when a single bar spans both,
scanning from the fill bar inclusive; otherwise it is forced out at the §1 EOD flatten
(15:55 ET). Both conventions affect only *when the next candidate becomes eligible*.

## A-27 — the P3 hint cannot be reconciled with any bar grid

> A13 *"`2025-01-29 10:20` remains an admitted trade on 2m/3m/5m."*

Recorded because it looks like a checkable fact and is not. Under a fixed grid, 2m, 3m and 5m
bars share a boundary only every 30 minutes from 09:30 — at 09:59/10:29/10:59 under reading
A-01.2, and at 10:00/10:30/11:00 under readings A-01.1 and A-01.3. **10:20 is not one under any of
the three.** So "10:20" must be the wall-clock *parity instant* (as "2025-01-22 09:50" is for P2),
not a signal minute. It does not discriminate A-01, and no attempt was made to bend the grid to
fit it. For the record, this implementation's nearest qualified candidates on 2025-01-29 are
10:19 (2m long), 10:21 (2m long) and 10:22 (1m long), with a 3m at 10:11.

## A-28 — minor readings taken without much doubt, listed for completeness

* Only the **BB basis** is a §3 cluster level; §2's ±2σ bands are computed but are not levels,
  since §3's set names *"BB MA"*.
* **Confluence count** counts distinct *types* (§3: *"VWAP family ×1, BB ×1, POC ×1, structural
  ×1"*), so all VWAP levels in a cluster count once; "structural" has no computable definition in
  the spec, so the attainable maximum is 3.
* **VWAP σ** is the volume-weighted population SD of HLC/3 about the VWAP
  (`Σv·tp²/Σv − vwap²`) — confirmed exactly by the A13 census reproduction.
* **Stop buffer** 1 tick = 0.25 (A2; tick size implied by A5's *"10.00 points (40 ticks)"*).
* **RR floor = 1.5** — marked CALIBRATE but stated as 1.5R throughout §6.5 and confirmed by A5's
  *"the minimum target distance becomes 15.00 pts (10.00 × 1.5)"*.
* **CALIBRATE start values used as given:** cluster tolerance 10.00, B_min 0.6, ATR k 1.0,
  RR floor 1.5, F 2.5 (see A-08), session cap 3.
* Sessions are processed **only** for `session_end_date <= 2025-01-31` (539 of the 796 the store
  holds), asserted in `process_session`. Sessions after that date are never read; earlier
  sessions are read only for prior-day / prior-week highs and lows.

```

## 4. `READ_MANIFEST.md`, verbatim, in full (61 lines)

No judgement is offered here on whether the manifest is complete, whether it discharges the
isolation requirement, or whether the agent's own account should be trusted. That is the morning
adjudication.

```markdown
# READ MANIFEST

Append one line per file read.

Complete and honest record of every file this session read, searched, listed or opened,
in order. Nothing outside the working directory
`/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/blind_build/`
was read, with the single permitted exception noted at the bottom.

## Read (working directory)

- `SPEC.md`  — read in full, in two passes (lines 1–400, then 400–728)
- `TASK.md`  — read in full
- `bars_api.py` — read in full
- `READ_MANIFEST.md` — read (this file, before appending)

## Directory listings (working directory only)

- `ls -la` of the working directory itself, once, at the start. No other directory was
  listed anywhere on the machine.

## Written / created by me (working directory)

- `blind_impl.py`
- `blind_trades.json`
- `sensitivity.py`
- `AMBIGUITIES.md`
- `NOTES.md`
- `READ_MANIFEST.md` (this file)

## Scratch files I created and read back (outside the project, inside my own scratch area)

- `/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/prev.json`
  — a copy of my own `blind_trades.json`, made by me, read back only to verify that a rerun
  is byte-identical. Contains nothing but my own output.
- `/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/tasks/bmoex1ox5.output`
  — the captured stdout of my own backgrounded `sensitivity.py` run. My own output.

## The one permitted read outside the working directory

- `/home/user/AI-trading-agents/research/star-trading/tools/_nq_frontmonth.pkl`
  — loaded **indirectly and only** by `bars_api._build()` when `bars_api.sessions()` is called.
  I never opened, inspected, listed or unpickled it myself. This is the exception TASK.md
  explicitly grants.

## Explicit negative statement

I did **not** read, grep, glob, list or open any `.py` file, or any other file, under
`/home/user/AI-trading-agents/` — including anything under
`/home/user/AI-trading-agents/research/star-trading/tools/`. I did not list that directory or
any parent of it. No file named in SPEC.md as a cross-reference
(`research/STATE.md`, `research/vwap-bb/preflight.md`, `research/vwap-bb/PARITY-P2-RESULT.md`,
`research/vwap-bb/target-stop-reconciliation.md`, `data/reference/hand_log_scope.md`,
`vwapbb_a7_selector.py`, `loc_gate_measure.py`, `spec_current.py`,
`workbench_results_SEALED.parquet`) was opened or searched for; every reference to their
contents in my notes is quoted from SPEC.md itself.

No session with `session_end_date > 2025-01-31` was processed; the filter is applied before any
session is touched and is re-asserted inside `process_session()`.

**No accidental reads occurred. This manifest is complete and honest.**

```

## 5. `NOTES.md`, verbatim, in full (120 lines) — reproduced for completeness, not analysed

The blind build's own notes reference several spec-published figures (A5's 29.6%, A13's σ̂ census,
A9's 46.9) as points of comparison. **Whether those references make any specific ambiguity
resolution contaminated is an adjudication call and is not made here.**

```markdown
# NOTES — blind re-implementation of SPEC.md

## Headline

| | |
|---|---|
| **Sessions processed** | **539** — every `session_end_date <= 2025-01-31` the store holds (2023-01-03 … 2025-01-31). The store holds 796; the 257 after the seal date were never read. |
| **Trades produced** | **1,583** (2.9369 / session) |
| Sessions with ≥1 trade | 537 |
| Direction mix | 839 long / 744 short (53.0 / 47.0) |
| By entry TF | 1m 803 · 2m 337 · 3m 268 · 5m 175 |
| Trades/session distribution | 3 → 515 sessions · 2 → 16 · 1 → 6 · 0 → 2 |
| Output | `blind_trades.json`, sorted by (session_date, signal_minute, entry_tf); byte-identical across reruns; sha256 `8116166a969781893bc9dd…` |

Run: `python3 blind_impl.py`. Pure standard library, ~90 s.

## Independent checks that fell out of the build

These were not targets — they are quantities the spec happens to publish, which the
implementation reproduces without being fitted to them.

| check | spec | mine |
|---|---|---|
| A13 NY σ̂ census, all 7 rows (n = 6/10/20/30/35/50/90) | 9.23 · 11.12 · 16.00 · 19.48 · 20.91 · 24.69 · 30.10 | **identical to 0.01 on every row**, over the same 537 sessions A13 cites |
| A5 "the **29.6%** of triggers whose E1 entry falls on the wrong side of the wick extreme" | 29.6% | **29.54%** |
| A10 fractal example, 2025-01-22 | 08:30 & 08:45 both 21934.25; strict `>` falls back to 21905.00 at 06:15; A10 rule ⇒ **uptrend** | all three reproduced; flag at 09:50 = **uptrend** |
| A7 "levels 3, 4 and 5 **never fire at all**" | 0.0% | 0 of 6,917 ties (6,702 at level 1, 215 stood down at level 2) |
| A7 "blocked — position open" | 15.6–25.9% | 25.5% |
| A9 admitted trades with the location gate OFF | 2.9002 / session | 2.9369 / session |

Where I land outside the spec's published ranges: qualified candidates/session **78.6** (A7's four
readings span 8.87–47.43), 3/day cap binds on **95.5%** of sessions (A7: 63–91%), ties on **23.5%**
of signal minutes (A7: 16.4–22.9%), median hold **3 min** (A7: 5–7). I am more permissive than any
of their four readings. Note those tables predate A13: A12 records that the σ-band eligibility
rule is *"new and unrun"*, and A13 replaced the fixed 10:00 boundary with a live per-instant test
that is satisfied on ~71% of RTH minutes — so the published candidate counts are not measurements
of the specification I implemented.

## The single most important thing for the adjudicator

**Trade count is almost invariant to the ambiguities; trade identity is not.** Sweeping each
genuine fork one at a time (`sensitivity.py`, trade counts only — no outcome computed):

| variant | trades | qual/session | trades also in the baseline set |
|---|---|---|---|
| **baseline (chosen readings)** | **1583** | 78.6 | — |
| cluster = single-linkage chaining | 1561 | 59.0 | **1071 / 1583** |
| §7 invalidation band = other side | 1580 | 89.4 | **879 / 1583** |
| `range` flag needs 3 confluences | 1534 | 46.4 | **990 / 1583** |
| ATR(20) = Wilder instead of SMA | 1584 | 78.9 | 1538 / 1583 |
| target menu without prior-day/week H/L | 1577 | 74.0 | 1389 / 1583 |
| F = 2.0 | 1584 | 78.6 | 1555 / 1583 |
| F = 3.0 | 1584 | 78.5 | 1560 / 1583 |

Every variant lands within ±3% on count — which is §10.1(5) being true (*"the cap, not the
strategy, sets which trades are taken"*) — while as few as **55%** of the individual trades
survive. So: **two implementations agreeing on ~1,500 trades tells you almost nothing, and a
per-trade diff tells you everything.** Adjudicate on the trade sets, not the totals.

## Things to look at first if the two runs disagree

1. **`signal_minute` off by exactly +1 on every trade** → AMBIGUITIES A-01. The three readings of
   "the trigger bar's CLOSE" differ by a uniform constant; this is one decision, not 1,583.
2. **`target` differs but entry/stop match** → A-08 (F = 2.5 vs 2 vs 3) or A-13 (target-menu
   membership: I excluded Asia/London/pre-market boxes, data extremes, pullback origin and
   HTF range extremes, each for a stated reason).
3. **`entry` differs from the BB MA by several points on ~19% of trades** → A-10. TASK.md's
   "not the intended limit" is read as standard limit accounting: a bar that opens through the
   limit fills at the better open. 302 of 1,583 fills do this, median 7.52 pts, all on the very
   next bar, 284 of them because the BB MA already sits on the far side of the trigger close.
   That is A5's *"degenerate at both ends"* showing up in the output.
4. **`|entry − stop|` is not ≥ 10.00 on those same trades** → A-11, and deliberate: A5 says the
   floor *"applies at order placement only"*, so stop and target are fixed from the limit while
   `entry` reports the fill.
5. **Whole trades present in one set and absent from the other** → most likely A-07 (which ±1σ is
   "the opposing" one) or A-04 (cluster linkage), the two forks with the largest identity effect.

## One place I deliberately did not chase a matching number

Setting the `range` HTF flag's confluence minimum to 3 moves qualified candidates from 78.6 to
**46.4/session**, which sits almost exactly on A9's 46.9 and A7 reading A's 47.43. I kept **2**
anyway, because §4 states the rule as *"Counter-trend **raises** confluence requirement"* — which
makes 2 the base and 3 the exception — and because selecting a reading by how close it lands to a
published count is fitting, not reading. Recorded here so the adjudicator can overrule it on the
evidence rather than discover it. It is switchable: `OPT["range_conf"] = 3`.

## Deliberate non-implementations (all justified in AMBIGUITIES.md)

* **T_cancel** (§5.5) — CALIBRATE with *no* start value, so the cancel rule is disabled rather
  than invented, following A2's precedent. Cost: 120 trades (7.6%) fill more than 30 minutes
  after their signal. Any T_cancel removes some of them.
* **Location gate** — A9 demotes it to a recorded covariate; not applied, and TASK.md's schema
  carries no column for it.
* **Volatility stand-down** — A2: DISABLED for v1.
* **§6 rule 2 pattern defaults, rule 3 news override, rule 6 alignment bonus** — A4 records rule 2
  as open, A13 records that no economic calendar exists, and rule 6 is a "prefer" with no rule.
* **§10.2 daily halt (2 losses / −2R)** — cannot be evaluated without computing outcomes, which
  TASK.md forbids. Not applied.
* **§8 management, §9 sizing, A11's `entry_tf_1m` boolean** — no output column; `entry_tf` already
  records which trades are 1m (803 of 1,583, i.e. 50.7%, so A11's hole is live here).

## No outcome was computed

No P&L, no win/loss, no R multiple, no exit reason appears anywhere in the code or the output.
`simulate_exit()` exists solely to decide when the §5.6 / §10.1(2) one-position lock releases, and
its return value is an index — nothing else is derived from it.

## Sealed-data handling

`process_session()` opens with `assert date <= "2025-01-31"`. The date list is filtered before any
session is touched. Sessions before the seal date are additionally read to supply prior-day and
prior-week highs and lows for the §6 target menu; nothing after 2025-01-31 is read at any point.

## Files

* `blind_impl.py` — the implementation (the `OPT` dict at the top holds the switchable forks)
* `blind_trades.json` — 1,583 trades
* `sensitivity.py` — the fork sweep above
* `AMBIGUITIES.md` — 28 entries
* `READ_MANIFEST.md`

```

## 6. What was deliberately NOT done, per the split instruction

- No disagreement in §1 has been classified as detector bug / second-build bug / spec ambiguity.
- No entry in `AMBIGUITIES.md` has been checked against its cited clause, and none has been ruled
  contaminated or clean.
- No verdict has been rendered on whether isolation held.
- No trade has been removed from the diff on the grounds that the ambiguity producing it was
  output-contaminated.
- `blind_impl.py` and `sensitivity.py` were read only far enough to run the grep and confirm the
  function/constant inventory in §2; they were not read for correctness.

**Everything above is collection. The calls happen in the morning, against item 7's own
adjudication instructions.**
