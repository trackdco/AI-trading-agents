"""Market Engine — deterministic NQ setup detection.

Consumes 1-minute NQ bars (historical replay or live Databento), computes the
strategy indicators, detects the documented mechanical setups, and emits a
candidate JSON. No LLM calls, no order execution, no account state.
"""
__version__ = "0.1.0"
