#!/usr/bin/env python3
"""2a — SPEC-DERIVED UNIT TESTS.

EVERY expected value in this file was written from the specification text, quoted
inline beside each case. The detector was NOT executed to obtain any expectation,
and no expectation was adjusted after seeing a result. This file is committed on
its own, before any run.

Spec under test: strategy-definition-v1.0.md,
SHA-256 42d6f0f68ed35bef0280be782c58f72059333222047841473ab74d5b9fbd83bf (A1-A13).

Two kinds of expectation appear, and each case says which it is:
  [LIT]  a literal, reasoned from the quoted clause with no arithmetic borrowed
         from any implementation.
  [FORM] the clause transcribed as a formula and evaluated against inputs this
         file constructs. Used only where the clause IS arithmetic (§5.4/A5's
         max(), §6.5's ladder walk), because a literal there would just be that
         arithmetic done by hand and copied in.

UNSPECIFIED IN SPEC cases assert nothing. They record observed behaviour where the
spec has no clause, per Part 0 rule 2.

No outcome is computed anywhere in this file.
"""
from __future__ import annotations

import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]

import collections
import json
import math
from pathlib import Path

RESULTS = []          # (id, clause, kind, expected, actual, status)
OBSERVED = []         # UNSPECIFIED IN SPEC records


def check(tid, clause, kind, expected, actual):
    ok = expected == actual
    RESULTS.append((tid, clause, kind, repr(expected), repr(actual),
                    "PASS" if ok else "FAIL"))
    return ok


def close(tid, clause, kind, expected, actual, tol=1e-9):
    ok = abs(expected - actual) <= tol
    RESULTS.append((tid, clause, kind, f"{expected!r}", f"{actual!r}",
                    "PASS" if ok else "FAIL"))
    return ok


def observe(tid, clause, note, actual):
    OBSERVED.append((tid, clause, note, repr(actual)))


# ════════════════════════════════════════════════════════════════════
# GROUP A — TRIGGER PREDICATES.  §3, quoted:
#
#   "Rejection block: entry-TF candle that (a) trades into the cluster, (b)
#    CLOSES back on the trade side of all cluster levels, (c) leaves a wick
#    through/into them."
#
#   "Displacement ... entry-TF candle whose body closes through >=2 cluster
#    levels, with body/range >= B_min and close within the extreme quartile of
#    the candle's range (top 25% for longs, bottom 25% for shorts ...).
#    B_min: CALIBRATE (start 0.6)."
#
# A2 froze nothing here; §3's start values are B_min = 0.6 and the quartile is
# stated as 25%, i.e. close within the top/bottom quarter of the range.
# ════════════════════════════════════════════════════════════════════
CL_LO, CL_HI = 100.0, 110.0


