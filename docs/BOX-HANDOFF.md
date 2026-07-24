# BOX-HANDOFF — pin & verify the Route-B file-tail data path on the VPS

**For whoever is at the Windows VPS (Pat/Angus).** The Route-B data path (read Sierra's own
on-disk `.scid`/`.depth` files instead of taking data over DTC, which the CME non-pro licence
blocks) is built and green offline (431 tests). This is the **on-box gate that cannot be
closed from a Mac**: confirm the byte layouts the parser assumes match *this* Sierra build,
then replay a captured day through the real pipeline.

Everything below is copy-paste. **The engine places nothing** — this is data-ingest only.
It needs **no funded account and no Lucid login**: it works on data Sierra already has, so it
can run the moment Sierra is streaming (or on stored history). See `docs/VPS-SETUP.md` Parts
3–5 for getting Sierra up first.

> Paths below assume the repo is cloned at `C:\ai-trading-agents` and Sierra's data lives at
> `C:\SierraChart\Data`. Adjust if yours differ. Commands are **PowerShell** on Windows
> Server 2022; the two `python scripts\...` calls are identical on Mac/Linux (swap `\`→`/`).

---

## Step A — Dump a real NQU6 `.scid` + `.depth` sample

Sierra writes these continuously while connected; you do not "export" anything — you just
locate the files it already maintains.

1. In Sierra, open the **NQU26** (front-month E-mini NQ) chart so Sierra is writing its
   intraday file. For depth, market-depth storage must be ON:
   **Global Settings → Data/Trade Service Settings → check "Store Market Depth Data"**
   (and the chart's DOM must be populating — see the depth caveat in
   `docs/FOR-ANGUS-golive-questions.md`).

2. Find the two files (PowerShell):

   ```powershell
   cd C:\SierraChart\Data
   # intraday bars/ticks — the front-month NQ contract file:
   Get-ChildItem -Filter "NQU26*.scid" | Select-Object Name,Length,LastWriteTime
   # market depth — stored under MarketDepthData\, one file per day:
   Get-ChildItem MarketDepthData\ -Filter "NQU26*.depth" | Select-Object Name,Length,LastWriteTime
   ```

   Note the exact filenames (the `.depth` name usually carries the date, e.g.
   `NQU26-CME.2026-07-27.depth`). These are the two inputs for Steps B and C. You do **not**
   need to copy them anywhere — read them in place.

---

## Step B — Verify / pin the byte-layout constants against this Sierra build

`scripts\sierra_pin_check.py` opens a real file and asserts the header magic, HeaderSize,
RecordSize, and — for `.depth` — that **every Command byte decodes to a known action**,
against the constants pinned at the top of `src/canon/sierra_files.py`. It prints the header
and sample records so you can eyeball prices/sizes/times against Sierra's chart + DOM.

```powershell
cd C:\ai-trading-agents

# 1) the intraday file
python scripts\sierra_pin_check.py "C:\SierraChart\Data\NQU26-CME.scid"

# 2) the depth file (use the actual name from Step A)
python scripts\sierra_pin_check.py "C:\SierraChart\Data\MarketDepthData\NQU26-CME.2026-07-27.depth"
```

**PASS** (exit 0) → the layout matches; eyeball the sample rows against Sierra and move to
Step C.

**FAIL** (exit 1, "layout/enum mismatch") → the message names the exact constant to adjust in
`src/canon/sierra_files.py`, all isolated at the top of the file under the `PIN-ON-BOX`
banner:

- Header/record **size** mismatch → fix `SCID_HEADER_SIZE`/`SCID_REC_SIZE` (and the
  `SCID_HEADER`/`SCID_REC` `struct` format strings) or the `DEPTH_*` equivalents.
- **`.depth` unknown Command N** → the Command enum differs on this build (the least-
  documented part of the format). Fix the `DCMD_CLEAR/SET_BID/SET_ASK/DEL_BID/DEL_ASK`
  values and the `_DCMD_ACTION` map. If side turns out to live in the `Flags` byte rather
  than folded into Command, adjust `DepthReader._decode` (it already receives `flags`).

  To see the raw bytes while pinning:

  ```powershell
  python -c "import struct; f=open(r'C:\SierraChart\Data\MarketDepthData\NQU26-CME.2026-07-27.depth','rb'); h=f.read(64); print('hdr',struct.unpack('<4sIIHH48s',h)[:4]); [print(struct.unpack('<qBBHfII',f.read(24))) for _ in range(8)]"
  ```

  Re-run the pin check after each edit until it PASSES. This is a one-time pin per Sierra
  build.

---

## Step C — Replay the captured day through the real pipeline

`scripts\sierra_parity_replay.py` drives the real files through `SierraFileFeed →
CanonIngestor(book=DepthBook())` — the exact live wiring — and reports that real Sierra bytes
reconstruct sane bars, a populated MBP-10 book, and canon feature rows.

### C.1 Sanity replay (any captured day, incl. a fresh live day)

```powershell
python scripts\sierra_parity_replay.py `
  "C:\SierraChart\Data\NQU26-CME.scid" `
  "C:\SierraChart\Data\MarketDepthData\NQU26-CME.2026-07-27.depth"
```

Confirm the output shows: bars reconstructed with a sensible ts span; **best bid < best ask**
with a realistic spread; **10 bid / 10 ask** levels (a thin/empty book means CME depth isn't
subscribed yet — expected pre-funding, see the go-live questions doc); and a feature_row
carrying the `tape/CVD`, `VWAP`, and `depth` families with finite values.

### C.2 True feed-parity (arch §2.1) — needs an OVERLAPPING historical day

A fresh live day has no backtest reference to compare against. To get a real parity number,
capture a day that Sierra **still has stored** AND that exists in the repo's reference archive
`data\reference\depth_2026\` (run `Get-ChildItem data\reference\depth_2026\` to list them —
e.g. `2026-02-10`). Point Sierra at that stored `.depth` and:

```powershell
python scripts\sierra_parity_replay.py `
  "C:\SierraChart\Data\NQU26-CME.scid" `
  "C:\SierraChart\Data\MarketDepthData\NQU26-CME.2026-02-10.depth" `
  --parity --day 2026-02-10
```

This reconstructs the book per reference-snapshot minute from `.depth` and diffs
`(side, price, size)` against the frozen MBP-10 the backtest scored on. **Target: every
snapshot-minute matches** (`150/150 snapshot-minutes match`). Any mismatch prints example
minutes with got-vs-want — investigate before trusting the feed (usually a residual layout/
aggregation nuance from Step B, or a tz/rounding edge).

> Delta-sign note: the aggressor delta (`ask−bid`) is flagged `PIN-ON-BOX` in
> `MinuteAggregator` because the repo documents that a naive CVD is the *negative* of ours
> (`docs/FINDING-cvd-confirm-vs-fade-signcheck.md`). If a tape/CVD feature comes out sign-
> flipped vs the backtest on the overlapping day, flip it there and re-run.

---

## What this gates

Green Steps B + C = the live **data** path reproduces the backtest on real Sierra bytes.
Combined with the offline suite (`python -m pytest -q` → 431 passed) and the **DTC order
path** (already built, `src/desk/dtc_client.py`), the only remaining go-live blockers are the
two rulings in `docs/FOR-ANGUS-golive-questions.md` and the funded-account data subscription
(`docs/VPS-SETUP.md` Part 4c). The `StartupParityGate` (`src/canon/infra.py`) keeps the desk
read-only until a human clears this green.
