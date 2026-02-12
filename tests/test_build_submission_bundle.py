import tempfile
import unittest
from pathlib import Path

from scripts.build_submission_bundle import sha256_file


class BuildSubmissionBundleTest(unittest.TestCase):
    def test_sha256_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.txt"
            path.write_text("abc", encoding="utf-8")
            digest = sha256_file(path)
            self.assertEqual(
                "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
                digest,
            )


if __name__ == "__main__":
    unittest.main()
