import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from selectors.block_selector import select_block, select_block_traced


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


if __name__ == "__main__":
    unittest.main()
