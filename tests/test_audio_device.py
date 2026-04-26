"""Unit tests for MMIO audio sink."""

from __future__ import annotations

import unittest

from emulator.devices.audio_device import AudioDevice


class AudioDeviceTests(unittest.TestCase):
    def test_write_and_length_read(self) -> None:
        dev = AudioDevice(max_samples=4)
        dev.write(0, 0x10)
        dev.write(0, 0x20)
        self.assertEqual(dev.read(0), 2)
        self.assertEqual(dev.samples, [0x10, 0x20])

    def test_ring_cap_drops_oldest(self) -> None:
        dev = AudioDevice(max_samples=2)
        dev.write(0, 1)
        dev.write(0, 2)
        dev.write(0, 3)
        self.assertEqual(dev.samples, [2, 3])
        self.assertEqual(dev.read(0), 2)


if __name__ == "__main__":
    unittest.main()
