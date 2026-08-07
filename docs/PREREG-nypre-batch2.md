# PRE-REGISTRATION BATCH — five NY pre-market families (declared before census)

Filed per VALIDATION-PROCESS §1; this commit's timestamp is the declaration for
all five. Eras for every family: 2025 and 2026 (Jan–Jul) separately; inverse
pass at refinement; 2023/24 untouched. L0 = base-rate census, no costs.
Event-day flags are tape-defined at L0 (descriptive); live rules require the
release calendar (known in advance). All windows/buckets per family = ONE
ledgered trial family each.

## NYP-GAP-01 (gap engine)

Claims: gap fill rate is conditioned by (a) location — open inside prior RTH
range fills at materially higher rate than outside; (b) clock — most fills
complete early; a gap unfilled at 10:00 fills the rest of day at a materially
lower rate; (c) cause — gaps on tape-event 8:30 days that held fill less.
Census: per day, gap = 09:30 open − prior RTH close; inside/outside prior
range; filled (touch prior close) by 10:00 / by 16:00; survival-conditional
fill rate; splits by size tercile and event flag.
Kills: no location conditioning (inside≈outside within noise) both eras; era
flip; survival flip absent (post-10:00 fill rate not materially lower).

## NYP-INV-01 (inventory flush)

Claims: when ≥90% of 04:00–09:29 1-min closes sit one side of prior settlement,
the first 30 min of RTH moves counter to the overnight side at an elevated
rate/magnitude vs unconditional; effect stronger when the open sits at/near the
overnight extreme.
Census: inventory skew buckets {≥90% long, ≥90% short, mixed}; 09:30→10:00
return signed AGAINST the overnight side; magnitude and hit rate vs
unconditional base.
Kills: no counter-move edge either era; era flip; edge only on ≤3 days.

## NYP-EUR-01 (euro handoff / ALN)

Claims: classified at 08:00 ET — London broke Asia high & held Asia low
("engulf-up") → NY (08:00–16:00) breaks the pattern high before the pattern low
at ≥65%; mirror for engulf-down. (Published: 80.8%/75.0%; census re-bases.)
Boxes: Asia 20:00–02:00, London 02:00–08:00 ET.
Census: pattern frequency; P(pattern-side break first); degradation when the
wrong side breaks first.
Kills: <60% either direction either era; era flip. Redundancy gate vs canon pre
fills REQUIRED before any L1 (highest-risk candidate).

## NYP-QH-01 (quiet-hours fade)

Claims: in hours 06:00/07:00/08:00 ET, a 1-min close beyond the prior hour's
range followed by re-entry reverts to the current hour's midpoint before hour
end at ≥65% (published 76–83.5%); rate does NOT collapse in the post-2025
(popularization) sub-era.
Census: per hour-slot: event count, reversion-to-mid rate, by era AND by
pre/post-2025-07 split.
Kills: <60% both eras; post-popularization collapse (>15pp drop vs 2025H1);
event count too thin (<30/era/slot).

## NYP-PRE-01 (pre-release premium)

Claims: on tape-event 8:30 days (top-decile 08:30 candle — descriptive at L0),
the 04:00→08:25 return is positive on average, concentrated in high-vol
regimes (trailing 5-day realized vol top tercile); near zero on non-event days.
Census: mean/median 04:00→08:25 points by {event day × vol tercile} by era.
Kills: no positive conditional drift both eras; effect not vol-concentrated;
magnitude below plausible cost floor at L1 sizing.