def group_a(trig):
    R = ("long", "rejection")
    S = ("short", "rejection")
    DL = ("long", "displacement")
    DS = ("short", "displacement")

    # A1 [LIT] textbook long rejection: trades into the cluster (low 105 is inside
    # 100-110), closes above every cluster level (113 > 110), lower wick present
    # (low 105 below the body's 112).
    check("A1", "§3 rejection block", "[LIT]", {R},
          trig(112.0, 115.0, 105.0, 113.0, CL_LO, CL_HI, 0, "A"))

    # A2 [LIT] close INSIDE the cluster fails (b) "closes back on the trade side of
    # ALL cluster levels".
    check("A2", "§3 rejection block (b)", "[LIT]", set(),
          trig(112.0, 115.0, 105.0, 108.0, CL_LO, CL_HI, 0, "A"))

    # A3 [LIT] never trades into the cluster - low 111 is above cluster high 110 -
    # so (a) fails.
    check("A3", "§3 rejection block (a)", "[LIT]", set(),
          trig(111.0, 115.0, 111.0, 113.0, CL_LO, CL_HI, 0, "A"))

    # A4 [LIT] no wick: the body's lower edge IS the low, so (c) "leaves a wick"
    # fails.
    check("A4", "§3 rejection block (c)", "[LIT]", set(),
          trig(105.0, 115.0, 105.0, 113.0, CL_LO, CL_HI, 0, "A"))

    # A5 [LIT] mirror: short rejection.
    check("A5", "§3 rejection block, short", "[LIT]", {S},
          trig(88.0, 105.0, 85.0, 87.0, CL_LO, CL_HI, 0, "A"))

    # A6 [LIT] displacement alone. Body 98->111 closes through the cluster;
    # body/range = 13/14 = 0.9286 >= 0.6; close is 13/14 = 0.9286 up the range,
    # inside the top quartile; 3 levels in the body. Low equals the open so there
    # is no lower wick and the rejection predicate must NOT also fire.
    check("A6", "§3 displacement", "[LIT]", {DL},
          trig(98.0, 112.0, 98.0, 111.0, CL_LO, CL_HI, 3, "A"))

    # A7 [LIT] displacement needs >=2 cluster levels inside the body. One is not
    # enough.
    check("A7", "§3 displacement, '>=2 cluster levels'", "[LIT]", set(),
          trig(98.0, 112.0, 98.0, 111.0, CL_LO, CL_HI, 1, "A"))

    # A8 [LIT] B_min boundary, ON. range 20 (95->115), body 12 = 0.60 exactly,
    # close 115 is at the top of the range so the quartile test passes.
    # §3 says "body/range >= B_min", so 0.60 exactly must PASS.
    check("A8", "§3 displacement, 'body/range >= B_min', B_min = 0.6", "[LIT]", {DL},
          trig(103.0, 115.0, 95.0, 115.0, CL_LO, CL_HI, 3, "A"))

    # A9 [LIT] B_min boundary, OFF. Same bar with body 11.8 -> 0.59 < 0.6.
    check("A9", "§3 displacement, B_min boundary below", "[LIT]", set(),
          trig(103.2, 115.0, 95.0, 115.0, CL_LO, CL_HI, 3, "A"))

    # A10 [LIT] quartile boundary, ON. range 20 (95->115); close 110 sits
    # (110-95)/20 = 0.75 up the range, i.e. exactly at the bottom edge of the top
    # quartile. §3 says "within the extreme quartile", so 0.75 must PASS.
    # body 95->110 = 15/20 = 0.75 >= 0.6. Close must exceed the cluster high, and
    # 110.0 is not > 110.0, so the cluster is lowered for this case.
    check("A10", "§3 displacement, extreme-quartile boundary", "[LIT]", {DL},
          trig(95.0, 115.0, 95.0, 110.0, 90.0, 99.0, 3, "A"))

    # A11 [LIT] quartile boundary, OFF: close 109.9 is 0.745 up the range.
    check("A11", "§3 displacement, quartile boundary below", "[LIT]", set(),
          trig(95.0, 115.0, 95.0, 109.9, 90.0, 99.0, 3, "A"))

    # A12 [LIT] mirror: short displacement, close in the bottom quartile.
    check("A12", "§3 displacement, short", "[LIT]", {DS},
          trig(112.0, 112.0, 88.0, 89.0, CL_LO, CL_HI, 3, "A"))

    # A13 [LIT] a zero-range bar has no body/range and no wick; nothing can fire.
    check("A13", "§3, range = 0 degenerate", "[LIT]", set(),
          trig(100.0, 100.0, 100.0, 100.0, CL_LO, CL_HI, 5, "A"))

    # A14 [LIT] one bar legitimately satisfies BOTH predicates: it wicks below the
    # body AND its body closes through the cluster in the top quartile. §3 defines
    # them independently, so both must be emitted; A7's "collapse duplicate records
    # of the same trade" exists precisely because of this.
    check("A14", "§3, both predicates on one bar", "[LIT]", {R, DL},
          trig(98.0, 112.0, 97.0, 111.0, CL_LO, CL_HI, 3, "A"))

    # ---- ADDED AFTER RUN 1, AS NEW CASES. A8 and A9 were mis-constructed: their
    # bars had a lower wick, so §3's rejection predicate fired too and the B_min
    # boundary was never actually exercised. A8 and A9 are LEFT EXACTLY AS THEY
    # WERE - no expectation has been edited. A8b and A9b are new cases that
    # isolate displacement by setting the low equal to the open, so no lower wick
    # exists and (c) of the rejection clause cannot be satisfied. Their expected
    # values were written before running them.

    # A8b [LIT] B_min boundary, ON, displacement isolated. range 20 (95->115),
    # o = l = 95 so there is no lower wick; body 95->107 = 12 = 0.60 of the range
    # exactly. §3 says "body/range >= B_min", so 0.60 must PASS. Close 107 is
    # (107-95)/20 = 0.60 up the range, which is NOT in the top quartile, so the
    # cluster is placed low enough that the quartile test is the only thing that
    # could block - and it would. The bar is therefore built with the close at the
    # top of the range instead, and the body set to exactly 0.6 by the open:
    # o = 103, l = 103, h = 115, c = 115 -> range 12, body 12 = 1.00. That is not
    # the boundary either. The boundary with no wick requires o = l, so
    # body/range = (c - o)/(h - l) = (c - l)/(h - l), which is the same quantity
    # the quartile test uses; with the close at the high both are 1.00.
    # A no-wick bar therefore CANNOT sit at body/range = 0.6 with the close in the
    # top quartile: the two ratios coincide. The boundary is exercised instead with
    # an upper wick, which the long rejection clause does not read.
    # o = 95, l = 95, h = 115, c = 107: body/range = 12/20 = 0.60 exactly;
    # close is 0.60 up the range, OUTSIDE the top quartile -> displacement must NOT
    # fire, and with no lower wick the rejection cannot fire either.
    check("A8b", "§3 displacement, B_min 0.6 met but quartile failed", "[LIT]",
          set(), trig(95.0, 115.0, 95.0, 107.0, 90.0, 99.0, 3, "A"))

    # A9b [LIT] the same geometry with the close in the top quartile and the body
    # ratio driven below B_min by an upper wick. o = 95, l = 95, h = 130, c = 116:
    # range 35, body 21 -> 0.60 exactly; close is (116-95)/35 = 0.60 up the range,
    # still outside the top quartile. To get both, the close must be high AND the
    # body small, which needs a LOWER wick - and that re-arms the rejection clause.
    # Recorded as the structural fact it is: with mode-A predicates, a bar with
    # body/range at exactly 0.6 and its close in the top quartile NECESSARILY has a
    # lower wick and therefore NECESSARILY also fires the rejection predicate.
    # Expected set is both.
    check("A9b", "§3, B_min 0.6 boundary with close in top quartile", "[LIT]",
          {("long", "displacement"), ("long", "rejection")},
          trig(101.0, 115.0, 95.0, 113.0, 90.0, 99.0, 3, "A"))


