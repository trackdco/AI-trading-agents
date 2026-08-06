"""Tests for the YouTube research MCP server.

No network. Transcript handling is exercised against on-disk fixtures, which is
the path that matters — the cache is what the research audit trail is made of.

    tools/youtube-mcp/.venv/bin/python -m pytest tools/youtube-mcp/test_server.py -q

Run from the repo root. This suite is deliberately outside the main `tests/`
tree and the main venv: the MCP server has its own dependencies (mcp,
youtube-transcript-api) that the engine does not, and the approved-dependency
list for the engine stays untouched.
"""

from __future__ import annotations

import json

import pytest

import server


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "CACHE_DIR", tmp_path)
    return tmp_path


def _seed(cache_dir, video_id: str, lines: list[str]) -> None:
    directory = cache_dir / "transcripts"
    directory.mkdir(parents=True, exist_ok=True)
    text = "\n".join(lines)
    (directory / f"{video_id}.txt").write_text(text)
    (directory / f"{video_id}.json").write_text(
        json.dumps(
            {
                "video_id": video_id,
                "language": "en",
                "segments": len(lines),
                "characters": len(text),
                "cached_at": "2026-08-05T00:00:00+00:00",
            }
        )
    )


def _seed_sweep(cache_dir, label: str, rows: list[dict], failed: list[dict] | None = None) -> None:
    sweeps = cache_dir / "sweeps"
    sweeps.mkdir(parents=True, exist_ok=True)
    (sweeps / f"{label}.json").write_text(
        json.dumps(
            {
                "query": "london open sweep nasdaq",
                "label": label,
                "swept_at": "2026-08-05T00:00:00+00:00",
                "transcribed": rows,
                "failed": failed or [],
            }
        )
    )


RULES = [
    "[0:00] today we cover the london open sweep",
    "[0:12] entry is a sweep of the asia high then displacement back inside",
    "[0:25] your stop loss goes above the sweep wick that is the invalidation",
    "[0:40] target the opposing session low for 2 to 1 risk to reward",
]
NOISE = [
    "[0:00] hey guys quick video",
    "[0:08] this setup just works trust me",
    "[0:20] smash that like button",
]

SWEEP_ROW = {
    "video_id": "AAAAAAAAAAA",
    "title": "London Open Sweep | NQ",
    "channel": "Some Trader",
    "url": "https://www.youtube.com/watch?v=AAAAAAAAAAA",
    "published_at": "2026-01-15T00:00:00Z",
    "duration": "18:22",
    "views": 41000,
    "rule_keyword_hits": 9,
    "cache_path": "research/youtube/transcripts/AAAAAAAAAAA.txt",
}


class TestVideoIdExtraction:
    @pytest.mark.parametrize(
        "value",
        [
            "dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/shorts/dQw4w9WgXcQ",
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
            "https://www.youtube.com/live/dQw4w9WgXcQ",
            "  dQw4w9WgXcQ  ",
        ],
    )
    def test_accepts_every_url_form(self, value):
        assert server.extract_video_id(value) == "dQw4w9WgXcQ"

    @pytest.mark.parametrize(
        "value",
        [
            "short",
            "way-too-long-to-be-an-id",
            "has spaces!",
            "https://www.youtube.com/@somechannel",
        ],
    )
    def test_rejects_junk(self, value):
        with pytest.raises(ValueError):
            server.extract_video_id(value)

    def test_any_id_shaped_string_is_accepted(self):
        # YouTube IDs are exactly 11 chars of [A-Za-z0-9_-], so an arbitrary
        # string of that shape is indistinguishable from a real ID without a
        # network call. Accepted here; it fails at the API instead.
        assert server.extract_video_id("not-a-video") == "not-a-video"


class TestFormatting:
    def test_hms(self):
        assert server._hms(95) == "1:35"
        assert server._hms(3725) == "1:02:05"

    def test_iso_duration(self):
        assert server._iso_duration_to_seconds("PT1H2M5S") == 3725
        assert server._iso_duration_to_seconds("PT45S") == 45
        assert server._iso_duration_to_seconds("") == 0

    def test_slugify(self):
        assert server._slugify("ICT Silver Bullet / NQ 10am!") == "ict-silver-bullet-nq-10am"


