"""newslab config — release registry, grids, holdout seal.

Units doctrine (Angus): every headline number is reported in R AND points,
R first. Dollar conversion: NQ $20/pt, MNQ $2/pt.
"""
from __future__ import annotations
import os

TZ_ET = "America/New_York"

DOLLARS_PER_POINT = {"NQ": 20.0, "MNQ": 2.0}

# Census grids
STOP_GRID_PTS = [10, 20, 30, 50]          # bracket stop distances for gap-fill tables
HORIZONS_MIN = [5, 15, 30, 60, 120]       # post-release measurement horizons
DRIFT_WINDOWS_MIN = [60, 30, 5]           # pre-release drift lookbacks
DEFAULT_STOP_PTS = 20                      # R denominator for headline tables

# ---------------------------------------------------------------------------
# HOLDOUT SEAL — placeholder boundary, FROZEN ONLY BY ANGUS'S RULING in
# PREREG-L3.md. Code refuses to score sealed rows unless NEWSLAB_UNSEAL=1.
# Bars in repo end 2026-01-31; default seals the final 4 months of coverage.
# ---------------------------------------------------------------------------
SEAL_FROM = os.environ.get("NEWSLAB_SEAL_FROM", "2025-10-01")

def unsealed() -> bool:
    return os.environ.get("NEWSLAB_UNSEAL", "0") == "1"

# ---------------------------------------------------------------------------
# Release registry.
# time_et: official release time (verify per event via calendar join).
# alfred: FRED/ALFRED series used for FIRST-PRINT actuals (vintage-safe).
#   transform: "pch" = MoM % computed from SAME-VINTAGE index levels,
#              "diff_k" = month diff in thousands, "level" = as-is.
# surprise_field: which actual is z-scored for the headline surprise.
# ---------------------------------------------------------------------------
RELEASES = {
    "cpi": dict(tier=1, time_et="08:30",
        alfred={"headline_mom": ("CPIAUCSL", "pch"),
                "core_mom":     ("CPILFESL", "pch")},
        surprise_field="core_mom",
        note="#1 NQ mover this cycle; algos read the unrounded 2nd decimal."),
    "nfp": dict(tier=1, time_et="08:30",
        alfred={"payrolls_k":   ("PAYEMS",  "diff_k"),
                "unrate":       ("UNRATE",  "level"),
                "ahe_mom":      ("CES0500000003", "pch")},
        surprise_field="payrolls_k",
        note="Two surveys; tag all three surprises — they can conflict."),
    "fomc": dict(tier=1, time_et="14:00",
        alfred={},  # decision & consensus come from calendar/manual, not FRED
        surprise_field="decision_bps",
        note="Two-phase event (14:00 stmt, 14:30 presser). Tag SEP meetings."),
    "ppi": dict(tier=1, time_et="08:30",
        alfred={"headline_mom": ("PPIFIS", "pch"),
                # VERIFIED 12 Aug 2026 against the FRED series metadata, not
                # guessed: PPIFES = "Producer Price Index by Commodity: Final
                # Demand: Final Demand Less Foods and Energy", Seasonally
                # Adjusted, Monthly. That is the core PPI the market trades.
                # Rejected: WPSFD4131 is the older FINISHED GOODS ex food/
                # energy concept, and PPICOR is the same series NSA.
                "core_mom": ("PPIFES", "pch")},
        surprise_field="headline_mom",
        note="Punches hardest when it confirms/contradicts CPI next day."),
    "pce": dict(tier=1, time_et="08:30",
        alfred={"headline_mom": ("PCEPI",   "pch"),
                "core_mom":     ("PCEPILFE","pch")},
        surprise_field="core_mom",
        note="Mostly pre-priced from CPI+PPI; small clean surprises."),
    "retail": dict(tier=2, time_et="08:30",
        alfred={"headline_mom": ("RSAFS", "pch")},
        surprise_field="headline_mom",
        note="Control group is the read-through; survived old jackknife n=4."),
    "claims": dict(tier=2, time_et="08:30",
        alfred={"initial_k": ("ICSA", "level")},
        surprise_field="initial_k",
        note="Weekly Thursday. n~187 — the statistical workhorse."),
    "gdp_adv": dict(tier=2, time_et="08:30",
        alfred={"real_gdp_saar": ("A191RL1Q225SBEA", "level")},
        surprise_field="real_gdp_saar",
        note="ADVANCE print only; 2nd/3rd estimates are dead events."),
    "ism_mfg": dict(tier=2, time_et="10:00", alfred={},
        surprise_field="pmi",
        note="Lands INSIDE RTH — different liquidity than 08:30 prints."),
    "ism_svc": dict(tier=2, time_et="10:00", alfred={},
        surprise_field="pmi",
        note="Often the bigger mover of the two ISMs."),
    # --- added for the forward trading calendar (dates first; ALFRED maps
    # stay empty until L0b needs actuals for them) ---
    "jolts": dict(tier=2, time_et="10:00", alfred={},
        surprise_field="openings_k",
        note="Lands INSIDE RTH. Fed watches it for labour slack."),
    "adp": dict(tier=2, time_et="08:15", alfred={},
        surprise_field="employment_k",
        note="08:15 — the only pre-08:30 print; sets the tone into NFP week."),
    "umich": dict(tier=2, time_et="10:00", alfred={},
        surprise_field="sentiment",
        note="Inflation EXPECTATIONS sub-index moves more than the headline."),
}

FAMILIES = list(RELEASES)
TIER1 = [k for k, v in RELEASES.items() if v["tier"] == 1]

# Sign convention for "surprise direction → expected NQ direction".
# Hot inflation / hot jobs = hawkish = NQ DOWN → sign flip (-1).
# Strong growth prints are ambiguous regime-dependent; start hawkish (-1)
# and let the census measure it. Claims: HIGHER claims = weak labor = dovish
# = NQ UP → +1 on the raw surprise.
SURPRISE_TO_NQ_SIGN = {
    "cpi": -1, "nfp": -1, "ppi": -1, "pce": -1, "retail": -1,
    "gdp_adv": -1, "ism_mfg": -1, "ism_svc": -1, "claims": +1,
    "fomc": -1,  # hawkish surprise (higher-than-priced rate) = NQ down
}

MIN_SURPRISE_HISTORY = 8   # events required before a causal z is emitted
