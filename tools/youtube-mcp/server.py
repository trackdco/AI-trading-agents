"""YouTube research MCP server — transcript sourcing for the research lane.

Why this exists: the research sweeps in `research/articles/` are WebSearch
extracts, because direct page fetches are 403-blocked at egress
(`research/findings/london-session-clock.md`). That leaves URLs as leads
rather than sources. This server closes that gap for video sources — it pulls
the actual transcript, timestamps every line, and writes it to disk so a thesis
can quote what a trader said rather than what a search snippet summarised.

It feeds `research/README.md`'s stage 1 (broad sweep → theses in `candidates/`)
and stage 2 (deep-dive on greenlight). Nothing here authorizes anything:
transcripts are sources, and the standing law that every cited number has a file
in `research/articles/` is exactly what the caching is for.

Design notes (deliberate, not accidental):

1. Sweeps NEVER return transcript text. A 60-minute trading video is ~60k
   characters; twelve of them would bury a context window before any analysis
   happens. Sweeps return a ranked index + cache paths; you grep, then read the
   two that matter.
2. Everything fetched is written to disk under `research/youtube/` and
   committed. A transcript that only ever existed in a context window is not a
   source and cannot be re-checked.
3. Search needs a YouTube Data API v3 key; transcript fetching does not. The
   server is useful with no key at all — search tools then return a clear error
   rather than failing obscurely.

Env vars:
  YOUTUBE_API_KEY            Data API v3 key. Required only for search/details.
  YOUTUBE_MCP_CACHE_DIR      Cache root. Default: <repo>/research/youtube
  YOUTUBE_TRANSCRIPT_PROXY   Optional http(s) proxy for transcript fetches.
                             YouTube blocks datacenter IPs — needed if this runs
                             anywhere other than a workstation.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from mcp.server import MCPServer
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig

API_ROOT = "https://www.googleapis.com/youtube/v3"
REPO_ROOT = Path(__file__).resolve().parents[2]

# Controlled tag vocabulary — docs/VAULT-SCHEMA.md §5. Improvised values are a
# lint failure there, so the article writer validates against these rather than
# letting a sweep invent a tag.
SESSION_TAGS = ("ny-pre", "ny-gold", "london", "asia")
MECHANISM_TAGS = (
    "depth-walls",
    "overnight-structure",
    "order-flow",
    "vwap",
    "trigger-density",
    "structural-events",
    "pattern-taxonomy",
    "exit-mechanics",
    "sizing",
    "calendar",
    "volume",
    "reversal",
)


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader. Claude Code passes the launching shell's environment,
    which usually does not include the repo's .env — so read it ourselves rather
    than making the user export keys by hand."""
    if not path.exists():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'\"")
        # Fill in blanks as well as absences: .mcp.json passes "${VAR:-}", which
        # sets the variable to an empty string when it is unset in the shell.
        # Treating that as "already set" would silently ignore the .env file.
        if key and not os.environ.get(key):
            os.environ[key] = value


_load_dotenv(REPO_ROOT / ".env")

_cache_env = os.environ.get("YOUTUBE_MCP_CACHE_DIR", "").strip()
CACHE_DIR = (
    Path(_cache_env)
    if Path(_cache_env).is_absolute()
    else REPO_ROOT / (_cache_env or "research/youtube")
)

server = MCPServer(
    name="youtube-research",
    version="1.0.0",
    instructions=(
        "Video sourcing for the research lane. Typical flow: "
        "youtube_research_sweep(query) to pull and cache a corpus, "
        "youtube_grep_transcripts(pattern) to find where rules are actually "
        "stated, youtube_get_transcript(video, full=True) on the two or three "
        "that matter, then youtube_article_record() to write the "
        "research/articles/ file. Never pull twelve full transcripts into "
        "context — that is what the grep is for."
    ),
)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

