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

**4a — Denali data (MBO) — can do NOW (comes with Package 12):**
14. Global Settings → **Data/Trade Service Settings** → select the **Denali Exchange Data Feed**.
15. Enable the **CME real-time data** (non-pro) — this is where the ~$16/mo exchange fee + the MBO
    depth live. Confirm you can see live NQ data + the market depth ladder.

**4b — Rithmic execution — DEFERRED until the Lucid account is funded:**
16. Once Lucid is funded (after parity passes): Global Settings → Data/Trade Service Settings →
    add a **Rithmic** *trade* connection → enter the **Lucid-provided Rithmic credentials + server/gateway**.
17. Sierra then runs **Denali for data, Rithmic for the trade route** (two connections at once).
18. **Verify 10-level DOM depth** shows on the Rithmic account (the wall checks need the full ladder).

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
| 4a Denali data (MBO) | Pat | no |
| 4b Rithmic execution | Pat | **yes** (after funding) |
| 5 DTC server | Pat | no |
| 6 Python + engine + gates | Pat | no |

Everything except 4b can be done today. 4b is the last connect, once the account's funded and
parity's passed.