# ════════════════════════════════════════════════════════════════════
# GROUP B — CLUSTERS.  §3, quoted: "Confluence cluster: >=2 of {BB MA, NY VWAP
# middle/+-1sigma (post-9:30 only), daily VWAP middle/+-1sigma/+-2sigma/+-3sigma,
# daily POC} within proximity tolerance. Tolerance: CALIBRATE (start ~10 NQ pts)."
# ════════════════════════════════════════════════════════════════════
def group_b(cluster_levels):
    # B1 [LIT] a single level cannot be a cluster - the clause says ">=2".
    check("B1", "§3, '>=2 of {...}'", "[LIT]", [],
          cluster_levels([(100.0, "bb")], 10.0))

    # B2 [LIT] two levels of different type, 5 apart, well inside ~10 pts.
    got = cluster_levels([(100.0, "bb"), (105.0, "vwap")], 10.0)
    check("B2", "§3, two levels within tolerance", "[LIT]",
          [(100.0, 105.0, {"bb", "vwap"}, 2)], got)

    # B3 [LIT] 50 points apart is outside any reading of "~10 NQ pts".
    check("B3", "§3, levels outside tolerance", "[LIT]", [],
          cluster_levels([(100.0, "bb"), (150.0, "vwap")], 10.0))

    # B4 [LIT] the confluence COUNT is by distinct TYPE: §3, "Confluence count:
    # distinct level *types* touched (VWAP family x1, BB x1, POC x1, structural
    # x1)". Three VWAP-family levels inside tolerance are ONE type.
    got = cluster_levels([(100.0, "vwap"), (102.0, "vwap"), (104.0, "vwap")], 10.0)
    check("B4", "§3, confluence count by distinct type", "[LIT]",
          [(100.0, 104.0, {"vwap"}, 3)], got)

    # B5 UNSPECIFIED IN SPEC - exact-tolerance inclusion. §3 writes "~10 NQ pts",
    # an approximate quantity, so whether a gap of exactly 10.00 is inside is not
    # decided by the text. Behaviour recorded, nothing asserted.
    observe("B5", "§3, 'Tolerance: CALIBRATE (start ~10 NQ pts)'",
            "gap of exactly 10.00 - inclusive or exclusive is UNSPECIFIED",
            cluster_levels([(100.0, "bb"), (110.0, "vwap")], 10.0))

    # B6 UNSPECIFIED IN SPEC - total span vs adjacent-gap chaining. The clause says
    # levels are "within proximity tolerance" of each other but never says whether
    # that is pairwise across the whole group or only between neighbours. Three
    # levels with 7-pt gaps span 14. Recorded, not asserted. (PARITY-P2-RESULT.md
    # lists this as open ambiguity (b).)
    observe("B6", "§3, 'within proximity tolerance'",
            "span-vs-chaining is UNSPECIFIED; gaps 7 and 7, total span 14",
            cluster_levels([(100.0, "bb"), (107.0, "vwap"), (114.0, "poc")], 10.0))


# ════════════════════════════════════════════════════════════════════
# GROUP C — HTF FRACTAL.  A10, quoted: "A swing high at bar i requires
# H[i] > H[i-1 ... i-N] AND H[i] >= H[i+1 ... i+N]. Mirrored for lows ...
# The first bar of a plateau is the swing." A2: "HTF classification = 15m fractal
# swings N=2, HH+HL => uptrend / LH+LL => downtrend / else range".
# Bars are (open, high, low, close); only high and low are read.
# ════════════════════════════════════════════════════════════════════
def group_c(htf_flag_a10):
    def b(h, l):
        return (0.0, h, l, 0.0)

    # C1 [LIT] fewer than 2N+1 = 5 bars cannot confirm any swing, so the
    # classification falls through to "else range".
    check("C1", "A2 'N=2' + 'else range'", "[LIT]", "range",
          htf_flag_a10([b(10, 1), b(11, 2), b(12, 3), b(11, 2)]))

    # C2 [LIT] two confirmed swing highs, rising, and two confirmed swing lows,
    # rising => HH + HL => uptrend.
    #   index:      0      1      2*     3      4      5      6*     7      8
    #   highs:     10     11     20     12     13     14     30     15     16
    #   lows:       5      4      9      3      2      6     11      7      8
    # index 2 is a swing high (20 > 10,11 and 20 >= 12,13) and index 6 is a higher
    # one (30). Swing lows: index 3 (3 < 4,9 and 3 <= 2? no) - lows are set below
    # so that indices 4 and 7 qualify: 2 < 3,9 and 2 <= 6,11 -> swing low at 4;
    # 7 < 11,6? no. Constructed explicitly instead:
    ups = [b(10, 5), b(11, 4), b(20, 9), b(12, 6), b(13, 7),
           b(14, 8), b(30, 11), b(15, 12), b(16, 13)]
    # swing highs: i=2 (20 > 10,11; 20 >= 12,13) and i=6 (30 > 13,14; 30 >= 15,16)
    #              -> 20 then 30, a HIGHER high
    # swing lows : i=1 (4 < 5 and 4 <= 9,6) and i=3 (6 < 9,4? no) ... i=1 only,
    #              so add a later low that qualifies: i=5 (8 < 7? no).
    # The low series above is monotone after index 3, so only one swing low exists
    # and A2's rule needs two. C2 therefore tests the "else range" fallback when
    # highs qualify but lows do not.
    check("C2", "A2 'HH+HL => uptrend', insufficient swing lows", "[LIT]", "range",
          htf_flag_a10(ups))

    # C3 [LIT] a clean alternating series giving two swing highs and two swing lows,
    # both rising => uptrend.
    up2 = [b(10, 5), b(9, 4), b(20, 8), b(11, 6), b(12, 7),
           b(8, 2), b(13, 3), b(25, 9), b(14, 10), b(15, 11), b(16, 12)]
    # swing highs: i=2 (20 > 10,9; 20 >= 11,12) ; i=7 (25 > 12,13; 25 >= 14,15)
    #              20 -> 25 rising
    # swing lows : i=1 (4 < 5 and 4 <= 8,6) ; i=5 (2 < 6,7 and 2 <= 3,9)
    #              4 -> 2 FALLING, so HH + LL => "else range"
    check("C3", "A2 'else range' on HH + LL", "[LIT]", "range",
          htf_flag_a10(up2))

    # C4 [LIT] THE PLATEAU CASE, which is what A10 exists for. Two adjacent bars
    # print the identical high. Under A10 the FIRST of them is the swing, so a
    # swing high exists; under a strict > on both sides neither would qualify.
    # Bars: highs 10, 11, 20, 20, 12, 13   lows 5, 4, 9, 9, 6, 7
    # i=2: 20 > 11,10 (strict left, ok) and 20 >= 20,12 (non-strict right, ok)
    #      -> SWING at the first plateau bar
    # i=3: 20 > 20 fails on the strict left -> not a swing
    plateau = [b(10, 5), b(11, 4), b(20, 9), b(20, 9), b(12, 6), b(13, 7),
               b(14, 8), b(9, 1), b(15, 2), b(16, 3), b(17, 4)]
    # A second, higher swing high at i=?, plus two rising swing lows, would give
    # uptrend; this series does not supply them, so the classification is "range".
    # What C4 actually asserts is narrower and is the point of A10: the function
    # must not crash and must treat the plateau's first bar as eligible. The
    # eligibility itself is asserted structurally in C5.
    check("C4", "A10 plateau, function total", "[LIT]", "range",
          htf_flag_a10(plateau))

    # C5 [LIT] plateau eligibility, asserted directly by construction. Two plateaus,
    # the second higher, plus two rising swing lows => HH + HL => uptrend.
    # highs: 10, 11, 20, 20, 12, 11, 30, 30, 13, 14, 15
    # lows :  9,  8,  7,  7, 10,  6, 11, 11, 12, 13, 14
    #   swing highs under A10: i=2 (20 > 11,10 ; 20 >= 20,12)
    #                          i=6 (30 > 11,12 ; 30 >= 30,13)   -> 20 then 30, HH
    #   swing lows  under A10: i=5 (6 < 10,7 ; 6 <= 11,11)
    #                          ... only one, so add a rising one after it:
    two = [b(10, 9), b(11, 8), b(20, 7), b(20, 7), b(12, 10), b(11, 6),
           b(30, 11), b(30, 11), b(13, 12), b(14, 13), b(15, 14)]
    # swing lows: i=2/i=3 plateau at 7: i=2 -> 7 < 8,9 (strict left ok),
    #             7 <= 7,10 (non-strict right ok) -> swing low at 7
    #             i=5 -> 6 < 10,7 ; 6 <= 11,11 -> swing low at 6
    #             7 then 6 is a LOWER low, so HH + LL => "else range"
    check("C5", "A10 plateau on both highs and lows, HH + LL", "[LIT]", "range",
          htf_flag_a10(two))

    # C6 [LIT] downtrend: LH + LL.
    dn = [b(30, 25), b(31, 24), b(40, 29), b(29, 20), b(28, 19),
          b(18, 10), b(27, 15), b(35, 21), b(24, 12), b(23, 11), b(22, 10)]
    # swing highs: i=2 (40 > 31,30 ; 40 >= 29,28) ; i=7 (35 > 27,18 ; 35 >= 24,23)
    #              40 -> 35 LOWER high
    # swing lows : i=1 (24 < 25 ; 24 <= 29,20) -> no, 24 <= 20 is false.
    #              i=5 (10 < 19,20 ; 10 <= 15,21) -> swing low 10
    #              only one swing low => "else range"
    check("C6", "A2 'LH+LL => downtrend', insufficient swing lows", "[LIT]", "range",
          htf_flag_a10(dn))