class TestTranscriptCache:
    def test_reads_cache_without_network(self, isolated_cache):
        _seed(isolated_cache, "AAAAAAAAAAA", RULES)
        result = server.youtube_get_transcript("AAAAAAAAAAA")
        assert result["from_cache"] is True
        assert result["segments"] == 4
        assert "transcript" not in result, "excerpt mode must not return full text"
        assert result["excerpt"]

    def test_full_flag_returns_everything(self, isolated_cache):
        _seed(isolated_cache, "AAAAAAAAAAA", RULES)
        result = server.youtube_get_transcript("AAAAAAAAAAA", full=True)
        assert result["transcript"].count("\n") == 3

    def test_rule_density_ranks_substance_above_noise(self, isolated_cache):
        _seed(isolated_cache, "AAAAAAAAAAA", RULES)
        _seed(isolated_cache, "BBBBBBBBBBB", NOISE)
        substantive = server.youtube_get_transcript("AAAAAAAAAAA")["rule_keyword_hits"]
        filler = server.youtube_get_transcript("BBBBBBBBBBB")["rule_keyword_hits"]
        assert substantive > filler


class TestGrep:
    def test_finds_rules_with_timestamps(self, isolated_cache):
        _seed(isolated_cache, "AAAAAAAAAAA", RULES)
        _seed(isolated_cache, "BBBBBBBBBBB", NOISE)
        result = server.youtube_grep_transcripts(r"stop ?loss|invalidat|risk to reward")
        assert result["videos_searched"] == 2
        assert result["videos_with_hits"] == 1
        assert result["total_hits"] == 2
        assert {m["timestamp"] for m in result["results"][0]["matches"]} == {"0:25", "0:40"}

    def test_respects_max_hits(self, isolated_cache):
        _seed(isolated_cache, "AAAAAAAAAAA", RULES)
        result = server.youtube_grep_transcripts(r"\[", max_hits_per_video=2)
        assert result["total_hits"] == 2

    def test_sweep_label_scopes_the_search(self, isolated_cache):
        _seed(isolated_cache, "AAAAAAAAAAA", RULES)
        _seed(isolated_cache, "BBBBBBBBBBB", NOISE)
        _seed_sweep(isolated_cache, "scoped", [{"video_id": "AAAAAAAAAAA"}])
        result = server.youtube_grep_transcripts("the", sweep_label="scoped")
        assert result["videos_searched"] == 1

    def test_unknown_sweep_label_is_a_clear_error(self):
        with pytest.raises(RuntimeError, match="No sweep manifest"):
            server.youtube_grep_transcripts("x", sweep_label="does-not-exist")


class TestApiKeyGuard:
    """Search and channel listing fall back to scraping the public pages, so
    they need no key. Only the tools that read per-video *statistics* still
    require one, and those must say so clearly rather than failing obscurely."""

    @pytest.mark.parametrize(
        ("call", "kwargs"),
        [("youtube_video_details", {"videos": ["dQw4w9WgXcQ"]}), ("youtube_find_channel", {"query": "x"})],
    )
    def test_api_only_tools_explain_the_missing_key(self, monkeypatch, call, kwargs):
        monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
        with pytest.raises(RuntimeError, match="YOUTUBE_API_KEY is not set"):
            getattr(server, call)(**kwargs)

    def test_search_takes_the_scrape_path_without_a_key(self, monkeypatch):
        monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
        monkeypatch.setattr(
            server, "_scrape_search",
            lambda q, n: [{"video_id": "AAAAAAAAAAA", "title": "t", "duration": "12:00",
                           "views": "1.2K views", "published": "1 day ago"}])
        result = server.youtube_search("anything")
        assert "no YOUTUBE_API_KEY" in result["source"]
        assert result["results"][0]["views_estimate"] == 1200
        assert result["results"][0]["url"].endswith("AAAAAAAAAAA")

    def test_scrape_search_respects_min_duration(self, monkeypatch):
        monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
        monkeypatch.setattr(
            server, "_scrape_search",
            lambda q, n: [{"video_id": "AAAAAAAAAAA", "title": "short", "duration": "3:00",
                           "views": "5 views", "published": "1 day ago"}])
        assert server.youtube_search("x", min_duration_minutes=8)["count"] == 0

    def test_transcript_tools_do_not_need_a_key(self, isolated_cache, monkeypatch):
        monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
        _seed(isolated_cache, "AAAAAAAAAAA", RULES)
        assert server.youtube_get_transcript("AAAAAAAAAAA")["segments"] == 4


