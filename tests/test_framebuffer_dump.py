"""Tests for framebuffer export helpers."""

from __future__ import annotations

import unittest

from emulator.framebuffer_dump import framebuffer_to_ascii, framebuffer_to_ppm, index_to_rgb


class FramebufferDumpTests(unittest.TestCase):
    def test_index_to_rgb_zero_is_dark(self) -> None:
        r, g, b = index_to_rgb(0)
        self.assertLess(r + g + b, 80)

    def test_ascii_contains_expected_chars(self) -> None:
        fb = [[0, 0, 5], [0, 10, 0]]
        text = framebuffer_to_ascii(fb, empty=".")
        self.assertIn(".", text)
        self.assertTrue(text.endswith("\n"))

    def test_ppm_header_and_size(self) -> None:
        fb = [[0, 1], [2, 3]]
        raw = framebuffer_to_ppm(fb)
        self.assertTrue(raw.startswith(b"P6\n2 2\n255\n"))
        payload = raw.split(b"\n255\n", 1)[1]
        self.assertEqual(len(payload), 2 * 2 * 3)


if __name__ == "__main__":
    unittest.main()