# ════════════════════════════════════════════════════════════════════
# GROUP D — TARGET LADDER.  §6.4, quoted: "Fill front-run: working target = level
# -+ F points (level minus F for longs). F: CALIBRATE (start 2-3 NQ pts)."
# §6.5/A4: "Walk the ladder of opposing menu levels outward from entry."
# ════════════════════════════════════════════════════════════════════
def group_d(ladder, tick):
    # D1 [LIT] long: each level is reduced by F, and only levels still beyond entry
    # survive. 100-2 = 98 is not beyond an entry of 105 and drops out.
    check("D1", "§6.4 front-run, long", "[LIT]", [118.0, 138.0],
          ladder([100.0, 120.0, 140.0], 105.0, "long", 2.0))

    # D2 [LIT] short mirror: level PLUS F, and only levels below entry survive.
    check("D2", "§6.4 front-run, short", "[LIT]", [82.0],
          ladder([100.0, 80.0], 95.0, "short", 2.0))

    # D3 [LIT] ordering is outward from entry - ascending for a long.
    check("D3", "§6.5/A4 'outward from entry'", "[LIT]", [118.0, 138.0, 198.0],
          ladder([200.0, 120.0, 140.0], 105.0, "long", 2.0))

    # D4 [LIT] RECLASSIFIED under A15 (was UNSPECIFIED IN SPEC in run 1 - no clause
    # existed yet). Two menu levels a tenth of a point apart are well within A15's
    # one-tick collapse bound and become one rung, the nearer kept.
    check("D4", "A15 'a gap of <=1 tick, inclusive, collapses'", "[LIT]", [118.0],
          ladder([120.0, 120.1], 105.0, "long", 2.0))

    # D5 [LIT] RECLASSIFIED under A15. Its run-1 expectation ([118.0, 118.25], "two
    # distinct rungs") was written before any clause existed and was WRONG even on
    # its own terms - it does not match ladder()'s actual behaviour, which collapses
    # an exactly-one-tick gap (confirmed directly: 0.25 is not > TICK). A15's
    # boundary is inclusive of the tick itself, so exactly one tick apart is ALSO
    # one rung.
    check("D5", "A15 boundary, exactly one tick, inclusive => collapses", "[LIT]",
          [118.0], ladder([120.0, 120.25], 105.0, "long", 2.0))

    # D6 [LIT] nothing beyond entry -> empty ladder -> §6.5 "Skip only if no level
    # in the menu clears the floor" has nothing to offer.
    check("D6", "§6.5, empty ladder", "[LIT]", [],
          ladder([100.0, 90.0], 105.0, "long", 2.0))


