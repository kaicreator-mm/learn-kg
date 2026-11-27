#!/usr/bin/env python3
"""Run the finite HS00 candidate contract tests."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from test_hs00 import HS00Tests

suite = unittest.defaultTestLoader.loadTestsFromTestCase(HS00Tests)
result = unittest.TextTestRunner(verbosity=2).run(suite)
print(f"HS00_TESTS={result.testsRun - len(result.failures) - len(result.errors)}/{result.testsRun}")
print("QUALIFICATION=NOT_GRANTED")
raise SystemExit(0 if result.wasSuccessful() else 1)
