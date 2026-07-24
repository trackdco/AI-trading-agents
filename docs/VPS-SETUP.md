# VPS Setup — step by step (ChartVPS Alpha Mark-2)

Do these in order on the live VPS. Angus owns Parts 1–2 (get in, make it 24/5); Pat/Brake
owns Parts 3–6 (Sierra + engine). Share the RDP login so both can connect.

**What needs the Lucid account (not funded until parity passes):** only the **Rithmic
execution connection** (Part 4b). Everything else — Sierra install, Package 12 + Denali data,
DTC, Python, repos — can be done **now**.

---

## Part 1 — Get into the VPS from your Mac (RDP)

1. From the ChartVPS email/portal, grab the **IP address**, **username**, **password**.
2. On the Mac, install **Microsoft Remote Desktop** (free — Mac App Store).
3. Open it → **Add PC** (+). PC name = the **IP**. User account = **Add** → the username + password.
4. Double-click the PC → accept the certificate warning → you're on the **Windows Server 2022 desktop**.
5. **Share access with Pat:** give him the same IP/user/pass. Windows Server allows 2 admin RDP
   sessions, so you can both be on (or take turns).

---

## Part 2 — Make it 24/5-ready (Windows hygiene)

6. **Power:** Control Panel → Power Options → **High performance** → set "Turn off display" and
   "Put computer to sleep" to **Never**.
7. **Auto-login** (so it comes back after a reboot without a human): press Win+R → `netplwiz` →
   uncheck "Users must enter a user name and password" → enter the password. (Or leave on if you
   prefer to log in manually.)
8. **Screensaver off**, **Windows Update:** Settings → set **Active hours** wide and defer
   auto-restarts so it never reboots mid-session.
9. **THE KEY 24/5 HABIT:** when you're done, **DISCONNECT** (just close the RDP window / click X) —
   do **NOT** "Sign out / Log off." Disconnecting keeps the session alive and Sierra + the engine
   keep running. Logging off **closes everything.** This is the #1 gotcha.

---

## Part 3 — Install Sierra Chart (Pat) — do this ON the VPS

10. Open a browser **on the VPS** → `sierrachart.com` → **Download** → run the Windows installer
    (default install folder is fine). Download it *on the VPS*, not the Mac.
11. **Create a Sierra Chart account** at sierrachart.com/Register (username + password) — this is
    separate from the VPS and from Lucid.
12. **Buy Service Package 12 — Integrated Advanced MBO** in the Sierra account management
    (Account → Manage Services). It activates on your account. (Or start the trial, then subscribe.)
13. Launch Sierra Chart → log in with the Sierra account → it pulls down Package 12.

---

## Part 4 — Data + execution connections

> **How Sierra combines the two feeds (verified 24-Jul on the live VPS).** You do **not**
> select a separate "Denali" service. You keep **Rithmic Direct - DTC** as the selected service
> (it carries the trade route) and **blank its Market Data + Historical Data username/password**
> fields. With no data creds on the trading service, Sierra automatically falls back to the
> **Denali (SC Data)** feed for market data + depth. Rithmic's own log confirms why this is
> mandatory: `MarketDepthIsSupported: 0` — Lucid's Rithmic carries **no depth at all**, so the
> ladder *must* come from Denali.

**4a — Rithmic execution connection — the trade route:**
14. Global Settings → **Data/Trade Service Settings** → **Current Selected Service** = **Rithmic
    Direct - DTC** → enter the **Lucid-provided Rithmic Trading Username/Password + server**. This
    connects for *order routing*. (Data via Rithmic is the wrong path — no depth — so we turn it
    off in 4b.)

**4b — Point data at Denali (blank Rithmic's data creds):**
15. Same window → **clear** these four fields, leave the two Trading fields filled:
    Market Data Username, Market Data Password, Historical Data Username, Historical Data Password.
16. OK → **File → Disconnect → Connect to Data Feed.** Sierra now uses **Denali for data,
    Rithmic for the trade route.**

**4c — CME real-time + depth data — DEFERRED until the Lucid account is FUNDED:**
17. The Denali feed needs a **CME real-time exchange subscription** to actually stream. The
    affordable **non-professional** rate (~**$40.50/mo** for CME Group *with market depth* — depth
    is the pricey part, not the ~$16 top-of-book figure) **requires a verified live funded futures
    account** that Sierra connects to at least once a month. Until Lucid is funded you'd be forced
    onto pro rates for something not needed pre-go-live.
18. **So don't buy data yet.** Everything before go-live (the parity gate) runs on committed
    historical data — no live feed. Sequence: pass parity → fund Lucid → connect the funded account
    → subscribe to CME real-time+depth at non-pro → live L1 + **full MBP-10 + MBO depth** floods in.
19. At that point **verify the 10-level DOM depth** populates (the wall checks need the full ladder).
    Until then, a blank DOM + `B: 0.00 A: 0.00` is the **expected** state — the wiring is proven,
    the data tap is just deliberately off.

---

## Part 5 — Turn on the DTC server (so the engine can read Sierra)

19. Global Settings → **Sierra Chart Server Settings** (a.k.a. DTC Server) → enable the **DTC Protocol
    Server** → note the port (default **11099**), bind to `127.0.0.1` (localhost only — nothing public).
20. This is the local port the Python ingestor connects to for raw trades + depth, and routes orders through.

---

## Part 6 — Python + the engine (Pat)

21. Install **Python 3.11+** and **git** on the VPS.
22. `git clone` **Pat's Hermes/agents repo** and **this repo** onto the VPS.
23. Point the ingestor at Sierra's DTC port (`127.0.0.1:11099`). Bring up the event server
    (`DESK-EVENTS.md`) and the dashboard.
24. Run the **reconciliation day** (features from the live/replayed feed must match the backtest to
    the decimal) and keep the **parity gate** green. Arming key stays out until all gates pass.

---

## Quick split of who does what

| Part | Owner | Needs Lucid? |
|---|---|---|
| 1–2 Get in + 24/5 hygiene | Angus | no |
| 3 Install Sierra + Package 12 | Pat | no |
| 4a Rithmic execution connection | Pat | **yes** (funded, after parity) |
| 4b Point data at Denali (blank Rithmic data creds) | Pat | no |
| 4c CME real-time+depth data (~$40.50/mo non-pro) | Pat | **yes** (needs funded acct to qualify) |
| 5 DTC server | Pat | no |
| 6 Python + engine + gates | Pat | no |

**Net:** the whole data/trade *wiring* (Parts 3, 4b, 5, 6) can be built and proven now on Sim.
The two money/live pieces — the Rithmic execution login (4a) and the CME depth subscription (4c) —
both wait on a **funded** Lucid account, which waits on **parity passing**. Validate first, buy second.

Everything except 4b can be done today. 4b is the last connect, once the account's funded and
parity's passed.
