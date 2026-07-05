from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from youtube import _format_iso8601_duration, _is_probable_short


class YouTubeDurationTests(unittest.TestCase):
    def test_formats_iso8601_duration(self) -> None:
        self.assertEqual(_format_iso8601_duration("PT32M41S"), "32:41")
        self.assertEqual(_format_iso8601_duration("PT1H02M03S"), "1:02:03")

    def test_detects_probable_short(self) -> None:
        self.assertTrue(_is_probable_short("PT59S"))
        self.assertFalse(_is_probable_short("PT2M01S"))


if __name__ == "__main__":
    unittest.main()
