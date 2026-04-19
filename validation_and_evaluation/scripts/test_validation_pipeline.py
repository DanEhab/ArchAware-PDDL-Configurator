"""
Validation Pipeline Test Suite
================================
Tests all 4 stages of the validation pipeline using the actual
benchmark domain files from the project.

Usage:
    python test_validation_pipeline.py                  # runs all tests (skips Docker)
    python test_validation_pipeline.py --with-docker    # include V2 Docker tests

This script uses the Barman domain (benchmarks/barman/domain.pddl) as
the primary test subject because it has the richest structure (12 actions,
15 predicates, 7 types).
"""

import sys
import os
import re
import logging
from pathlib import Path

# ── Setup paths ──
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from v1_extraction import extract_pddl_from_response
from v2_syntactic_validation import validate_with_val, check_docker_available
from v3_identity_check import is_identical_to_original, normalise_pddl
from v4_semantic_equivalence import (
    check_semantic_equivalence,
    parse_domain,
)
from validation_pipeline import validate_domain, ValidationResult

# ── Config ──
BARMAN_DOMAIN = PROJECT_ROOT / "benchmarks" / "barman" / "domain.pddl"
BARMAN_INSTANCE = PROJECT_ROOT / "benchmarks" / "barman" / "instances" / "instance-01.pddl"
VISITALL_DOMAIN = PROJECT_ROOT / "benchmarks" / "visitall" / "domain.pddl"

# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("test")

# ── Tracking ──
PASSED = 0
FAILED = 0
SKIPPED = 0


def test(name, condition, detail=""):
    """Register a test result."""
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  [PASS] {name}")
    else:
        FAILED += 1
        print(f"  [FAIL] {name}")
        if detail:
            print(f"         Detail: {detail}")


def skip(name, reason):
    """Register a skipped test."""
    global SKIPPED
    SKIPPED += 1
    print(f"  [SKIP] {name} -- {reason}")


# =====================================================================
# Stage V1 Tests: PDDL Extraction
# =====================================================================

def test_v1():
    print("\n" + "=" * 60)
    print("STAGE V1: PDDL Extraction")
    print("=" * 60)

    barman_pddl = BARMAN_DOMAIN.read_text(encoding="utf-8")

    # Test 1: Clean PDDL input (no wrapping)
    result = extract_pddl_from_response(barman_pddl)
    test("Clean PDDL input", result.startswith("(define"), f"Got: {result[:50]}...")

    # Test 2: Markdown-wrapped PDDL
    markdown_wrapped = f"Here is the reordered domain:\n\n```pddl\n{barman_pddl}\n```\n\nI reordered the actions."
    result = extract_pddl_from_response(markdown_wrapped)
    test("Markdown-wrapped PDDL", result.startswith("(define"))

    # Test 3: JSON-encoded PDDL
    json_encoded = barman_pddl.replace("\n", "\\n")
    json_encoded = f'"{json_encoded}"'
    result = extract_pddl_from_response(json_encoded)
    test("JSON-encoded PDDL", result.startswith("(define"))

    # Test 4: Empty response
    result = extract_pddl_from_response("")
    test("Empty response -> empty", result == "")

    # Test 5: Garbage response (no PDDL)
    result = extract_pddl_from_response("I cannot help with that request.")
    test("Garbage response -> empty", result == "")

    # Test 6: Unbalanced parentheses
    unbalanced = "(define (domain test) (:action move"
    result = extract_pddl_from_response(unbalanced)
    test("Unbalanced parens -> empty", result == "")

    # Test 7: PDDL with explanation text before and after
    with_explanation = f"Sure! Here's the reordered domain:\n\n{barman_pddl}\n\nNote: I reordered actions alphabetically."
    result = extract_pddl_from_response(with_explanation)
    test("PDDL with surrounding text", result.startswith("(define"))

    # Test 8: Verify extracted content is complete
    result = extract_pddl_from_response(barman_pddl)
    test("Extracted PDDL is complete (balanced)", result.count("(") == result.count(")"))


# =====================================================================
# Stage V2 Tests: Syntactic Validation (VAL)
# =====================================================================

def test_v2(with_docker: bool):
    print("\n" + "=" * 60)
    print("STAGE V2: Syntactic Validation (VAL)")
    print("=" * 60)

    if not with_docker:
        skip("All V2 tests", "Docker not requested (use --with-docker)")
        return

    docker_ok = check_docker_available()
    if not docker_ok:
        skip("All V2 tests", "Docker not available")
        return

    barman_pddl = BARMAN_DOMAIN.read_text(encoding="utf-8")

    # Test 1: Valid domain against valid problem
    result = validate_with_val(barman_pddl, str(BARMAN_INSTANCE))
    test("Valid domain + valid problem -> is_valid", result.is_valid,
         f"exit={result.exit_code}, stderr={result.stderr[:200]}")

    # Test 2: Broken PDDL
    broken = "(define (domain broken) (:action bad :parameters() :precondition (and) :effect (invalid_pred)))"
    result = validate_with_val(broken, str(BARMAN_INSTANCE))
    test("Broken PDDL -> rejected", not result.is_valid)

    # Test 3: Nonexistent problem file
    result = validate_with_val(barman_pddl, "nonexistent_problem.pddl")
    test("Nonexistent problem -> rejected", not result.is_valid)


