import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from selectors.block_selector import select_block, select_block_traced, select_tier_block


class BlockSelectorTests(unittest.TestCase):
    def test_select_block_preserves_exact_empty_string(self):
        with patch("selectors.block_selector._load_blocks", return_value={"exact": "", "fallback": "fallback text"}):
            self.assertEqual(select_block("daily_horoscope", "todays_sky", "exact"), "")

    def test_select_block_traced_preserves_exact_empty_string_without_fallback(self):
        with patch("selectors.block_selector._load_blocks", return_value={"exact": "", "fallback": "fallback text"}):
            self.assertEqual(
                select_block_traced("daily_horoscope", "todays_sky", "exact"),
                ("", ["exact"], False),
            )

    def test_select_tier_block_uses_authored_non_todo_last_resort(self):
        with patch(
            "selectors.block_selector.select_block",
            side_effect=[
                "[BLOCK NOT FOUND: x]",
                "[BLOCK NOT FOUND: x]",
                "This route is not fully authored yet. Stay close to the computed pattern and avoid adding claims the current block library does not explicitly support.",
            ],
        ):
            result = select_tier_block("soul_ecosystem", "foresight_pattern", "Vindicated Oracle", "DOMINANT")
        self.assertNotIn("TODO", result)
        self.assertIn("not fully authored yet", result)


if __name__ == "__main__":
    unittest.main()
