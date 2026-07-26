from eia_engine.mode_selection import select_dominant_mode, select_secondary_mode


def test_select_dominant_mode_uses_catalog_order_for_ties():
    scores = {"Direct Spark": 0.7, "Responsive Pull": 0.7}

    assert select_dominant_mode(scores, ["Direct Spark", "Responsive Pull"]) == "Direct Spark"


def test_secondary_requires_threshold_and_near_dominant_score():
    scores = {"Direct Spark": 0.76, "Responsive Pull": 0.61, "Quiet Accumulation": 0.42}

    assert select_secondary_mode(scores, "Direct Spark", list(scores)) == "Responsive Pull"


def test_secondary_allows_named_contradiction_pair():
    scores = {"Direct Spark": 0.82, "Quiet Accumulation": 0.55}

    assert select_secondary_mode(scores, "Direct Spark", list(scores)) == "Quiet Accumulation"
