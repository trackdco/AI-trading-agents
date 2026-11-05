"""The multi-firm map excludes Apex and the firms that ban a bot."""

from scripts.run_multi_firm_farm import equal_days, load_survey


def test_survey_excludes_apex_and_bot_bans():
    survey = load_survey()
    assert "apex" not in survey
    assert all("apex" not in key for key in survey)
    assert survey["take_profit_trader"]["simulate"] is False
    assert survey["alpha_futures"]["simulate"] is False
    assert survey["elite_trader_funding"]["simulate"] is False
    assert survey["lucid_flex_50k"]["simulate"] is True
    assert survey["tradeify_select_flex_50k"]["stated_breach"] == "intraday"
    assert survey["topstep_50k"]["funded_cap"] == 5


def test_equal_days_match_the_consistency_rule():
    assert equal_days(0.40, 1) == 3
    assert equal_days(0.50, 1) == 2
    assert equal_days(0.55, 1) == 2
    assert equal_days(0.30, 4) == 4