class TestScrapeParsers:
    """The channel listing moved to lockupViewModel in 2025. Both shapes are
    parsed, because YouTube will move it again."""

    def test_parses_lockup_view_model(self):
        lockup = {
            "contentType": "LOCKUP_CONTENT_TYPE_VIDEO",
            "contentId": "AAAAAAAAAAA",
            "contentImage": {"thumbnailViewModel": {"overlays": [
                {"thumbnailBottomOverlayViewModel": {"badges": [
                    {"thumbnailBadgeViewModel": {"text": "16:08"}}]}}]}},
            "metadata": {"lockupMetadataViewModel": {
                "title": {"content": "Opening Range Breakout with AMT"},
                "metadata": {"contentMetadataViewModel": {"metadataRows": [
                    {"metadataParts": [{"text": {"content": "3.6K views"}},
                                       {"text": {"content": "10 days ago"}}]}]}}}},
        }
        v = server._lockup_to_video(lockup)
        assert v == {"video_id": "AAAAAAAAAAA", "title": "Opening Range Breakout with AMT",
                     "duration": "16:08", "views": "3.6K views", "published": "10 days ago"}

    def test_ignores_non_video_lockups(self):
        assert server._lockup_to_video({"contentType": "LOCKUP_CONTENT_TYPE_PLAYLIST"}) is None

    def test_harvest_handles_both_shapes_and_dedupes(self):
        tree = {"a": [{"lockupViewModel": {"contentType": "LOCKUP_CONTENT_TYPE_VIDEO",
                                           "contentId": "AAAAAAAAAAA", "metadata": {}}},
                      {"videoRenderer": {"videoId": "BBBBBBBBBBB",
                                         "title": {"runs": [{"text": "Second"}]}}},
                      {"videoRenderer": {"videoId": "BBBBBBBBBBB", "title": {"runs": []}}}],
                "b": {"continuationCommand": {"token": "TOKEN123"}}}
        out, seen, conts = [], set(), []
        server._harvest(tree, out, seen, conts)
        assert [v["video_id"] for v in out] == ["AAAAAAAAAAA", "BBBBBBBBBBB"]
        assert conts == ["TOKEN123"]

    @pytest.mark.parametrize(("text", "minutes"),
                            [("16:08", 16.13), ("3:49:37", 229.62), ("", 0.0), ("bad", 0.0)])
    def test_duration_to_minutes(self, text, minutes):
        assert round(server._duration_to_minutes(text), 2) == minutes

    @pytest.mark.parametrize(("text", "count"),
                            [("3.6K views", 3600), ("1,583,686 views", 1583686),
                             ("2.67M subscribers", 2670000), ("", 0)])
    def test_views_to_int(self, text, count):
        assert server._views_to_int(text) == count


