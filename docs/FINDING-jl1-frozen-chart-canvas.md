# The chart canvas froze while every data API kept returning correct values

Found 2026-08-20, jl1 day 1, and it is the most safety-relevant defect of the run.

## What happened

`capdrive` captured three manage frames for 07-05 A10 (11:02, 11:06, 11:09). Each one:

- landed on its **exact target cursor**, re-read from `replay status`, never trusted from `step`;
- returned a legend read **twice, in agreement**, coherent (`Lower <= Basis <= Upper`);
- was stored with values that match the briefing exactly.

Every numeric guard passed. And the **picture was of a different cursor** — BB basis 29,884.09
and a last close of 29,896.75, against a stored-and-verified 30,018.91 at a price of 30,030.5.

The chart canvas had stopped painting. `data_get_study_values` reads TradingView's data window,
not the canvas, so it kept returning live, correct numbers for the real cursor while the rendered
chart sat frozen on an earlier view. Proof: setting a tight visible range changed nothing in the
image, while `values` simultaneously reported the live 30,026.65.

## Scope, established rather than assumed

- 74 jl1 screenshots hashed: 72 distinct. The only two identical pairs are legitimately the SAME
  cursor (A8 candidate / A7 manage both at 10:44; L1 / L9 manage both at 04:59) — no mass freeze.
- A4's candidate frame (09:44) matches its stored legend **exactly**.
- A10's candidate frame (11:00) matches its stored legend **exactly**.
- A7's manage frame (10:44) is **byte-identical to A8's known-good candidate frame at the same
  cursor** — an independent cross-check that the manage path was sound up to 13:12 wall-clock.

The freeze therefore began between 13:12 and 13:20 and caught **three frames only**: A10's manage
captures. The one verdict made against a frozen frame (A10 11:02) explicitly refused the image and
decided on the verified legend, so it stands.

## Why a numeric check could never have caught this

Cursor verification, double legend reads and BB coherence all test the DATA PATH. The screenshot
is a separate path with no assertion on it at all. A frame can be simultaneously
cursor-correct and picture-wrong, and nothing downstream of `capdrive` compares the two.

It was caught only because the manage agent held its image up against its own briefing and said
they disagreed. That is the **fifth** defect across jr2 and jl1 found by an agent objecting to its
INPUT rather than by anyone auditing an output.

## Recovery attempted, and the state it left

A chart page reload (`location.reload()`) previously cleared a wedged replay widget. This time it
made things worse: the canvas came back **blank**, the watchlist disappeared, and the restored
layout carries an indicator that was not there before (`MenthorQ Paste-In Levels`), while the
header reports resolution 15 against a toolbar showing 3m. `tab list` confirms a single tab on the
correct chart (`QhaPRAxc`); the data APIs still answer (`bar_count: 100`, replay started, cursor
live). The pane simply will not paint.

**This needs a manual TradingView restart.** It is outside what the run can do.

## What this costs and what it does not

jl1 day 1 (2026-07-05) is COMPLETE and its book is sound: all 19 candidates adjudicated, both
window-open votes recorded, six fills managed and exited. Every frame day 1 relied on was captured
and verified before the freeze.

Days 2-5 cannot proceed: they need ~29 candidate frames and their manage frames, and any capture
taken now would be blank.

## The rule this earns

**Assert on the artefact you actually hand the agent, not only on the data you used to build it.**
A capture pipeline that verifies cursor and legend but never inspects the image it saves is
checking the half that was already reliable. The cheap fix is to render the stored legend into the
comparison — after the screenshot, read the image's own legend region back, or at minimum hash
consecutive frames and refuse a capture whose image is identical to a frame at a different cursor.
