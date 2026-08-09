"""Regression controls for exact sales-landing capture provenance."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from PIL import Image


HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[1]
MODULE_PATH = HERE / "check_sales_landing_captures.py"
FAILED_CANDIDATE = "a350aa9c590ea02dfcf89240df772be8d8bdd041"
SPEC = importlib.util.spec_from_file_location("capture_check", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {MODULE_PATH}")
capture_check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(capture_check)

INTERPRETER_MODES = [(), ("-O",), ("-OO",)]


class CaptureProvenanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for specifications in capture_check.CAPTURES.values():
            for name, _size, _sha in specifications:
                shutil.copy2(HERE / name, self.root / name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_checker(self, mode: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", *mode, str(MODULE_PATH), "--root", str(self.root)],
            cwd=REPOSITORY,
            capture_output=True,
            check=False,
            text=True,
        )

    def assert_rejected_in_all_modes(self) -> None:
        for mode in INTERPRETER_MODES:
            with self.subTest(mode=mode or ("normal",)):
                result = self.run_checker(mode)
                self.assertNotEqual(
                    result.returncode,
                    0,
                    msg=f"stdout={result.stdout}\nstderr={result.stderr}",
                )
                self.assertNotIn(
                    "sales-landing capture provenance checks: PASS", result.stdout
                )

    def test_exact_reviewed_artifacts_pass(self) -> None:
        for mode in INTERPRETER_MODES:
            with self.subTest(mode=mode or ("normal",)):
                result = self.run_checker(mode)
                self.assertEqual(
                    result.returncode,
                    0,
                    msg=f"stdout={result.stdout}\nstderr={result.stderr}",
                )
                self.assertIn(
                    "sales-landing capture provenance checks: PASS", result.stdout
                )

    def test_uniform_blank_substitution_fails(self) -> None:
        name, size, _sha = capture_check.CAPTURES["mobile"][0]
        Image.new("RGB", size, "#f7f1e3").save(self.root / name)
        self.assert_rejected_in_all_modes()

    def test_original_false_green_capture_fails(self) -> None:
        name, _size, _sha = capture_check.CAPTURES["mobile"][0]
        source = f"{FAILED_CANDIDATE}:.claude/design-qa/{name}"
        result = subprocess.run(
            ["git", "show", source],
            cwd=REPOSITORY,
            capture_output=True,
            check=True,
        )
        (self.root / name).write_bytes(result.stdout)
        self.assert_rejected_in_all_modes()

    def test_high_entropy_synthetic_substitution_fails(self) -> None:
        name, size, _sha = capture_check.CAPTURES["mobile"][0]
        needed = size[0] * size[1] * 3
        pixels = bytearray()
        counter = 0
        while len(pixels) < needed:
            pixels.extend(hashlib.sha256(counter.to_bytes(8, "big")).digest())
            counter += 1
        Image.frombytes("RGB", size, bytes(pixels[:needed])).save(self.root / name)
        self.assert_rejected_in_all_modes()

    def test_swapped_valid_capture_fails(self) -> None:
        target, _size, _sha = capture_check.CAPTURES["mobile"][0]
        source, _size, _sha = capture_check.CAPTURES["mobile"][1]
        shutil.copy2(self.root / source, self.root / target)
        self.assert_rejected_in_all_modes()


if __name__ == "__main__":
    unittest.main()
