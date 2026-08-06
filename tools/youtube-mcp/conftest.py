"""Keep the MCP server's tests out of the engine's test run.

`pytest` from the repo root collects everything, but the engine venv has no
`mcp` or `youtube-transcript-api` — those are deliberately not on the approved
dependency list in requirements.txt. Without this guard the engine suite would
fail on a collection error for a component it has nothing to do with.

Run these with the server's own venv:

    tools/youtube-mcp/.venv/bin/python -m pytest tools/youtube-mcp/test_server.py -q
"""

collect_ignore = []

try:
    import mcp  # noqa: F401
except ImportError:  # engine venv — skip silently, this isn't its suite
    collect_ignore = ["test_server.py"]