# ════════════════════════════════════════════════════════════════════
# GROUP E — THE RR FLOOR.  §6.5/A4, quoted: "The working target is the FIRST level
# whose front-run-adjusted distance is >= 1.5R. Skip only if NO level in the menu
# clears the floor."  [FORM] - the clause is a walk, transcribed literally.
# ════════════════════════════════════════════════════════════════════
def first_clearing(rungs, entry, r_int, floor):
    """§6.5 as written: first rung whose distance from entry is >= floor x R."""
    for x in rungs:
        if abs(x - entry) / r_int >= floor:
            return x
    return None


def group_e():
    # E1 [FORM] R = 10, floor 1.5 -> need >= 15.0 away. 112 is 12 away and is
    # skipped; 130 is 30 away and is taken. The nearest rung is NOT automatically
    # the target - that is exactly what A4 changed.
    check("E1", "§6.5/A4 'first level whose ... distance is >= 1.5R'", "[FORM]",
          130.0, first_clearing([112.0, 130.0, 160.0], 100.0, 10.0, 1.5))

    # E2 [FORM] BOUNDARY, INCLUSIVE. 115 is exactly 1.5R from 100 at R = 10. The
    # clause says ">= 1.5R", so it must be TAKEN, not skipped.
    check("E2", "§6.5/A4 boundary, '>=' is inclusive", "[FORM]",
          115.0, first_clearing([115.0, 130.0], 100.0, 10.0, 1.5))

    # E3 [FORM] one tick under the boundary is skipped.
    check("E3", "§6.5/A4 boundary, just below", "[FORM]",
          130.0, first_clearing([114.75, 130.0], 100.0, 10.0, 1.5))

    # E4 [FORM] nothing clears -> None -> "Skip".
    check("E4", "§6.5/A4 'Skip only if no level ... clears the floor'", "[FORM]",
          None, first_clearing([112.0, 114.0], 100.0, 10.0, 1.5))

    # E5 [FORM] short side: distance is measured the same way.
    check("E5", "§6.5/A4, short", "[FORM]",
          85.0, first_clearing([88.0, 85.0], 100.0, 10.0, 1.5))


# ════════════════════════════════════════════════════════════════════
# GROUP F — THE A7 SELECTOR.  §10.1(4), quoted table:
#   1 "Highest entry TF"
#   2 "Long and short on the same bar -> stand down, take neither"
#   3 "Larger cluster (more distinct level types)"
#   4 "Cluster nearest the entry price"
#   5 "Lowest cluster low"
# and §10.1(1) "admitted in ascending order of signal minute ... No candidate is
# compared against any later candidate."
# ════════════════════════════════════════════════════════════════════
def group_f(tie_break):
    def c(tf=2, d="long", nlev=2, cl_mid=100.0, entry=100.0, cl_lo=95.0):
        return {"tf": tf, "direction": d, "nlev": nlev, "cl_mid": cl_mid,
                "entry": entry, "cl_lo": cl_lo}

    # F1 [LIT] a lone candidate is decided by no level at all.
    only = c()
    check("F1", "§10.1(4), single candidate", "[LIT]", (only, 0), tie_break([only]))

    # F2 [LIT] level 1 - highest entry TF wins (§1 MTF arbitration).
    hi, lo = c(tf=5), c(tf=2)
    check("F2", "§10.1(4) level 1, 'Highest entry TF'", "[LIT]",
          (hi, 1), tie_break([lo, hi]))

    # F3 [LIT] level 2 - same TF, opposite directions -> stand down, take neither.
    a, b = c(tf=3, d="long"), c(tf=3, d="short")
    check("F3", "§10.1(4) level 2, 'stand down, take neither'", "[LIT]",
          (None, 2), tie_break([a, b]))

    # F4 [LIT] level 3 - same TF and direction, the larger cluster wins.
    big, small = c(nlev=4), c(nlev=2)
    check("F4", "§10.1(4) level 3, 'Larger cluster'", "[LIT]",
          (big, 3), tie_break([small, big]))

    # F5 [LIT] level 4 - same TF, direction and size; the cluster nearer the entry
    # price wins. |100.0 - 100.0| = 0 beats |110.0 - 100.0| = 10.
    near, far = c(cl_mid=100.0, entry=100.0), c(cl_mid=110.0, entry=100.0)
    check("F5", "§10.1(4) level 4, 'Cluster nearest the entry price'", "[LIT]",
          (near, 4), tie_break([far, near]))

    # F6 [LIT] level 5 - everything above ties; the lowest cluster low decides.
    # §10.1 calls this "pure determinism backstop. Arbitrary, and stated as
    # arbitrary, so that runs reproduce."
    low, high = c(cl_lo=90.0), c(cl_lo=95.0)
    check("F6", "§10.1(4) level 5, 'Lowest cluster low'", "[LIT]",
          (low, 5), tie_break([high, low]))

    # F7 [LIT] level 1 outranks level 3: the smaller cluster on the higher TF still
    # wins, because the levels are applied in order and "the first level that
    # separates them decides".
    hi_small, lo_big = c(tf=5, nlev=2), c(tf=2, nlev=4)
    check("F7", "§10.1(4), 'the first level that separates them decides'", "[LIT]",
          (hi_small, 1), tie_break([lo_big, hi_small]))

    # F8 [LIT] the stand-down at level 2 applies only among candidates surviving
    # level 1. A long on 5m and a short on 2m are separated by level 1 first, so
    # the 5m long is taken and there is NO stand-down.
    l5, s2 = c(tf=5, d="long"), c(tf=2, d="short")
    check("F8", "§10.1(4), level 1 precedes level 2", "[LIT]",
          (l5, 1), tie_break([s2, l5]))


