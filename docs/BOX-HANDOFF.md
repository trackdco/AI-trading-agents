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
   intraday file. Depth recording is a **PER-SYMBOL** setting, not a global one
   (confirmed on the box, SC build 2930, 2026-07-24):

   **Global Settings → Symbol Settings →** select the symbol pattern **`NQ?#.CME`**
   (service code `rithmic.trading`) **→ set "Record Market Depth Data" = Yes.**

   > This corrects the earlier instruction, which pointed at *Data/Trade Service
   > Settings → "Store Market Depth Data"* — that is the WRONG dialog and would leave
   > depth unrecorded. The switch lives on the **symbol pattern**, so it must be set on
   > the `NQ?#.CME` pattern that the front-month NQU26 resolves through.

   On the same symbol pattern, set **"Number of Depth Levels to Subscribe" = 10**.
   Note: **`0` does NOT mean "unlimited"** — it means *defer to the global default*.
   Pin it to `10` explicitly so this symbol always subscribes the full MBP-10 ladder
   our depth checks (`WALLSZ`, `dep_wall_*`) need. (The chart's DOM must also be
   populating — see the depth caveat in `docs/FOR-ANGUS-golive-questions.md`.)

   Two more box findings that affect the capture (no action needed beyond noting them):
   - **Intraday Data Storage Time Unit** was already **`1 Tick`** on this install — the
     `.scid` is tick-resolution as the parser assumes; **no re-download needed**.
   - The connected server is **`LucidTrading-Chicago Area-Aggregated`**. *Aggregated* =
     **MBP-10** (level-aggregated depth), confirming the feed spec from the box itself:
     the `.depth` ladder is MBP-10, the exact view the canon was validated on.

   **Flush latency (affects the reconciliation-day lag measurement):** the
   **"Intraday File Flush Time in Milliseconds"** setting lives at **Global Settings →
   Advanced Service Settings → General**. A value of **`0` is the Sierra default = ~5 s
   flush**; it was set to **`1000`** (1 s) on the box to tighten the file-append latency
   floor the file-tail path reads through. Route B measures this observed lag per bar
   (Step C) rather than assuming it away — see `docs/LIVE-STACK.md` for the configured
   value the reconciliation gate reports against.

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

> **Build note (from the box):** this install is **SC build 2930**. Sierra switched the
> intraday `SCDateTime` field from `double` to `int64` at build **2151**, so 2930 > 2151
> ⇒ times are **int64 microseconds** — exactly the `<q` (int64) the pinned `SCID_REC` /
> `DEPTH_REC` formats assume. The header/record sizes the box session read (`.scid` header
> 56 / `.depth` header 64 / record 24) all match the pinned constants, so the pin check is
> *expected* to PASS on this build — but it still MUST be run against a real file; the spec
> matching is not proof the bytes do.
>
> The check now ALSO enforces two order-flow guarantees beyond layout (see the two loud
> assertions it prints on FAIL): `.scid` Bid/Ask volumes must be non-zero across the sample
> (or CVD and the whole order-flow family are blind), and `.depth` must yield **10** ladder
> levels per side, not 5 (5 ⇒ Denali depth not fully subscribed).

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

## Step B.2 — Measure Sierra's disk-flush cadence (Angus, 2026-07-26)

**Why:** the whole Route-B data path assumes Sierra commits `.scid`/`.depth` writes to disk
promptly. Our tail polls every 1s; the canon decides on CLOSED 1-min bars, so we have a ~60s
budget. If Sierra buffers for a few seconds that is fine; if it buffers for tens of seconds the
bot would be scoring a stale tape. **Measured, not assumed.**

During a LIVE session (Sierra connected and streaming), run this and watch the cadence:

```powershell
$f = "C:\SierraChart\Data\NQU26-CME.scid"
1..30 | ForEach-Object {
  $i = Get-Item $f
  "{0:HH:mm:ss.fff}  size={1}  modified={2:HH:mm:ss.fff}" -f (Get-Date), $i.Length, $i.LastWriteTime
  Start-Sleep -Milliseconds 500
}
```

**Record:** how often `size` actually increases. Report the typical gap.
- **< 2s** — ideal, no action.
- **2–10s** — fine against a 60s bar; note it and move on.
- **> 15s** — flag it, do not arm. We would need to shorten Sierra's flush interval
  (Global Settings → Data/Trade Service Settings) or reconsider the poll design.

Repeat for the `.depth` file.

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
