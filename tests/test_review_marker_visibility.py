from generate import _usable_block, _weekly_resolve_or_placeholder


def test_usable_block_preserves_review_markers():
    assert _usable_block("[TODO: write this section]") == "[TODO: write this section]"
    assert _usable_block("[BLOCK NOT FOUND: year_ahead.foo]") == "[BLOCK NOT FOUND: year_ahead.foo]"
    assert _usable_block("[MISSING BLOCK FILE: blocks/example.json]") == "[MISSING BLOCK FILE: blocks/example.json]"


def test_weekly_placeholder_policy_keeps_literal_todo_visible():
    resolved, used_placeholder = _weekly_resolve_or_placeholder("TODO", "legacy fallback")

    assert resolved == "TODO"
    assert used_placeholder is True
