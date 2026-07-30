# Combined audit — Stage 1: FAILED

No verdict should be read from this stage.

```
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/user/AI-trading-agents/scripts/combined_book_audit.py", line 443, in <module>
    main()
    ~~~~^^
  File "/home/user/AI-trading-agents/scripts/combined_book_audit.py", line 439, in main
    {0: stage0, 1: stage1, 2: stage2, 3: stage3}[a.stage]()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/home/user/AI-trading-agents/scripts/combined_book_audit.py", line 228, in stage1
    f"{j.ny.corr(j.lon, method='spearman'):+.3f} |\n"
       ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/user/AI-trading-agents/.venv/lib/python3.13/site-packages/pandas/core/series.py", line 2774, in corr
    result = nanops.nancorr(
        this_values, other_values, method=method, min_periods=min_periods
    )
  File "/home/user/AI-trading-agents/.venv/lib/python3.13/site-packages/pandas/core/nanops.py", line 87, in _f
    return f(*args, **kwargs)
  File "/home/user/AI-trading-agents/.venv/lib/python3.13/site-packages/pandas/core/nanops.py", line 1655, in nancorr
    f = get_corr_func(method)
  File "/home/user/AI-trading-agents/.venv/lib/python3.13/site-packages/pandas/core/nanops.py", line 1670, in get_corr_func
    from scipy.stats import spearmanr
ModuleNotFoundError: No module named 'scipy'
```
