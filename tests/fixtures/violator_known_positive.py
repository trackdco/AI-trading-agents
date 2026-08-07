"""KNOWN-POSITIVE fixture for the chokepoint AST test. This module deliberately
reads a raw data file directly, building the path in a variable first — the
exact pattern a regex misses. The guard test MUST detect this file; if it
doesn't, the scan is broken and every clean result from it is meaningless.
This module must never be imported by real code."""

path_part = "glbx-mdp3-20250602"
full_path = path_part + ".mbp-10_condensed.csv"


def sneaky_read():
    with open(full_path) as f:  # direct raw read through a variable-built path
        return f.read()
