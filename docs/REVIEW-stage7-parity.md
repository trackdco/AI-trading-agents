# Stage-7 review — the parity gate itself (Pat directive, 19 Jul)

Different animal from the earlier stage reviews: Stage 7 is a VERIFICATION TOOL, and a
verification tool's failure mode isn't crashing — it's PASSING when it shouldn't. So
this review attacked the gate's blindness, not its uptime. Three real gaps, all fixed,
plus a live demonstration that the new selftest catches comparator blind spots.

## Findings and resolutions

**F1 — the trade key compared only half the trade.**
The match key was (date, fill_ts, direction, points, dollars). Book, entry price, exit
price, exit reason, and size were NOT compared — a stream that drifted in any of those
while landing the same P&L would have passed the gate silently (e.g. the wrong book
producing a coincidentally identical trade, or a different exit path to the same
dollars). → Strict key now includes book, entry, exit_price, exit_reason, and size on
all three surfaces (batch record, streamed event, journal row), with dollars tightened
from whole-dollar to 2dp rounding.

**F2 — vacuous passes.**
An empty window (typo'd dates, weekend range) produced batch 0 == stream 0 → "MATCH".
A gate that can pass on nothing proves nothing. → No reference days in the window →
loud FAIL before any simulation; zero trades on both sides → loud FAIL with an
instruction to pick a real window. Verified: a weekend range now fails immediately.

**F3 — the alarm had never been heard to ring.**
40 days of MATCH is only evidence if the comparator CAN mismatch. → `--selftest` mode:
four single-field mutations of the real batch result (dropped trade, dollars ±$1,
wrong book, wrong exit reason) must each be caught by the exact comparison the gate
uses. First run immediately demonstrated the value: the exit-reason mutation was
reported MISSED — the gate failed loudly, and the cause was a bug in the selftest's
own mutation (it overwrote exit_reason with "stop" on a trade already exiting "stop",
a no-op). Fixed to always produce a differing value. Note the failure direction: the
gate failed toward FALSE ALARM, never toward false pass.

**F4 — journal session picks were counted, not checked.**
The journal gate printed how many daily book picks were logged but never compared them
to the reference switch — a wrap_policy or policy bug could log wrong books all week
and pass. → Every scored day's journaled pick is now asserted equal to
`book_for_day(day, vector)`; any divergence is listed and fails the gate.

## Re-verification after hardening
All three standing windows re-passed under the STRICT key with selftest on:
- Feb 9–13: 7 trades, picks match, 4/4 mutations caught
- Mar 16–20: 8 trades, picks match, 4/4 mutations caught
- April 1–30 (full month): 30 trades, 35 picks match
- Weekend window: fails loud (no vacuous pass)

Stage 7 stands: 40 historical days, 45 trades, zero difference on every execution
field. The gate is now proven able to fail — which is what makes its passes evidence.
