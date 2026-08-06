"""Window causality — the mechanical form of `docs/VALIDATION-PROCESS.md` §2.5.

The standing causality rule has always been *"decision at minute t uses only ≤ t
information"*, and it has always been audited **per column**. That audit is not
sufficient, and this programme has now produced three separate proofs of it:

- **LDN-SWP-01** — every input to group P was individually a legal, observed fact. The
  defect was that the *window* over which group membership was determined stayed open
  until the outcome window had closed. Column-wise the census was clean; the primary
  statistic was an artifact.
- **LDN-ATC-01** — the L0 lookahead audit certified "no column reads a bar that closes
  after the decision minute", and it was right about every column. It missed the
  interaction: the LTA condition is evaluated over 07:00–08:00 while the trigger scan
  fires from 07:30, so 27% of the census was gated on bars that had not closed.
- **LDN-INV-01** — the quintile boundaries are era-local, so the cut applied to a
  January day is defined by a distribution that includes the following December.

The generalisation is that causality is a property of the **(condition window, decision
time)** pair, not of a column. A rule is causal only when every condition it composes is
*settled* by the moment the rule can fire:

    for every rule R composed of conditions c1..cn with evaluation windows W1..Wn,
    and every decision time T at which R can fire:
        max(close_time(Wi)) <= T   for all i

That inequality is the whole check. It is cheap, it is decidable before any data is
pulled, and — critically — it catches the defect class that the fragility ladder cannot,
because **circularity is robust**: a lookahead survives drop-top-3, winsorisation and
every trim depth we run, and comes out looking large, stable and significant.

Worked example of a rule that passes, from `docs/VERDICT-LDN-DEF-01.md` §4: every
footprint minute read lies in `[t-3, t]` and the outcome is measured over
`(t, window close]`, so the condition window closes exactly at the decision minute.
`assert max(mins) <= t` fired on every event and the census is causally clean.

Usage — transcribe the prereg's §1 per-condition window table directly:

    rule = Rule.from_table(
        "LDN-DEF-01 absorption read",
        [("ABSORB",  "t-3",  Rel(0)),
         ("level",   "t-3",  Rel(0))],
        decision_times=["08:15", "09:30"],
    )
    assert_causal(rule)          # raises CausalityViolation with a full report

The prereg table and this object are the same declaration written twice; keeping them in
sync is the point.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence, Union

__all__ = [
    "CausalityViolation",
    "Condition",
    "Rel",
    "Rule",
    "Violation",
    "Window",
    "assert_causal",
    "resolve",
    "to_minutes",
    "violations",
    "worst_lag",
]


class CausalityViolation(AssertionError):
    """A rule can fire before one of its conditions is settled."""


@dataclass(frozen=True)
class Rel:
    """A window edge defined relative to the decision minute T, in minutes.

    `Rel(0)` means "closes at T" and is legal — the decision minute's own bar has closed
    by the time the decision is taken, which is the convention every census in this repo
    uses. `Rel(-3)` closes three minutes before T. `Rel(+15)` closes fifteen minutes
    after the decision and is a lookahead by construction.
    """

    minutes: int

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return f"T{self.minutes:+d}m" if self.minutes else "T"


Edge = Union[str, int, Rel]


def to_minutes(v: Union[str, int]) -> int:
    """`"07:45"` -> 465. Ints pass through so callers can work in raw minutes."""
    if isinstance(v, bool):  # bool is an int subclass; almost certainly a mistake
        raise TypeError("clock edge must be 'HH:MM' or minutes-from-midnight, not bool")
    if isinstance(v, int):
        return v
    hh, _, mm = str(v).partition(":")
    return int(hh) * 60 + int(mm)


def resolve(edge: Edge, T: Union[str, int]) -> int:
    """Resolve a window edge to minutes-from-midnight, given decision time T."""
    t = to_minutes(T)
    return t + edge.minutes if isinstance(edge, Rel) else to_minutes(edge)


@dataclass(frozen=True)
class Window:
    """`opens` is documentation; `closes` is the binding edge.

    Only the close matters to causality: it is the moment the last datum the condition
    depends on becomes known. A window that opens in the future is a different bug.
    """

    opens: Edge
    closes: Edge

    def close_at(self, T: Union[str, int]) -> int:
        return resolve(self.closes, T)

    def describe(self) -> str:
        f = (lambda e: str(e) if isinstance(e, Rel) else str(e))
        return f"{f(self.opens)}..{f(self.closes)}"


@dataclass(frozen=True)
class Condition:
    """One row of the prereg's per-condition window table."""

    name: str
    window: Window
    note: str = ""


