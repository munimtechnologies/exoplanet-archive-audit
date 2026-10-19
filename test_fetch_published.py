# Apache-2.0. Tests for fetch_published 0.2.0 (pure function only; no network). Made with AI agents, MV2 of Munim, Inc.
import unittest

import fetch_published as fp


class Acceptable(unittest.TestCase):
    def test_json_when_no_text_expected(self):
        self.assertTrue(fp.acceptable(b'{"a": 1}'))
        self.assertTrue(fp.acceptable(b"[1, 2]", ""))
        self.assertFalse(fp.acceptable(b"404: Not Found"))
        self.assertFalse(fp.acceptable(b""))

    def test_text_when_expected(self):
        note = "# Rubble reserve pre-registration (P1, P2)\n".encode("utf-8")
        self.assertTrue(fp.acceptable(note, "Rubble reserve pre-registration"))
        self.assertFalse(fp.acceptable(b"404: Not Found", "Rubble reserve pre-registration"))
        self.assertFalse(fp.acceptable(b'{"a": 1}', "Rubble reserve pre-registration"))


if __name__ == "__main__":
    unittest.main()