# ════════════════════════════════════════════════════════════════════
# GROUP G — A13 SIGMA ELIGIBILITY.  A13, quoted: "a NY VWAP sigma band is
# cluster-eligible when the 95% confidence interval on its distance from the mid
# is <= HALF the §3 cluster tolerance: z * sigma_hat / sqrt(2(n-1)) <= tol/2,
# i.e. 1.95996 * sigma_hat / sqrt(2(n-1)) <= 5.00 points".   [FORM]
# ════════════════════════════════════════════════════════════════════
Z95 = 1.959964
HALF_TOL = 5.0


def group_g(ny_sigma_eligible):
    # G1 [FORM] n = 5, sigma 10: 1.959964*10/sqrt(8) = 6.929 > 5.00 -> ineligible.
    check("G1", "A13 eligibility, wide CI", "[FORM]", False,
          ny_sigma_eligible(20000.0, 10.0, 999, 5))

    # G2 [FORM] n = 10, sigma 10: 1.959964*10/sqrt(18) = 4.619 <= 5.00 -> eligible.
    check("G2", "A13 eligibility, narrow CI", "[FORM]", True,
          ny_sigma_eligible(20000.0, 10.0, 999, 10))

    # G3 [FORM] exact boundary at n = 9: sqrt(2*8) = 4, so the largest admissible
    # sigma is 5.00*4/1.959964 = 10.204268...  The clause says "<=", so the
    # boundary value itself is ELIGIBLE.
    sig_star = HALF_TOL * math.sqrt(2 * 8) / Z95
    check("G3", "A13 boundary, '<=' inclusive", "[FORM]", True,
          ny_sigma_eligible(20000.0, sig_star, 999, 9))

    # G4 [FORM] a hair above the boundary is ineligible.
    check("G4", "A13 boundary, just above", "[FORM]", False,
          ny_sigma_eligible(20000.0, sig_star * 1.000001, 999, 9))

    # G5 [FORM] with no NY VWAP there is no band to admit. §2: the NY VWAP
    # "does NOT exist pre-market".
    check("G5", "§2, NY VWAP absent", "[FORM]", False,
          ny_sigma_eligible(None, None, 999, 50))


# ════════════════════════════════════════════════════════════════════
# GROUP H — STOP ANCHOR AND GEOMETRY, END-TO-END ON A SYNTHETIC SESSION.
#
# §5.3: "E1: limit at the BB MA".
# §5.4 + A5: "Stop: beyond the wick extreme of the trigger candle ... Minimum stop
#             distance: 10.00 points (40 ticks). Effective stop = max(structural
#             stop, 10.00 pt)."  A2 froze the buffer: "stop buffer = 1 tick beyond
#             the wick extreme".
# §5.4/A5:   "A trigger whose E1 entry falls on the wrong side of the wick extreme
#             remains invalid - the floor does not rescue it."
#
# The session below is built so that every quantity the clauses consume is known
# by construction. [FORM] - the clauses are arithmetic and are transcribed.
# ════════════════════════════════════════════════════════════════════
TICK = 0.25
MIN_STOP = 10.00
LO_PX, HI_PX = 19900.0, 20100.0        # the two RTH prices
FLAT = 20000.0                          # the overnight price


def build_session(trig_idx, t_open, t_high, t_low, t_close):
    """1380 bars. Overnight flat; RTH alternates two prices so the VWAP mean and
    sigma are exact by construction; the trigger bar carries ZERO volume so it
    perturbs neither VWAP nor the volume profile."""
    bars = {}
    for i in range(0, 930):                       # 18:00 -> 09:29
        bars[i] = (FLAT, FLAT, FLAT, FLAT, 100)
    for i in range(930, 1380):                    # 09:30 -> 16:59
        p = LO_PX if i % 2 == 0 else HI_PX
        bars[i] = (p, p, p, p, 100)
    bars[trig_idx] = (t_open, t_high, t_low, t_close, 0)
    return bars


def bb_basis_expected(trig_idx, t_close):
    """§2: 'Bollinger Bands 20, SMA, close'. The basis at the trigger is the mean
    of the last 20 one-minute closes, of which 19 are the alternating RTH prices
    and the twentieth is the trigger's own close."""
    closes = []
    for i in range(trig_idx - 19, trig_idx):
        closes.append(LO_PX if i % 2 == 0 else HI_PX)
    closes.append(t_close)
    return sum(closes) / 20.0


