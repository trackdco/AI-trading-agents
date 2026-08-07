#!/usr/bin/env python3
"""Nightly archive of Sierra's .scid + .depth files to Backblaze B2 (the live-book record).

WHY THIS EXISTS: the funded feed is MBP-10 (Aggregated, Lucid Market Depth add-on) — there is
no raw MBO to capture — and Sierra retains historical **.depth only ~30 days**, after which the
files CANNOT be re-downloaded. During paper these files are the ONLY record of the live book we
will ever have, so this offload must be running BEFORE paper starts (non-blocking for go-live,
but a hard prerequisite for the research substrate). Idempotent: safe to re-run; it only sends
new/changed files and catches up any un-archived recent .depth day before it ages out.

Run it:
    python scripts/archive_sierra.py                 # uses config/live.yaml [archive]
    python scripts/archive_sierra.py --dry-run       # list what WOULD upload, no network
    python scripts/archive_sierra.py --register      # print the Windows scheduled-task command

Register the nightly Windows task (run the printed command once, in an Admin PowerShell on the
VPS). Default 17:30 CT — just after the 17:00 CT CME close/maintenance, so the prior session's
.depth day file is complete. Needs B2_KEY_ID / B2_APP_KEY in the environment and `pip install
b2sdk`.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.canon.infra import B2Offload, SierraArchiver, make_b2_uploader  # noqa: E402

DEFAULTS = {
    "data_dir": "C:/SierraChart/Data",
    "bucket": "nq-sierra-book",
    "manifest": "output/live/archive_manifest.json",
    "prefix": "sierra",
    "root": "NQ",
    "suffix": "-CME",
}


def _cfg(config_path: Path) -> dict:
    if not config_path.exists():
        return dict(DEFAULTS)
    doc = yaml.safe_load(config_path.read_text()) or {}
    return {**DEFAULTS, **(doc.get("archive") or {})}


def register_command(config_path: str, time_ct: str = "17:30", task: str = "SierraArchive") -> str:
    """The `schtasks` line that registers this script as a daily Windows task on the VPS."""
    py = "python"
    script = str(Path(__file__).resolve())
    return (f'schtasks /Create /SC DAILY /TN "{task}" /ST {time_ct} /F /RL LIMITED '
            f'/TR "{py} {script} --config {config_path}"')


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default="config/live.yaml")
    ap.add_argument("--dry-run", action="store_true", help="list candidates, upload nothing")
    ap.add_argument("--register", action="store_true", help="print the Windows schtasks command")
    ap.add_argument("--time", default="17:30", help="daily run time (CT) for --register")
    a = ap.parse_args(argv)

    if a.register:
        print(register_command(a.config, a.time))
        return 0

    cfg = _cfg(Path(a.config))
    # dry-run reads nothing over the network and NEVER writes the manifest (so a later real run
    # still sends the files). Real run builds the b2sdk uploader from env creds.
    uploader = (lambda *_: None) if a.dry_run else make_b2_uploader()
    off = B2Offload(cfg["bucket"], uploader, prefix=cfg["prefix"])
    arch = SierraArchiver(cfg["data_dir"], off, cfg["manifest"],
                          root=cfg["root"], suffix=cfg["suffix"])
    if a.dry_run:
        keys = [k for k, _ in arch.pending()]
        print(f"would upload {len(keys)} file(s) to b2://{cfg['bucket']}/")
    else:
        keys = arch.archive()
        print(f"archived {len(keys)} file(s) to b2://{cfg['bucket']}/")
    for k in keys:
        print(f"  {k}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
