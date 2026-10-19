from app import catalog, guard

SETTINGS = {
    "monthly_budget": 200.0,
    "per_purchase_cap": 100.0,
    "blocked_categories": ["alcohol"],
    "savings_goal_name": "Emergency fund",
    "savings_goal_target": 1000.0,
    "savings_goal_saved": 400.0,
    "monthly_savings": 300.0,
}


def test_blocked_category():
    result = guard.check_rules(catalog.get_product("wine-01"), SETTINGS, 0)
    assert result.decision == "blocked"


def test_over_cap_nudges_to_cheaper_item_in_same_category():
    result = guard.check_rules(catalog.get_product("head-02"), SETTINGS, 0)
    assert result.decision == "nudge"
    assert result.alternative["id"] == "head-01"


def test_over_cap_with_no_alternative_blocks():
    settings = {**SETTINGS, "per_purchase_cap": 10.0}
    result = guard.check_rules(catalog.get_product("book-01"), settings, 0)
    assert result.decision == "blocked"
    assert result.alternative is None


def test_over_remaining_budget_nudges():
    result = guard.check_rules(catalog.get_product("moist-03"), SETTINGS, 180.0)
    assert result.decision == "nudge"
    assert result.alternative["price"] <= 20.0


def test_within_limits_passes():
    assert guard.check_rules(catalog.get_product("moist-01"), SETTINGS, 0).decision == "pass"


def test_goal_impact_days():
    impact = guard.goal_impact(30.0, SETTINGS)  # saving $10/day
    assert impact["days_delayed"] == 3.0
    assert impact["days_to_goal_before"] == 60.0
    assert impact["days_to_goal_after"] == 63.0


def test_goal_impact_without_savings_rate():
    assert guard.goal_impact(30.0, {**SETTINGS, "monthly_savings": 0}) is None