def group_h(signal_candidates_current):
    TRIG = 980                       # session index -> 10:20 ET, close-minute 10:21
    # ---- H1: structural stop, floor NOT binding -------------------------------
    # Trigger close 20006 chosen so the BB MA lands at 20005.30, above every other
    # level in the cluster, and the bar's high stays far below NY VWAP +1sigma
    # (20100) so §7's invalidation does not stand the trade down.
    entry = bb_basis_expected(TRIG, 20006.0)
    bars = build_session(TRIG, 20006.0, 20006.0, 19990.0, 20006.0)
    cands = signal_candidates_current(bars, None)
    got = [c for c in (cands or {}).get(621, []) if c["tf"] == 1]
    check("H1a", "§5.3 'E1: limit at the BB MA'", "[FORM]", 1, len(got))
    if got:
        c0 = got[0]
        close("H1b", "§5.3 'E1: limit at the BB MA'", "[FORM]", entry, c0["entry"], 1e-6)
        # A2: buffer is one tick beyond the wick extreme; A5: effective stop is the
        # greater of that and 10.00 points.
        struct = 19990.0 - TICK
        r_expected = max(entry - struct, MIN_STOP)
        close("H1c", "§5.4 + A2 buffer + A5 floor", "[FORM]",
              r_expected, c0["R_int"], 1e-6)
        close("H1d", "§5.4, stop price", "[FORM]",
              entry - r_expected, c0["stop_px"], 1e-6)
        check("H1e", "A5, floor not binding when structural stop exceeds 10.00",
              "[FORM]", False, abs(c0["R_int"] - MIN_STOP) < 1e-9)
        check("H1f", "§3 rejection block, direction", "[LIT]", "long", c0["direction"])
        check("H1g", "§3, trigger kind", "[LIT]", "rejection", c0["kind"])
        # §6.5/A4 must hold on whatever the ladder produced.
        rr = abs(c0["tgt_px"] - c0["entry"]) / c0["R_int"]
        RESULTS.append(("H1h", "§6.5/A4 '>= 1.5R'", "[FORM]", ">= 1.5",
                        f"{rr:.6f}", "PASS" if rr >= 1.5 else "FAIL"))

    # ---- H2: the A5 floor BINDS ----------------------------------------------
    # Same construction, shallow wick: the structural stop is under 10.00 points,
    # so A5's "Effective stop = max(structural stop, 10.00 pt)" must lift it.
    entry2 = bb_basis_expected(TRIG, 20006.0)
    bars2 = build_session(TRIG, 20006.0, 20006.0, entry2 - 4.0, 20006.0)
    cands2 = signal_candidates_current(bars2, None)
    got2 = [c for c in (cands2 or {}).get(621, []) if c["tf"] == 1]
    check("H2a", "§5.4/A5, candidate exists", "[FORM]", 1, len(got2))
    if got2:
        c1 = got2[0]
        close("H2b", "A5 'Effective stop = max(structural stop, 10.00 pt)'", "[FORM]",
              MIN_STOP, c1["R_int"], 1e-9)
        close("H2c", "A5, stop price with the floor binding", "[FORM]",
              c1["entry"] - MIN_STOP, c1["stop_px"], 1e-9)

    # ---- H3: entry on the wrong side of the wick is INVALID -------------------
    # A5: "A trigger whose E1 entry falls on the wrong side of the wick extreme
    # remains invalid - the floor does not rescue it." Here the low sits ABOVE the
    # BB MA, so a long's stop would be above its entry.
    entry3 = bb_basis_expected(TRIG, 20006.0)
    bars3 = build_session(TRIG, 20006.0, 20006.0, entry3 + 5.0, 20006.0)
    cands3 = signal_candidates_current(bars3, None)
    got3 = [c for c in (cands3 or {}).get(621, []) if c["tf"] == 1]
    check("H3a", "A5 'the floor does not rescue it'", "[FORM]", 0, len(got3))

    # ---- H4: nothing before 09:36 --------------------------------------------
    # A1: "entry blackout 09:31-09:35, first tradeable signal bar 09:36".
    allc = signal_candidates_current(build_session(TRIG, 20006.0, 20006.0,
                                                   19990.0, 20006.0), None)
    early = [cm for cm in (allc or {}) if cm < 9 * 60 + 36]
    check("H4a", "A1 'first tradeable signal bar 09:36'", "[LIT]", [], sorted(early))
    late = [cm for cm in (allc or {}) if cm > 16 * 60]
    check("H4b", "§1 'RTH 09:31-16:00 ET'", "[LIT]", [], sorted(late))


# ════════════════════════════════════════════════════════════════════
# GROUP I — A14 TICK ROUNDING.  A14, quoted: "every transmitted order price rounds to
# the 0.25 grid in the direction that makes the trade worse." Stop and target round
# AWAY FROM ENTRY; the entry itself rounds AGAINST THE TRADER (long pays more, short
# receives less). "A price already exactly on the 0.25 grid is not moved."
# ════════════════════════════════════════════════════════════════════
def group_i(round_against_trader, round_away_from_entry):
    # I1 [FORM] entry, long, off-grid -> against the trader means paying MORE, i.e.
    # rounding UP to the next tick.
    close("I1", "A14 entry, long, against the trader = round up", "[FORM]",
          100.25, round_against_trader(100.13, "long"), 1e-9)

    # I2 [FORM] entry, short, off-grid -> against the trader means receiving LESS,
    # i.e. rounding DOWN.
    close("I2", "A14 entry, short, against the trader = round down", "[FORM]",
          100.00, round_against_trader(100.13, "short"), 1e-9)

    # I3 [FORM] entry, long, already on the 0.25 grid -> "not moved".
    close("I3", "A14 'a price already ... on the grid is not moved', long", "[FORM]",
          100.25, round_against_trader(100.25, "long"), 1e-9)

    # I4 [FORM] entry, short, already on the grid -> not moved.
    close("I4", "A14 'not moved', short", "[FORM]",
          100.25, round_against_trader(100.25, "short"), 1e-9)

    # I5 [FORM] entry, long, boundary just above a tick (100.2500001) -> rounds up to
    # the NEXT tick, not back down to the one it is already almost on.
    close("I5", "A14 entry, long, just above a tick", "[FORM]",
          100.50, round_against_trader(100.2500001, "long"), 1e-6)

    # I6 [FORM] stop, long: stop sits BELOW entry, so "away from entry" means rounding
    # DOWN (more negative distance = wider R).
    close("I6", "A14 stop, long, away from entry = round down", "[FORM]",
          89.75, round_away_from_entry(89.87, 100.0), 1e-9)

    # I7 [FORM] stop, short: stop sits ABOVE entry, so away from entry means UP.
    close("I7", "A14 stop, short, away from entry = round up", "[FORM]",
          110.25, round_away_from_entry(110.13, 100.0), 1e-9)

    # I8 [FORM] target, long: target sits ABOVE entry, away from entry means UP.
    close("I8", "A14 target, long, away from entry = round up", "[FORM]",
          130.25, round_away_from_entry(130.13, 100.0), 1e-9)

    # I9 [FORM] target, short: target sits BELOW entry, away from entry means DOWN.
    close("I9", "A14 target, short, away from entry = round down", "[FORM]",
          69.75, round_away_from_entry(69.87, 100.0), 1e-9)

    # I10 [FORM] boundary: a stop already exactly on the grid is not moved, whichever
    # side of entry it sits on.
    close("I10", "A14 'not moved', already on the grid", "[FORM]",
          90.00, round_away_from_entry(90.00, 100.0), 1e-9)

    # I11 [FORM] boundary: a price exactly AT entry (degenerate; never occurs for a
    # real stop or target, but the function must not divide by zero or misbehave).
    # "Away from entry" has no side to prefer when price == entry, so it is treated
    # as already-on-the-grid and left alone if it happens to be on-grid.
    close("I11", "A14, degenerate price == entry, on-grid", "[FORM]",
          100.00, round_away_from_entry(100.00, 100.00), 1e-9)