@dataclass(frozen=True)
class Violation:
    rule: str
    condition: str
    decision_time: int
    close_time: int
    window: str

    @property
    def lag_minutes(self) -> int:
        """How far past the decision the condition stays unsettled. Always > 0."""
        return self.close_time - self.decision_time

    def __str__(self) -> str:
        return (f"{self.rule}: condition '{self.condition}' (window {self.window}) closes "
                f"at {_clock(self.close_time)} but the rule can fire at "
                f"{_clock(self.decision_time)} — {self.lag_minutes} min of lookahead")


def _clock(m: int) -> str:
    """Render as a clock when the value is a wall-clock minute, else as a bare index.

    Units are the caller's choice — the check only ever compares two edges to each
    other, so minutes, day indices or bar indices all work, as long as one rule uses
    one unit. LDN-INV-01's era-local quintile is a day-scale window, not a clock one.
    """
    return f"{m // 60:02d}:{m % 60:02d}" if 0 <= m < 24 * 60 else f"t={m}"


@dataclass(frozen=True)
class Rule:
    """A rule, its conditions, and every minute at which it can fire.

    `decision_times` must be the *full* admissible set, not the typical case. LDN-ATC-01
    is the cautionary tale: the chain was reasoned about at 08:00 and later, where it is
    clean, while the trigger scan actually opens at 07:30, where it is not.
    """

    name: str
    conditions: tuple[Condition, ...]
    decision_times: tuple[Union[str, int], ...]
    note: str = field(default="", compare=False)

    @classmethod
    def from_table(
        cls,
        name: str,
        rows: Iterable[Sequence],
        decision_times: Iterable[Union[str, int]],
        note: str = "",
    ) -> "Rule":
        """Build from `(condition, opens, closes[, note])` rows — the prereg table."""
        conds = []
        for row in rows:
            cond, opens, closes, *rest = row
            conds.append(Condition(cond, Window(opens, closes), rest[0] if rest else ""))
        if not conds:
            raise ValueError(f"{name}: a rule with no conditions cannot be audited")
        dts = tuple(decision_times)
        if not dts:
            raise ValueError(f"{name}: declare every minute at which the rule can fire")
        return cls(name, tuple(conds), dts, note)


def violations(rule: Rule) -> list[Violation]:
    """Every (condition, decision time) pair that breaks `close_time(W) <= T`.

    Returned worst-first so the report leads with the largest lookahead.
    """
    out = [
        Violation(rule.name, c.name, to_minutes(T), c.window.close_at(T),
                  c.window.describe())
        for T in rule.decision_times
        for c in rule.conditions
        if c.window.close_at(T) > to_minutes(T)
    ]
    return sorted(out, key=lambda v: (-v.lag_minutes, v.decision_time, v.condition))


def worst_lag(rule: Rule) -> int:
    """Largest lookahead in minutes; 0 when the rule is causal."""
    v = violations(rule)
    return v[0].lag_minutes if v else 0


def assert_causal(rule: Rule) -> None:
    """Raise `CausalityViolation` listing every breach. No output, no exceptions: pass.

    Call this in the census script itself, next to `fit_only()` and the sealed-span
    assertions, so the answer lands before any result can be read. LDN-DEF-01 is the
    precedent for asserting causality in code rather than by eye.
    """
    v = violations(rule)
    if not v:
        return
    lines = "\n".join(f"  - {x}" for x in v)
    raise CausalityViolation(
        f"{rule.name}: {len(v)} window-causality violation(s) "
        f"across {len(rule.decision_times)} decision time(s):\n{lines}\n"
        f"A rule is causal only when every condition is SETTLED by the minute it can "
        f"fire. Restrict the decision times, or close the windows earlier — do not "
        f"reason that the affected cohort is 'the most on-mechanism part of the set'."
    )
