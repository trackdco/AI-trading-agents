# watchdog.ps1 — process supervisor for the NY canon live loop (2026-08-03 audit).
#
# What this closes: ny_run.py had NOTHING keeping it running. A crash, a Windows update
# reboot, or (before the market-calendar fix) the guaranteed daily self-halt at the CME
# maintenance break all required a human to notice and manually retype the arm command.
# This script is meant to run on a short Task Scheduler cycle (every 1-2 minutes) so the
# OS itself is the thing that keeps THIS script alive across a reboot — this script's only
# job is to keep ny_run.py alive underneath it.
#
# THE ONE RULE THAT OVERRIDES EVERYTHING ELSE: if the KILL file exists, DO NOTHING. A
# human deliberately stopped the loop; a watchdog that "helpfully" restarts through a kill
# file turns the kill switch into a lie. Checked FIRST, every run, no exceptions.
#
# Crash-loop guard: if ny_run.py dies and gets relaunched more than $MaxRestartsPerHour
# times inside a rolling hour, the watchdog STOPS restarting and pages loudly instead —
# a process that can't stay up needs a human, not an infinite respawn loop quietly eating
# the arm attempts (each of which, if ARM REFUSED, exits near-instantly).
#
# SECURITY TRADEOFF, explicit, not buried: unattended restart needs to present the arming
# phrase without a human typing it, so ARM_TOKEN must be set as a PERSISTENT (User or
# Machine scope) environment variable on this box. That means anything with access to this
# Windows account can read it. This is a deliberate choice to make — set it only if you
# want restart-without-you; otherwise leave ARM_TOKEN unset and the watchdog will detect
# the stall, alert you, and wait for you to arm manually (safer, not fully autonomous).
#
# Setup (run once, as Administrator, from the repo root):
#   1. Persist the token (skip this step to keep manual-arm-only):
#        [Environment]::SetEnvironmentVariable("ARM_TOKEN", "<the phrase>", "Machine")
#      Restart the terminal after this — env vars set this way don't apply retroactively.
#   2. Persist Telegram creds the same way (or reuse .env — see below):
#        [Environment]::SetEnvironmentVariable("TELEGRAM_BOT_TOKEN", "<token>", "Machine")
#        [Environment]::SetEnvironmentVariable("TELEGRAM_CHAT_ID", "<chat id>", "Machine")
#   3. Register the scheduled task (every 2 minutes, runs whether logged in or not):
#        $action  = New-ScheduledTaskAction -Execute "powershell.exe" `
#                     -Argument "-NoProfile -ExecutionPolicy Bypass -File C:\Users\Administrator\AI-trading-agents\scripts\watchdog.ps1"
#        $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 2) -RepetitionDuration ([TimeSpan]::MaxValue)
#        Register-ScheduledTask -TaskName "NYCanonWatchdog" -Action $action -Trigger $trigger -RunLevel Highest
#   4. Verify: Get-ScheduledTask -TaskName "NYCanonWatchdog" | Get-ScheduledTaskInfo
#
# This script does NOT replace the burn-in cert (docs/RUNBOOK-burnin-r16.md) — it has not
# been exercised against a real crash on the real box yet. Treat it as untested until that
# runbook's watchdog-specific steps pass.

$ErrorActionPreference = "Stop"
$RepoDir      = "C:\Users\Administrator\AI-trading-agents"
$KillFile     = Join-Path $RepoDir "output\live\KILL"
$StateFile    = Join-Path $RepoDir "output\live\watchdog_state.json"
$LogFile      = Join-Path $RepoDir "output\live\watchdog.log"
$RunLogOut    = Join-Path $RepoDir "output\live\ny_run_stdout.log"
$MaxRestartsPerHour = 3

function Write-Log($msg) {
    $line = "$(Get-Date -Format o)  $msg"
    Add-Content -Path $LogFile -Value $line
    Write-Output $line
}

function Send-Telegram($text) {
    $tok  = $env:TELEGRAM_BOT_TOKEN
    $chat = $env:TELEGRAM_CHAT_ID
    if (-not $tok -or -not $chat) { return }   # not configured: log-only, silently skip
    try {
        $uri = "https://api.telegram.org/bot$tok/sendMessage"
        Invoke-RestMethod -Uri $uri -Method Post -Body @{ chat_id = $chat; text = $text } `
            -TimeoutSec 10 | Out-Null
    } catch {
        Write-Log "WARN Telegram send failed: $_"
    }
}

# ---- rule 1: a deliberate kill is absolute -----------------------------------------
if (Test-Path $KillFile) {
    Write-Log "KILL file present — standing down, not restarting"
    exit 0
}

# ---- is ny_run.py already alive? ---------------------------------------------------
$procs = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
         Where-Object { $_.CommandLine -match "scripts\.ny_run" -and $_.CommandLine -match "--arm" }
if ($procs) {
    exit 0     # running normally — nothing to do, stay quiet
}

# ---- not running: load restart history for the crash-loop guard --------------------
# -AsHashtable needs PowerShell 6+; the box runs Windows PowerShell 5.1 (built-in) — a
# plain ConvertFrom-Json (PSCustomObject) is the compatible form on both.
$restarts = @()
if (Test-Path $StateFile) {
    try {
        $loaded = Get-Content $StateFile -Raw | ConvertFrom-Json
        if ($loaded.restarts) { $restarts = @($loaded.restarts) }
    } catch {}
}
$cutoff = (Get-Date).AddHours(-1)
$recent = @($restarts | Where-Object { [datetime]$_ -gt $cutoff })

if ($recent.Count -ge $MaxRestartsPerHour) {
    # only alert on the FIRST detection of the trip, not every 2-minute cycle after
    $tripFile = Join-Path $RepoDir "output\live\watchdog_tripped"
    if (-not (Test-Path $tripFile)) {
        Write-Log "CRASH LOOP: $($recent.Count) restarts in the last hour — giving up, human needed"
        Send-Telegram "CRASH LOOP: ny_run has failed to stay up $($recent.Count)x in the last hour. Watchdog has STOPPED auto-restarting. Check output\live\watchdog.log and ny_run_stdout.log on the box."
        New-Item -ItemType File -Path $tripFile -Force | Out-Null
    }
    exit 1
}

if (-not $env:ARM_TOKEN) {
    Write-Log "ny_run not running and ARM_TOKEN is not set — manual-arm-only mode, alerting and waiting"
    Send-Telegram "ny_run is NOT running and no ARM_TOKEN is set for auto-restart. Log in and arm manually: python -m scripts.ny_run --arm"
    exit 0
}

# ---- restart -------------------------------------------------------------------------
Write-Log "ny_run not running — restarting (attempt in the last hour: $($recent.Count + 1)/$MaxRestartsPerHour)"
$recent += (Get-Date).ToString("o")
[PSCustomObject]@{ restarts = $recent } | ConvertTo-Json | Set-Content -Path $StateFile
Remove-Item -Path (Join-Path $RepoDir "output\live\watchdog_tripped") -ErrorAction SilentlyContinue

Push-Location $RepoDir
try {
    Start-Process -FilePath "python" -ArgumentList "-m scripts.ny_run --arm" `
        -WorkingDirectory $RepoDir -WindowStyle Hidden `
        -RedirectStandardOutput $RunLogOut -RedirectStandardError "$RunLogOut.err"
    Send-Telegram "WATCHDOG: ny_run was down — restart attempt $($recent.Count)/$MaxRestartsPerHour issued."
} finally {
    Pop-Location
}
