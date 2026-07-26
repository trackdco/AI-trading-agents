@echo off
rem Daily news-sentinel launcher (docs/STATUS-go-live-checklist.md; Angus item 7).
rem Scheduled on the VPS via:
rem   schtasks /Create /TN "NQDesk-NewsSentinel" /TR "C:\ai-trading-agents\scripts\run_news_sentinel.bat" /SC DAILY /ST 06:00 /F
rem 06:00 US Central = 07:00 ET, an hour before the NY pre window. If this fails to run,
rem the PremarketGuard fails CLOSED: no snapshot for the day -> no pre-09:30 entries.
cd /d C:\ai-trading-agents
if not exist output\live mkdir output\live
python -m scripts.news_daily_agent >> output\live\news_sentinel.log 2>&1
