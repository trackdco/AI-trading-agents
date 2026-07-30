# Combined audit — Stage 2: FAILED

No verdict should be read from this stage.

```
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/user/AI-trading-agents/scripts/combined_book_audit.py", line 449, in <module>
    main()
    ~~~~^^
  File "/home/user/AI-trading-agents/scripts/combined_book_audit.py", line 445, in main
    {0: stage0, 1: stage1, 2: stage2, 3: stage3}[a.stage]()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/home/user/AI-trading-agents/scripts/combined_book_audit.py", line 338, in stage2
    E = _events(N, Lo, lon_ladder)
  File "/home/user/AI-trading-agents/scripts/combined_book_audit.py", line 283, in _events
    "risk": r._asdict()["risk_$"], "pnl": r.pnl_ladder})
            ~~~~~~~~~~~^^^^^^^^^^
KeyError: 'risk_$'
```