_ID_PATTERNS = [
    re.compile(r"(?:v=|/v/|youtu\.be/|/embed/|/shorts/|/live/)([A-Za-z0-9_-]{11})"),
    re.compile(r"^([A-Za-z0-9_-]{11})$"),
]


def extract_video_id(value: str) -> str:
    """Accept a bare ID, a watch URL, youtu.be, /shorts/, /embed/, or /live/."""
    value = value.strip()
    for pattern in _ID_PATTERNS:
        match = pattern.search(value)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract an 11-character YouTube video ID from {value!r}")


def _api_key() -> str:
    key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "YOUTUBE_API_KEY is not set, so YouTube search/metadata is unavailable. "
            "Transcript tools still work if you supply video IDs or URLs directly. "
            "Get a key at https://console.cloud.google.com/apis/library/youtube.googleapis.com "
            "and put YOUTUBE_API_KEY=... in your .env."
        )
    return key


def _get(path: str, params: dict[str, Any]) -> dict[str, Any]:
    params = {k: v for k, v in params.items() if v is not None}
    params["key"] = _api_key()
    with httpx.Client(timeout=30.0) as client:
        response = client.get(f"{API_ROOT}/{path}", params=params)
    if response.status_code == 403:
        raise RuntimeError(
            "YouTube API returned 403. Usual causes: daily quota exhausted "
            "(search costs 100 units of the 10,000/day free allowance, so ~100 "
            "searches/day), or the API is not enabled on the key's project. "
            f"Body: {response.text[:400]}"
        )
    response.raise_for_status()
    return response.json()


def _slugify(text: str, limit: int = 60) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:limit] or "untitled"


def _iso_duration_to_seconds(value: str) -> int:
    match = re.fullmatch(r"P(?:(\d+)D)?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", value or "")
    if not match:
        return 0
    days, hours, minutes, seconds = (int(g or 0) for g in match.groups())
    return ((days * 24 + hours) * 60 + minutes) * 60 + seconds


