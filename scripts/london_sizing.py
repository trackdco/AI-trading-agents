#!/usr/bin/env python3
"""London 10:00-13:00 book: day-stop base + evidence-based sizing grid (see chat/commit for results).
V1 1.5x CVD-confirm; V2 +0.5x covered-fail; V3 1.5x score>=4; V4 combined 2x/1.5x/1x/0.5x.
All boosts (no vetoes). Verified both-years + 4-halves. Run: python3 london_sizing.py"""
# (analysis performed inline in session; this file records the exact rules for reproduction)
RULES = {
 "book": "London Trend Pullback, entries 10:00-13:00 UK, M15, vol-fade, structural stop, 3R, flat 16:30 UK",
 "day_stop": "stop trading the window after the first LOSS of the day",
 "V1": "size 1.5x when 3-min real-CVD confirms direction at entry; 1.0x otherwise",
 "V2": "V1 plus 0.5x when CVD covered-but-against",
 "V3": "1.5x when Angus-score>=4 (StopFloor+ROOM+ASIA+NotEarlyTight)",
 "V4": "2x confirm+score4; 1.5x either; 0.5x covered-fail; 1x else",
}
print(RULES)