# =====================================================================
# Stage V3 Tests: Identity Check
# =====================================================================

def test_v3():
    print("\n" + "=" * 60)
    print("STAGE V3: Identity Check")
    print("=" * 60)

    barman_pddl = BARMAN_DOMAIN.read_text(encoding="utf-8")

    # Test 1: Identical domain -> should be detected as identity
    test("Identical domain -> is_identical=True",
         is_identical_to_original(barman_pddl, barman_pddl))

    # Test 2: Same content with extra whitespace/comments
    with_comments = "; This is a comment\n" + barman_pddl + "\n; Another comment\n"
    test("Same + extra comments -> is_identical=True",
         is_identical_to_original(with_comments, barman_pddl))

    # Test 3: Same content with different whitespace
    with_whitespace = barman_pddl.replace("  ", "    ").replace("\n", "\n\n")
    test("Same + extra whitespace -> is_identical=True",
         is_identical_to_original(with_whitespace, barman_pddl))

    # Test 4: Case differences should still be identical
    case_diff = barman_pddl.replace("define", "DEFINE", 1)
    test("Case difference -> is_identical=True",
         is_identical_to_original(case_diff, barman_pddl))

    # Test 5: Different domain -> should NOT be identical
    visitall_pddl = VISITALL_DOMAIN.read_text(encoding="utf-8")
    test("Different domain -> is_identical=False",
         not is_identical_to_original(visitall_pddl, barman_pddl))

    # Test 6: Reordered predicates -> should NOT be identical
    # Swap two predicate lines
    lines = barman_pddl.split("\n")
    # Find predicate lines and swap two
    pred_indices = [i for i, l in enumerate(lines) if "(holding" in l.lower() or "(clean" in l.lower()]
    if len(pred_indices) >= 2:
        lines[pred_indices[0]], lines[pred_indices[1]] = lines[pred_indices[1]], lines[pred_indices[0]]
        reordered = "\n".join(lines)
        test("Reordered predicates -> is_identical=False",
             not is_identical_to_original(reordered, barman_pddl))
    else:
        skip("Reordered predicates test", "Could not find predicates to swap")


# =====================================================================
# Stage V4 Tests: Semantic Equivalence
# =====================================================================

def test_v4():
    print("\n" + "=" * 60)
    print("STAGE V4: Semantic Equivalence")
    print("=" * 60)

    barman_pddl = BARMAN_DOMAIN.read_text(encoding="utf-8")

    # Test 1: Parse Barman domain
    parsed = parse_domain(barman_pddl)
    test("Parse Barman domain", len(parsed["actions"]) > 0,
         f"Found {len(parsed['actions'])} actions: {list(parsed['actions'].keys())}")

    test("Barman has 12 actions", len(parsed["actions"]) == 12,
         f"Found {len(parsed['actions'])}")

    test("Barman has predicates", len(parsed["predicates"]) > 0,
         f"Found {len(parsed['predicates'])}")

    # Test 2: Same domain -> semantically equivalent
    result = check_semantic_equivalence(barman_pddl, barman_pddl)
    test("Same domain -> is_equivalent=True", result.is_equivalent)
    test("Same domain -> no semantic change", not result.has_semantic_change)

    # Test 3: Reordered actions -> should be semantically equivalent
    lines = barman_pddl.split("\n")
    # Find action blocks by looking for (:action and swap two adjacent ones
    action_starts = [i for i, l in enumerate(lines) if "(:action" in l.lower()]
    if len(action_starts) >= 2:
        # Identify the full blocks of the first two actions
        start1 = action_starts[0]
        start2 = action_starts[1]
        # Find end of first action block (up to second action)
        block1 = lines[start1:start2]
        # Find end of second action block
        end2 = action_starts[2] if len(action_starts) > 2 else len(lines)
        block2 = lines[start2:end2]
        # Swap
        reordered_lines = lines[:start1] + block2 + block1 + lines[end2:]
        reordered = "\n".join(reordered_lines)

        result = check_semantic_equivalence(reordered, barman_pddl)
        test("Reordered actions -> is_equivalent=True", result.is_equivalent)
        test("Reordered actions -> actions_reordered flag",
             result.diff_features.get("actions_reordered", 0) == 1)
    else:
        skip("Reordered actions test", "Could not find action blocks to swap")

    # Test 4: Added predicate -> semantic change detected
    injected = barman_pddl.replace(
        "(:predicates",
        "(:predicates\n    (fake-predicate ?x - object)"
    )
    result = check_semantic_equivalence(injected, barman_pddl)
    test("Added predicate -> is_equivalent=False", not result.is_equivalent)
    test("Added predicate -> has_semantic_change=True", result.has_semantic_change)
    test("Added predicate -> pred_semantic_change flag",
         result.diff_features.get("pred_semantic_change", 0) == 1)

    # Test 5: Removed action -> semantic change detected
    # Remove the last action by chopping after finding the last (:action
    if action_starts:
        last_action_start = action_starts[-1]
        truncated = "\n".join(lines[:last_action_start]) + "\n)"
        result = check_semantic_equivalence(truncated, barman_pddl)
        test("Removed action -> is_equivalent=False", not result.is_equivalent)
        test("Removed action -> actions_semantic_change flag",
             result.diff_features.get("actions_semantic_change", 0) == 1)

    # Test 6: Parse VisitAll domain (minimal domain - 1 action)
    visitall_pddl = VISITALL_DOMAIN.read_text(encoding="utf-8")
    parsed_va = parse_domain(visitall_pddl)
    test("Parse VisitAll domain", len(parsed_va["actions"]) >= 1,
         f"Found {len(parsed_va['actions'])} actions: {list(parsed_va['actions'].keys())}")