def _hms(seconds: int) -> str:
    hours, rem = divmod(int(seconds), 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


def _transcript_api() -> YouTubeTranscriptApi:
    proxy = os.environ.get("YOUTUBE_TRANSCRIPT_PROXY", "").strip()
    if proxy:
        return YouTubeTranscriptApi(
            proxy_config=GenericProxyConfig(http_url=proxy, https_url=proxy)
        )
    return YouTubeTranscriptApi()


@dataclass
class CachedTranscript:
    video_id: str
    path: Path
    text: str
    language: str
    segments: int
    cached_at: str
    from_cache: bool


def _cache_paths(video_id: str) -> tuple[Path, Path]:
    base = CACHE_DIR / "transcripts"
    return base / f"{video_id}.txt", base / f"{video_id}.json"


def _fetch_transcript(video_id: str, languages: list[str], refresh: bool) -> CachedTranscript:
    text_path, meta_path = _cache_paths(video_id)
    if not refresh and text_path.exists() and meta_path.exists():
        meta = json.loads(meta_path.read_text())
        return CachedTranscript(
            video_id=video_id,
            path=text_path,
            text=text_path.read_text(),
            language=meta.get("language", "unknown"),
            segments=meta.get("segments", 0),
            cached_at=meta.get("cached_at", "unknown"),
            from_cache=True,
        )

    fetched = _transcript_api().fetch(video_id, languages=languages)
    lines: list[str] = []
    for snippet in fetched:
        stamp = _hms(snippet.start)
        lines.append(f"[{stamp}] {snippet.text.strip()}")
    text = "\n".join(lines)

    text_path.parent.mkdir(parents=True, exist_ok=True)
    text_path.write_text(text)
    cached_at = datetime.now(UTC).isoformat(timespec="seconds")
    meta = {
        "video_id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "language": getattr(fetched, "language_code", languages[0]),
        "segments": len(lines),
        "characters": len(text),
        "cached_at": cached_at,
    }
    meta_path.write_text(json.dumps(meta, indent=2))
    return CachedTranscript(
        video_id=video_id,
        path=text_path,
        text=text,
        language=meta["language"],
        segments=len(lines),
        cached_at=cached_at,
        from_cache=False,
    )


def _rel(path: Path) -> str:
    """Repo-relative where possible — paths quoted into research/ files must be
    stable regardless of the working directory the server was launched from."""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


# Words that appear where a speaker states a rule rather than tells a story.
# Used to rank which transcripts are worth spending context on.
RULE_KEYWORDS = [
    "entry", "enter", "stop loss", "stop-loss", "take profit", "target",
    "risk", "reward", "backtest", "win rate", "session", "timeframe",
    "confirmation", "invalidat", "filter", "rule", "setup", "trigger",
]


def _rule_density(text: str) -> int:
    lowered = text.lower()
    return sum(lowered.count(word) for word in RULE_KEYWORDS)


# --------------------------------------------------------------------------
# tools
# --------------------------------------------------------------------------


@server.tool(
    description=(
        "Search YouTube for videos. Requires YOUTUBE_API_KEY. Returns titles, "
        "channels, dates and IDs — no transcripts. Costs 100 API quota units."
    )
)
def youtube_search(
    query: str,
    max_results: int = 15,
    published_after: str | None = None,
    published_before: str | None = None,
    channel_id: str | None = None,
    order: str = "relevance",
    min_duration_minutes: int | None = None,
) -> dict:
    """Search YouTube.

    Args:
        query: Search terms, e.g. "NQ opening range breakout order flow".
        max_results: 1-50.
        published_after: RFC3339 date, e.g. "2024-01-01T00:00:00Z".
        published_before: RFC3339 date.
        channel_id: Restrict to one channel (use youtube_find_channel first).
        order: relevance | date | viewCount | rating.
        min_duration_minutes: Drop results shorter than this. Strategy
            explanations under ~8 minutes are usually hype, not rules.
    """
    payload = _get(
        "search",
        {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": max(1, min(50, max_results)),
            "order": order,
            "publishedAfter": published_after,
            "publishedBefore": published_before,
            "channelId": channel_id,
        },
    )
    items = payload.get("items", [])
    ids = [item["id"]["videoId"] for item in items if item.get("id", {}).get("videoId")]
    details = _video_details_raw(ids) if ids else {}

    results = []
    for item in items:
        video_id = item.get("id", {}).get("videoId")
        if not video_id:
            continue
        snippet = item["snippet"]
        detail = details.get(video_id, {})
        duration = detail.get("duration_seconds", 0)
        if min_duration_minutes and duration < min_duration_minutes * 60:
            continue
        results.append(
            {
                "video_id": video_id,
                "title": snippet["title"],
                "channel": snippet["channelTitle"],
                "channel_id": snippet["channelId"],
                "published_at": snippet["publishedAt"],
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "duration": _hms(duration) if duration else None,
                "views": detail.get("views"),
                "description": snippet.get("description", "")[:300],
            }
        )
    return {"query": query, "count": len(results), "results": results}


def _video_details_raw(video_ids: list[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for start in range(0, len(video_ids), 50):
        chunk = video_ids[start : start + 50]
        payload = _get(
            "videos",
            {"part": "snippet,contentDetails,statistics", "id": ",".join(chunk)},
        )
        for item in payload.get("items", []):
            stats = item.get("statistics", {})
            out[item["id"]] = {
                "title": item["snippet"]["title"],
                "channel": item["snippet"]["channelTitle"],
                "channel_id": item["snippet"]["channelId"],
                "published_at": item["snippet"]["publishedAt"],
                "description": item["snippet"].get("description", ""),
                "tags": item["snippet"].get("tags", []),
                "duration_seconds": _iso_duration_to_seconds(
                    item.get("contentDetails", {}).get("duration", "")
                ),
                "views": int(stats.get("viewCount", 0) or 0),
                "likes": int(stats.get("likeCount", 0) or 0),
                "comments": int(stats.get("commentCount", 0) or 0),
            }
    return out


@server.tool(
    description=(
        "Full metadata for one or more videos: duration, views, likes, full "
        "description, tags. Use for credibility triage before spending "
        "transcript budget. Requires YOUTUBE_API_KEY."
    )
)
def youtube_video_details(videos: list[str]) -> dict:
    """Args: videos — list of video IDs or URLs."""
    ids = [extract_video_id(v) for v in videos]
    details = _video_details_raw(ids)
    for video_id, detail in details.items():
        detail["url"] = f"https://www.youtube.com/watch?v={video_id}"
        detail["duration"] = _hms(detail["duration_seconds"])
    return {"count": len(details), "videos": details}


@server.tool(
    description=(
        "Find channels by name so you can restrict searches to a trader you "
        "already trust. Requires YOUTUBE_API_KEY."
    )
)
def youtube_find_channel(query: str, max_results: int = 5) -> dict:
    payload = _get(
        "search",
        {
            "part": "snippet",
            "q": query,
            "type": "channel",
            "maxResults": max(1, min(25, max_results)),
        },
    )
    channels = [
        {
            "channel_id": item["snippet"]["channelId"],
            "title": item["snippet"]["channelTitle"],
            "description": item["snippet"].get("description", "")[:300],
            "url": f"https://www.youtube.com/channel/{item['snippet']['channelId']}",
        }
        for item in payload.get("items", [])
    ]
    return {"query": query, "count": len(channels), "channels": channels}


@server.tool(
    description=(
        "Fetch (and cache) one transcript. Returns an excerpt plus the cache "
        "path by default; pass full=True only when you actually intend to read "
        "the whole thing into context."
    )
)
def youtube_get_transcript(
    video: str,
    languages: list[str] | None = None,
    full: bool = False,
    excerpt_chars: int = 1500,
    refresh: bool = False,
) -> dict:
    """Args:
        video: Video ID or any YouTube URL form.
        languages: Preferred transcript languages, default ["en"].
        full: Return the entire transcript text inline.
        excerpt_chars: Size of the excerpt when full=False.
        refresh: Re-fetch even if a cached copy exists.
    """
    video_id = extract_video_id(video)
    cached = _fetch_transcript(video_id, languages or ["en"], refresh)
    result = {
        "video_id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "language": cached.language,
        "segments": cached.segments,
        "characters": len(cached.text),
        "estimated_tokens": len(cached.text) // 4,
        "rule_keyword_hits": _rule_density(cached.text),
        "cache_path": _rel(cached.path),
        "from_cache": cached.from_cache,
    }
    if full:
        result["transcript"] = cached.text
    else:
        result["excerpt"] = cached.text[:excerpt_chars]
        result["note"] = (
            "Excerpt only. Read the cache_path file, or use "
            "youtube_grep_transcripts, instead of pulling the full text."
        )
    return result


@server.tool(
    description=(
        "Which transcript languages exist for a video, and whether they are "
        "auto-generated. Diagnostic for when a fetch fails."
    )
)
def youtube_list_transcript_languages(video: str) -> dict:
    video_id = extract_video_id(video)
    listing = _transcript_api().list(video_id)
    tracks = [
        {
            "language": track.language,
            "language_code": track.language_code,
            "auto_generated": track.is_generated,
            "translatable": track.is_translatable,
        }
        for track in listing
    ]
    return {"video_id": video_id, "count": len(tracks), "tracks": tracks}


@server.tool(
    description=(
        "THE MAIN RESEARCH TOOL. Search YouTube for a mechanism, fetch and cache "
        "every transcript, and return a ranked index (no full text). Rank by "
        "rule_keyword_hits to decide which two or three are worth reading."
    )
)
def youtube_research_sweep(
    query: str,
    max_videos: int = 12,
    published_after: str | None = None,
    min_duration_minutes: int = 6,
    order: str = "relevance",
    languages: list[str] | None = None,
    label: str | None = None,
) -> dict:
    """Args:
        query: What the mechanism is called, plus qualifiers.
        max_videos: How many search hits to attempt transcripts for.
        published_after: RFC3339 cutoff.
        min_duration_minutes: Skip shorts and teasers.
        order: relevance | date | viewCount.
        languages: Preferred transcript languages.
        label: Name for the sweep manifest. Defaults to a query slug.
    """
    search = youtube_search(
        query=query,
        max_results=min(50, max_videos * 2),
        published_after=published_after,
        order=order,
        min_duration_minutes=min_duration_minutes,
    )
    candidates = search["results"][:max_videos]

    index, failures = [], []
    for candidate in candidates:
        try:
            cached = _fetch_transcript(candidate["video_id"], languages or ["en"], False)
        except Exception as exc:  # noqa: BLE001 - one bad video must not kill the sweep
            failures.append(
                {
                    "video_id": candidate["video_id"],
                    "title": candidate["title"],
                    "url": candidate["url"],
                    "reason": f"{type(exc).__name__}: {str(exc)[:200]}",
                }
            )
            continue
        index.append(
            {
                **candidate,
                "characters": len(cached.text),
                "estimated_tokens": len(cached.text) // 4,
                "rule_keyword_hits": _rule_density(cached.text),
                "cache_path": _rel(cached.path),
                "opening": cached.text[:400],
            }
        )

    index.sort(key=lambda row: row["rule_keyword_hits"], reverse=True)

    slug = _slugify(label or query)
    manifest_dir = CACHE_DIR / "sweeps"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / f"{slug}.json"
    manifest = {
        "query": query,
        "label": slug,
        "swept_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "parameters": {
            "max_videos": max_videos,
            "published_after": published_after,
            "min_duration_minutes": min_duration_minutes,
            "order": order,
        },
        "transcribed": index,
        "failed": failures,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2))

    return {
        "query": query,
        "transcribed": len(index),
        "failed": len(failures),
        "manifest_path": _rel(manifest_path),
        "total_estimated_tokens": sum(row["estimated_tokens"] for row in index),
        "index": index,
        "failures": failures,
        "next_step": (
            "Do NOT read these all. Use youtube_grep_transcripts to find where "
            "rules are stated, read the top one or two cache_path files, then "
            "youtube_article_record to write the research/articles/ file."
        ),
    }


@server.tool(
    description=(
        "Regex search across cached transcripts with surrounding context and "
        "timestamps. This is how you extract stated rules from a corpus without "
        "loading it. Scope with video_ids or a sweep label."
    )
)
def youtube_grep_transcripts(
    pattern: str,
    video_ids: list[str] | None = None,
    sweep_label: str | None = None,
    context_lines: int = 2,
    max_hits_per_video: int = 12,
    ignore_case: bool = True,
) -> dict:
    """Args:
        pattern: Python regex, e.g. r"stop ?loss|invalidat|risk to reward".
        video_ids: Restrict to these videos.
        sweep_label: Restrict to the videos in a saved sweep manifest.
        context_lines: Transcript lines of context either side of a hit.
        max_hits_per_video: Cap per video so one rambler can't flood the result.
        ignore_case: Case-insensitive matching.
    """
    if sweep_label and not video_ids:
        manifest_path = CACHE_DIR / "sweeps" / f"{_slugify(sweep_label)}.json"
        if not manifest_path.exists():
            raise RuntimeError(f"No sweep manifest at {_rel(manifest_path)}")
        manifest = json.loads(manifest_path.read_text())
        video_ids = [row["video_id"] for row in manifest["transcribed"]]

    transcript_dir = CACHE_DIR / "transcripts"
    if video_ids:
        targets = [transcript_dir / f"{extract_video_id(v)}.txt" for v in video_ids]
        targets = [p for p in targets if p.exists()]
    else:
        targets = sorted(transcript_dir.glob("*.txt"))

    flags = re.IGNORECASE if ignore_case else 0
    regex = re.compile(pattern, flags)

    results, total = [], 0
    for path in targets:
        lines = path.read_text().splitlines()
        hits = []
        for i, line in enumerate(lines):
            if not regex.search(line):
                continue
            start, end = max(0, i - context_lines), min(len(lines), i + context_lines + 1)
            stamp = re.match(r"\[(\d+:\d{2}(?::\d{2})?)\]", line)
            hits.append(
                {
                    "timestamp": stamp.group(1) if stamp else None,
                    "context": "\n".join(lines[start:end]),
                }
            )
            if len(hits) >= max_hits_per_video:
                break
        if hits:
            video_id = path.stem
            results.append(
                {
                    "video_id": video_id,
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "hits": len(hits),
                    "matches": hits,
                }
            )
            total += len(hits)

    results.sort(key=lambda row: row["hits"], reverse=True)
    return {
        "pattern": pattern,
        "videos_searched": len(targets),
        "videos_with_hits": len(results),
        "total_hits": total,
        "results": results,
    }


@server.tool(description="List everything already cached — the research audit trail.")
def youtube_cache_status() -> dict:
    transcript_dir = CACHE_DIR / "transcripts"
    sweep_dir = CACHE_DIR / "sweeps"
    transcripts = []
    for meta_path in sorted(transcript_dir.glob("*.json")):
        try:
            transcripts.append(json.loads(meta_path.read_text()))
        except json.JSONDecodeError:
            continue
    sweeps = []
    for path in sorted(sweep_dir.glob("*.json")):
        try:
            manifest = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        sweeps.append(
            {
                "label": manifest.get("label"),
                "query": manifest.get("query"),
                "swept_at": manifest.get("swept_at"),
                "transcribed": len(manifest.get("transcribed", [])),
                "path": _rel(path),
            }
        )
    return {
        "cache_dir": _rel(CACHE_DIR),
        "transcripts_cached": len(transcripts),
        "total_characters": sum(t.get("characters", 0) for t in transcripts),
        "sweeps": sweeps,
        "transcripts": transcripts,
        "api_key_present": bool(os.environ.get("YOUTUBE_API_KEY", "").strip()),
        "transcripts_dir": _rel(transcript_dir),
    }


@server.tool(
    description=(
        "Write the research/articles/ file for a sweep, pre-filled with the "
        "source table and YAML frontmatter (research/README.md conventions, "
        "VAULT-SCHEMA §5 tags). The analysis sections are left for you to fill "
        "from the transcripts — this only removes the transcription."
    )
)
def youtube_article_record(
    title: str,
    sweep_label: str,
    session: str,
    mechanism_families: list[str],
    filename: str | None = None,
    status: str = "reference",
) -> dict:
    """Args:
        title: Human title, e.g. "London open sweep — video sources".
        sweep_label: The sweep whose sources go in the table.
        session: One of ny-pre | ny-gold | london | asia (VAULT-SCHEMA §5).
        mechanism_families: One or more of the controlled mechanism tags.
        filename: Override the generated filename (no extension).
        status: active | thesis-pending | greenlit | killed | reference.
    """
    if session not in SESSION_TAGS:
        raise ValueError(
            f"session must be one of {SESSION_TAGS} (VAULT-SCHEMA §5 controlled "
            f"vocabulary — improvised values are a lint failure). Got {session!r}."
        )
    unknown = [m for m in mechanism_families if m not in MECHANISM_TAGS]
    if unknown:
        raise ValueError(
            f"unknown mechanism_families {unknown}. Controlled vocabulary is "
            f"{MECHANISM_TAGS}. Adding a value is a one-line change to "
            "docs/VAULT-SCHEMA.md §5, not an improvisation here."
        )

    manifest_path = CACHE_DIR / "sweeps" / f"{_slugify(sweep_label)}.json"
    if not manifest_path.exists():
        raise RuntimeError(
            f"No sweep manifest at {_rel(manifest_path)}. Run youtube_research_sweep first."
        )
    manifest = json.loads(manifest_path.read_text())
    sources = manifest.get("transcribed", [])
    failed = manifest.get("failed", [])

    today = datetime.now(UTC).date().isoformat()
    tags = [session, *mechanism_families, "research-sweep", "youtube"]
    urls = [row["url"] for row in sources]

    lines = [
        "---",
        f"date: {today}",
        f"status: {status}",
        f"tags: [{', '.join(tags)}]",
        "sources: [" + ", ".join(f'"{u}"' for u in urls) + "]",
        "---",
        "",
        f"# {title}",
        "",
        (
            f"Sourcing: YouTube Data API v3 search (`{manifest.get('query')}`) plus "
            "fetched transcripts — not search snippets. Every quote below is verbatim "
            "with a timestamp, and the full transcripts are committed under "
            "`research/youtube/transcripts/`, so any claim here can be re-checked "
            "against what was actually said."
        ),
        "",
        f"Sweep manifest: `{_rel(manifest_path)}`",
        "",
        "## Sources transcribed",
        "",
        "| Video | Channel | Published | Duration | Views | Rule hits | Transcript |",
        "|---|---|---|---|---|---|---|",
    ]
    row_format = (
        "| [{title}]({url}) | {channel} | {published} | {duration} "
        "| {views} | {hits} | `{path}` |"
    )
    for row in sources:
        lines.append(
            row_format.format(
                title=row["title"].replace("|", "\\|")[:70],
                url=row["url"],
                channel=row["channel"].replace("|", "\\|"),
                published=(row.get("published_at") or "")[:10],
                duration=row.get("duration") or "?",
                views=row.get("views") or "?",
                hits=row.get("rule_keyword_hits", 0),
                path=row["cache_path"],
            )
        )
    lines += [
        "",
        (
            "`Rule hits` counts how often the speaker states rules (entry / stop / "
            "invalidation / session / filter) rather than narrating. It ranks reading "
            "order; it is not a quality score."
        ),
        "",
    ]

    if failed:
        lines += ["### No transcript available", ""]
        for row in failed:
            lines.append(f"- [{row['title'][:70]}]({row['url']}) — {row['reason']}")
        lines.append("")

    lines += [
        "## What's usable",
        "",
        (
            "_Mechanisms stated precisely enough to become a candidate thesis. Quote "
            "verbatim with `[video_id @ mm:ss]` so the claim traces to the transcript._"
        ),
        "",
        "- ",
        "",
        "## What's noise",
        "",
        (
            "_Claimed edges with no stated mechanism, unverifiable performance claims, "
            "and rules that dissolve on inspection. Recorded so the same source isn't "
            "re-read in three months._"
        ),
        "",
        "- ",
        "",
        "## Contradictions between sources",
        "",
        (
            "_Where two speakers give different rules for the same setup. Disagreement "
            "marks the discretionary joints — the places a mechanical spec has to "
            "invent a number, and therefore the places overfitting will enter._"
        ),
        "",
        "- ",
        "",
        "## Candidate leads",
        "",
        "_Which `research/candidates/` files this feeds, or should create._",
        "",
        "- ",
        "",
    ]

    article_dir = REPO_ROOT / "research" / "articles"
    article_dir.mkdir(parents=True, exist_ok=True)
    article_path = article_dir / f"{_slugify(filename or f'yt-{today}-{sweep_label}')}.md"
    article_path.write_text("\n".join(lines))

    return {
        "created": _rel(article_path),
        "sources_linked": len(sources),
        "transcript_failures": len(failed),
        "tags": tags,
        "next_step": (
            "Fill 'What's usable' / 'What's noise' / 'Contradictions' from the "
            "transcripts — use youtube_grep_transcripts to find the passages. "
            "Nothing gets cited in a thesis that isn't quoted here first."
        ),
    }


if __name__ == "__main__":
    server.run("stdio")