class TestDotenvLoading:
    def test_fills_a_variable_that_is_unset(self, tmp_path, monkeypatch):
        monkeypatch.delenv("SOME_TEST_KEY", raising=False)
        env = tmp_path / ".env"
        env.write_text("# comment\nSOME_TEST_KEY=abc123\nMALFORMED\n")
        server._load_dotenv(env)
        assert server.os.environ["SOME_TEST_KEY"] == "abc123"

    def test_fills_a_variable_set_to_empty(self, tmp_path, monkeypatch):
        # .mcp.json passes "${VAR:-}", which sets VAR to "" when the shell has
        # no value. That must not shadow the .env file.
        monkeypatch.setenv("SOME_TEST_KEY", "")
        (tmp_path / ".env").write_text("SOME_TEST_KEY=fromdotenv\n")
        server._load_dotenv(tmp_path / ".env")
        assert server.os.environ["SOME_TEST_KEY"] == "fromdotenv"

    def test_does_not_clobber_a_real_value(self, tmp_path, monkeypatch):
        monkeypatch.setenv("SOME_TEST_KEY", "from-shell")
        (tmp_path / ".env").write_text("SOME_TEST_KEY=fromdotenv\n")
        server._load_dotenv(tmp_path / ".env")
        assert server.os.environ["SOME_TEST_KEY"] == "from-shell"

    def test_missing_file_is_not_an_error(self, tmp_path):
        server._load_dotenv(tmp_path / "nope.env")


class TestCacheStatus:
    def test_reports_what_is_cached(self, isolated_cache):
        _seed(isolated_cache, "AAAAAAAAAAA", RULES)
        _seed(isolated_cache, "BBBBBBBBBBB", NOISE)
        status = server.youtube_cache_status()
        assert status["transcripts_cached"] == 2
        assert status["total_characters"] > 0


class TestArticleRecord:
    """The article writer must obey research/README.md and VAULT-SCHEMA §5.
    Improvised tag values are a lint failure in the vault, so they are rejected
    here rather than written and caught later."""

    def test_writes_frontmatter_and_source_table(self, isolated_cache, tmp_path, monkeypatch):
        monkeypatch.setattr(server, "REPO_ROOT", tmp_path)
        _seed_sweep(isolated_cache, "london-open-sweep", [SWEEP_ROW])
        result = server.youtube_article_record(
            title="London open sweep — video sources",
            sweep_label="london-open-sweep",
            session="london",
            mechanism_families=["order-flow", "overnight-structure"],
        )
        assert result["sources_linked"] == 1
        text = (tmp_path / result["created"]).read_text()
        assert text.startswith("---\n")
        assert "status: reference" in text
        assert "tags: [london, order-flow, overnight-structure, research-sweep, youtube]" in text
        assert '"https://www.youtube.com/watch?v=AAAAAAAAAAA"' in text
        assert "London Open Sweep" in text
        for heading in ("What's usable", "What's noise", "Contradictions between sources"):
            assert heading in text

    def test_records_transcript_failures(self, isolated_cache, tmp_path, monkeypatch):
        monkeypatch.setattr(server, "REPO_ROOT", tmp_path)
        _seed_sweep(
            isolated_cache,
            "with-failures",
            [SWEEP_ROW],
            failed=[
                {
                    "video_id": "CCCCCCCCCCC",
                    "title": "Captions Off",
                    "url": "https://www.youtube.com/watch?v=CCCCCCCCCCC",
                    "reason": "TranscriptsDisabled: uploader disabled captions",
                }
            ],
        )
        result = server.youtube_article_record(
            title="t",
            sweep_label="with-failures",
            session="ny-pre",
            mechanism_families=["vwap"],
        )
        assert result["transcript_failures"] == 1
        text = (tmp_path / result["created"]).read_text()
        assert "No transcript available" in text
        assert "TranscriptsDisabled" in text

    def test_rejects_improvised_session_tag(self, isolated_cache):
        _seed_sweep(isolated_cache, "s", [SWEEP_ROW])
        with pytest.raises(ValueError, match="session must be one of"):
            server.youtube_article_record(
                title="t", sweep_label="s", session="tokyo", mechanism_families=["vwap"]
            )

    def test_rejects_improvised_mechanism_tag(self, isolated_cache):
        _seed_sweep(isolated_cache, "s", [SWEEP_ROW])
        with pytest.raises(ValueError, match="unknown mechanism_families"):
            server.youtube_article_record(
                title="t",
                sweep_label="s",
                session="london",
                mechanism_families=["vwap", "moon-phase"],
            )

    def test_requires_an_existing_sweep(self):
        with pytest.raises(RuntimeError, match="No sweep manifest"):
            server.youtube_article_record(
                title="t", sweep_label="never-run", session="london", mechanism_families=["vwap"]
            )
