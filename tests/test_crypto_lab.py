"""Phase 5 tests for educational AES-GCM asset packs."""

from __future__ import annotations

import unittest

from crypto_lab.asset_pack import (
    AESGCM,
    IntegrityError,
    NonceTracker,
    ReplayError,
    create_asset_pack,
    derive_key,
    load_asset_pack,
)


@unittest.skipIf(AESGCM is None, "cryptography package not installed")
class CryptoLabTests(unittest.TestCase):
    def test_encrypt_decrypt_roundtrip(self) -> None:
        assets = {"scene.bin": b"\x01\x02\x03", "meta.json": b'{"name":"demo"}'}
        blob = create_asset_pack(assets, "passphrase-1")
        decoded = load_asset_pack(blob, "passphrase-1")
        self.assertEqual(decoded, assets)

    def test_wrong_key_fails_authentication(self) -> None:
        blob = create_asset_pack({"x.bin": b"hello"}, "correct")
        with self.assertRaises(IntegrityError):
            load_asset_pack(blob, "wrong")

    def test_tampered_payload_fails_authentication(self) -> None:
        blob = bytearray(create_asset_pack({"x.bin": b"hello"}, "pw"))
        blob[-1] ^= 0x01
        with self.assertRaises(IntegrityError):
            load_asset_pack(bytes(blob), "pw")

    def test_nonce_replay_detection(self) -> None:
        tracker = NonceTracker()
        blob = create_asset_pack({"x.bin": b"hello"}, "pw")
        first = load_asset_pack(blob, "pw", nonce_tracker=tracker)
        self.assertEqual(first["x.bin"], b"hello")
        with self.assertRaises(ReplayError):
            load_asset_pack(blob, "pw", nonce_tracker=tracker)

    def test_key_derivation_is_stable_for_same_salt(self) -> None:
        salt = b"\x00" * 16
        key1 = derive_key("abc", salt)
        key2 = derive_key("abc", salt)
        self.assertEqual(key1, key2)


if __name__ == "__main__":
    unittest.main()