# =====================================================================
# Full Pipeline Integration Tests
# =====================================================================

def test_full_pipeline():
    print("\n" + "=" * 60)
    print("FULL PIPELINE: Integration Tests")
    print("=" * 60)

    barman_pddl = BARMAN_DOMAIN.read_text(encoding="utf-8")

    # Test 1: Valid reordered domain (skip Docker)
    lines = barman_pddl.split("\n")
    action_starts = [i for i, l in enumerate(lines) if "(:action" in l.lower()]
    if len(action_starts) >= 2:
        start1, start2 = action_starts[0], action_starts[1]
        end2 = action_starts[2] if len(action_starts) > 2 else len(lines)
        block1 = lines[start1:start2]
        block2 = lines[start2:end2]
        reordered_lines = lines[:start1] + block2 + block1 + lines[end2:]
        reordered = "\n".join(reordered_lines)
        mock_response = f"```pddl\n{reordered}\n```"

        result = validate_domain(
            raw_llm_response=mock_response,
            original_domain_path=BARMAN_DOMAIN,
            problem_file_path=BARMAN_INSTANCE,
            skip_docker=True,
        )
        test("Full pipeline: reordered domain -> VALID", result.status == "VALID")

    # Test 2: Empty response -> extraction_failed
    result = validate_domain(
        raw_llm_response="I don't know how to do that.",
        original_domain_path=BARMAN_DOMAIN,
        problem_file_path=BARMAN_INSTANCE,
        skip_docker=True,
    )
    test("Full pipeline: garbage -> REJECTED (extraction_failed)",
         result.status == "REJECTED" and result.reason == "extraction_failed")

    # Test 3: Identical domain -> no_transformation
    result = validate_domain(
        raw_llm_response=barman_pddl,
        original_domain_path=BARMAN_DOMAIN,
        problem_file_path=BARMAN_INSTANCE,
        skip_docker=True,
    )
    test("Full pipeline: identical domain -> REJECTED (no_transformation)",
         result.status == "REJECTED" and result.reason == "no_transformation")

    # Test 4: Semantic change -> INVALID
    injected = barman_pddl.replace(
        "(:predicates",
        "(:predicates\n    (fake-predicate ?x - object)"
    )
    result = validate_domain(
        raw_llm_response=injected,
        original_domain_path=BARMAN_DOMAIN,
        problem_file_path=BARMAN_INSTANCE,
        skip_docker=True,
    )
    test("Full pipeline: added predicate -> INVALID (semantic_change_detected)",
         result.status == "INVALID" and result.reason == "semantic_change_detected")


# =====================================================================
# Main
# =====================================================================

def main():
    with_docker = "--with-docker" in sys.argv

    print("=" * 60)
    print("VALIDATION PIPELINE TEST SUITE")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Docker tests: {'ENABLED' if with_docker else 'DISABLED (use --with-docker)'}")
    print("=" * 60)

    # Verify benchmark files exist
    if not BARMAN_DOMAIN.exists():
        print(f"\n[ERROR] Barman domain not found at {BARMAN_DOMAIN}")
        sys.exit(1)
    if not BARMAN_INSTANCE.exists():
        print(f"\n[ERROR] Barman instance not found at {BARMAN_INSTANCE}")
        sys.exit(1)
    if not VISITALL_DOMAIN.exists():
        print(f"\n[ERROR] VisitAll domain not found at {VISITALL_DOMAIN}")
        sys.exit(1)

    # Run all test stages
    test_v1()
    test_v2(with_docker)
    test_v3()
    test_v4()
    test_full_pipeline()

    # Summary
    total = PASSED + FAILED + SKIPPED
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    print(f"  PASSED:  {PASSED}")
    print(f"  FAILED:  {FAILED}")
    print(f"  SKIPPED: {SKIPPED}")
    print(f"  TOTAL:   {total}")
    print("=" * 60)

    if FAILED > 0:
        print("\nSome tests FAILED. Review output above.")
        sys.exit(1)
    else:
        print("\nAll tests PASSED!")
        sys.exit(0)


if __name__ == "__main__":
    main()
