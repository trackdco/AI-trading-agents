"""Tests for the YouTube research MCP server.

No network. Transcript fetching is exercised against on-disk fixtures, which is
the path that matters — the cache is what the research audit trail is made of.

    .venv/bin/python -m pytest tools/youtube-mcp/test_server.py -q
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
            "short",  # too few characters
            "way-too-long-to-be-an-id",  # too many
            "has spaces!",  # illegal characters
            "https://www.youtube.com/@somechannel",  # a channel, not a video
        ],
    )
    def test_rejects_junk(self, value):
        with pytest.raises(ValueError):
            server.extract_video_id(value)

    def test_any_11_char_id_shaped_string_is_accepted(self):
        # YouTube IDs are exactly 11 chars of [A-Za-z0-9_-], so an arbitrary
        # string of that shape is indistinguishable from a real ID without a
        # network call. It is accepted here and fails at the API instead.
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
        assert {match["timestamp"] for match in result["results"][0]["matches"]} == {"0:25", "0:40"}

    def test_respects_max_hits(self, isolated_cache):
        _seed(isolated_cache, "AAAAAAAAAAA", RULES)
        result = server.youtube_grep_transcripts(r"\[", max_hits_per_video=2)
        assert result["total_hits"] == 2

    def test_sweep_label_scopes_the_search(self, isolated_cache):
        _seed(isolated_cache, "AAAAAAAAAAA", RULES)
        _seed(isolated_cache, "BBBBBBBBBBB", NOISE)
        sweeps = isolated_cache / "sweeps"
        sweeps.mkdir(parents=True, exist_ok=True)
        (sweeps / "scoped.json").write_text(
            json.dumps({"transcribed": [{"video_id": "AAAAAAAAAAA"}]})
        )
        result = server.youtube_grep_transcripts("the", sweep_label="scoped")
        assert result["videos_searched"] == 1

    def test_unknown_sweep_label_is_a_clear_error(self, isolated_cache):
        with pytest.raises(RuntimeError, match="No sweep manifest"):
            server.youtube_grep_transcripts("x", sweep_label="does-not-exist")


class TestApiKeyGuard:
    def test_search_without_key_explains_itself(self, monkeypatch):
        monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
        with pytest.raises(RuntimeError, match="YOUTUBE_API_KEY is not set"):
            server.youtube_search("anything")

    def test_transcript_tools_do_not_need_a_key(self, isolated_cache, monkeypatch):
        monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
        _seed(isolated_cache, "AAAAAAAAAAA", RULES)
        assert server.youtube_get_transcript("AAAAAAAAAAA")["segments"] == 4


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