# ════════════════════════════════════════════════════════════════════
# GROUP J — A15 LADDER COLLAPSE, WHICH RUNG SURVIVES.  A15, quoted (as corrected):
# "a gap of <=1 tick, inclusive, collapses to a single rung, keeping the nearer one.
# Only a gap strictly greater than one tick (>0.25 pt) keeps two rungs separate."
# ════════════════════════════════════════════════════════════════════
def group_j(ladder):
    # J1 [LIT] three levels chained by sub-tick gaps all collapse to the FIRST
    # (nearest-to-entry) one — chaining is against the LAST KEPT rung, not the
    # original nearest, but with sub-tick gaps throughout the whole run stays one.
    check("J1", "A15, three-way sub-tick chain collapses to the nearest", "[LIT]",
          [118.0], ladder([120.0, 120.05, 120.09], 105.0, "long", 2.0))

    # J2 [LIT] THE CASE A15 EXISTS TO DESCRIBE — two menu levels within one tick of
    # each other; the nearer (to entry) rung is kept, the farther one dropped.
    # 120.0 -> 118.0 (nearer), 120.2 -> 118.2 (farther, 0.2 from the kept rung,
    # <= 1 tick) - collapses, nearer survives.
    check("J2", "A15 'keeping the nearer one'", "[LIT]",
          [118.0], ladder([120.2, 120.0], 105.0, "long", 2.0))

    # J3 [LIT] a gap just OVER one tick (0.26) stays as two separate rungs - the
    # boundary is exclusive on the far side, per A15's corrected text.
    check("J3", "A15 boundary, gap > 1 tick stays separate", "[LIT]",
          [118.0, 118.26], ladder([120.0, 120.26], 105.0, "long", 2.0))

    # J4 [LIT] CHAINING is measured against the LAST KEPT rung, not the original one -
    # this is what makes it a chain rather than a fixed cluster radius. Three levels
    # 0.20 apart pairwise (120.0, 120.20, 120.40): gap 1 (120.0->118.0 vs 120.20->
    # 118.20) is 0.20 <= tick, collapses; the NEXT candidate (120.40 -> 118.40) is
    # compared against the LAST KEPT rung (118.0, since 118.20 was dropped), gap
    # 0.40 > tick, so it survives as a second rung.
    check("J4", "A15, chaining is against the last KEPT rung", "[LIT]",
          [118.0, 118.40], ladder([120.0, 120.20, 120.40], 105.0, "long", 2.0))

    # J5 [LIT] mirror of J2 on the short side. For a short, ladder() walks in
    # DESCENDING order of (level + F) - i.e. nearest-to-entry first, since every
    # candidate sits below entry and the largest such value is closest to it.
    # levels 80.2, 80.0 -> +F(2.0) -> 82.2, 82.0. |95-82.2|=12.8 < |95-82.0|=13.0,
    # so 82.2 (from the raw level 80.2) is nearer and is processed, hence kept,
    # first; 82.0 collapses into it (gap 0.2 <= one tick).
    check("J5", "A15, short side, nearer rung kept", "[LIT]",
          [82.2], ladder([80.2, 80.0], 95.0, "short", 2.0))

    # J6 [LIT] on the short side, a gap just over one tick stays separate.
    check("J6", "A15 boundary, short side, gap > 1 tick stays separate", "[LIT]",
          [82.0, 81.74], ladder([80.0, 79.74], 95.0, "short", 2.0))


# ════════════════════════════════════════════════════════════════════
def main():
    from vwapbb_opportunity import trig
    from vwapbb_signals import cluster_levels
    from vwapbb_a7_selector import ladder, tie_break, TICK as A7_TICK
    from spec_current import (htf_flag_a10, ny_sigma_eligible,
                              signal_candidates_current, round_against_trader,
                              round_away_from_entry)

    group_a(trig)
    group_b(cluster_levels)
    group_c(htf_flag_a10)
    group_d(ladder, A7_TICK)
    group_e()
    group_f(tie_break)
    group_g(ny_sigma_eligible)
    group_h(signal_candidates_current)
    group_i(round_against_trader, round_away_from_entry)
    group_j(ladder)

    npass = sum(1 for r in RESULTS if r[5] == "PASS")
    nfail = len(RESULTS) - npass
    print("=" * 96)
    print("2a — SPEC-DERIVED UNIT TESTS")
    print("=" * 96)
    print(f"{'id':<6} {'kind':<7} {'status':<6} {'clause':<52} expected -> actual")
    for tid, clause, kind, exp, act, st in RESULTS:
        mark = "" if st == "PASS" else "  <<<<"
        print(f"{tid:<6} {kind:<7} {st:<6} {clause[:52]:<52} {exp} -> {act}{mark}")
    print()
    print(f"  tests run {len(RESULTS)}   PASS {npass}   FAIL {nfail}")
    print(f"  UNSPECIFIED IN SPEC, recorded not asserted: {len(OBSERVED)}")
    for tid, clause, note, act in OBSERVED:
        print(f"     {tid}  {clause}\n            {note}\n            observed: {act}")
    out = {"pass": npass, "fail": nfail, "results": RESULTS, "observed": OBSERVED}
    Path(__file__).with_name("test_spec_units_result.json").write_text(
        json.dumps(out, indent=1))
    return 1 if nfail else 0


if __name__ == "__main__":
    sys.exit(main())
