"""
Comprehensive Stage V4 Semantic Equivalence Test Suite
=======================================================
This script performs exhaustive testing of the V4 semantic equivalence
checker across ALL 5 benchmark domains with 26 distinct test scenarios.

For each test:
  1. A specific alteration is applied to the original domain PDDL
  2. The altered PDDL is validated through V4
  3. A row is written to validation_and_evaluation/data/v4_tests/pddl_diff_metrics.csv
  4. A JSON structural report is saved to validation_and_evaluation/data/v4_tests/diffs/<domain>/

Test Categories:
  T01-T09: Reordering-only scenarios (should be VALID -> no semantic change)
  T10-T26: Semantic change scenarios   (should be INVALID -> semantic change detected)

Naming convention for JSON reports:
  <domain>__<test_id>__<description>.details.json

Example:
  barman__T01__reorder_actions.details.json
  depots__T05__reorder_preconditions.details.json

Usage:
    python test_v4_comprehensive.py

Author: Daniel (auto-generated for thesis pipeline)
"""

import sys
import csv
import json
import re
import copy
from pathlib import Path
from dataclasses import dataclass
from typing import Callable, Optional

# ── Setup paths ──
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from v4_semantic_equivalence import (
    parse_domain,
    check_semantic_equivalence,
    compute_diff_features,
    compute_diff_details,
    norm,
)

# ── Output directories ──
OUTPUT_DIR = SCRIPT_DIR.parent / "data" / "v4_tests"
DIFFS_DIR = OUTPUT_DIR / "diffs"
CSV_PATH = OUTPUT_DIR / "pddl_diff_metrics.csv"

# ── Domains ──
DOMAINS = {
    "barman":          PROJECT_ROOT / "benchmarks" / "barman" / "domain.pddl",
    "depots":          PROJECT_ROOT / "benchmarks" / "depots" / "domain.pddl",
    "ricochet-robots": PROJECT_ROOT / "benchmarks" / "ricochet-robots" / "domain.pddl",
    "snake":           PROJECT_ROOT / "benchmarks" / "snake" / "domain.pddl",
    "visitall":        PROJECT_ROOT / "benchmarks" / "visitall" / "domain.pddl",
}

# ── CSV header ──
CSV_HEADER = [
    "domain", "test_id", "test_description", "expected_verdict",
    "actual_verdict", "pass_fail",
    "has_semantic_change",
    "req_semantic_change",    "req_reordered",
    "type_semantic_change",   "type_reordered",
    "pred_semantic_change",   "pred_reordered",
    "func_semantic_change",   "func_reordered",
    "actions_semantic_change", "actions_reordered",
    "params_semantic_change", "params_reordered",
    "pre_semantic_change",    "pre_reordered",
    "eff_add_semantic_change", "eff_add_reordered",
    "eff_del_semantic_change", "eff_del_reordered",
    "json_report_path",
]

# ── Tracking ──
PASSED = 0
FAILED = 0
RESULTS = []


# =====================================================================
# Domain Alteration Functions
# =====================================================================
# Each function takes the original PDDL text and returns the altered text.
# They are designed to be domain-agnostic (work on any of the 5 domains).

def alter_reorder_actions(pddl: str) -> str:
    """T01: Reorder action blocks -- swap first two actions."""
    lines = pddl.split("\n")
    starts = [i for i, l in enumerate(lines) if re.match(r"\s*\(:action\s+", l, re.I)]
    if len(starts) < 2:
        return pddl  # Can't swap with only 1 action
    s1, s2 = starts[0], starts[1]
    e2 = starts[2] if len(starts) > 2 else len(lines)
    block1 = lines[s1:s2]
    block2 = lines[s2:e2]
    return "\n".join(lines[:s1] + block2 + block1 + lines[e2:])


def alter_reorder_predicates(pddl: str) -> str:
    """T02: Reorder predicate declarations -- reverse order of top-level predicates.
    Uses balanced parenthesis extraction to avoid corrupting the PDDL."""
    # Find the (:predicates ...) block
    m = re.search(r"\(:predicates", pddl, re.I)
    if not m:
        return pddl
    # Find balanced block
    block_start = m.start()
    depth = 0
    block_end = None
    for i in range(block_start, len(pddl)):
        if pddl[i] == "(":
            depth += 1
        elif pddl[i] == ")":
            depth -= 1
            if depth == 0:
                block_end = i + 1
                break
    if block_end is None:
        return pddl

    # Extract inner content after (:predicates
    inner_start = m.end()
    inner = pddl[inner_start:block_end - 1]  # Exclude outer closing paren

    # Split into individual predicate S-expressions
    from v4_semantic_equivalence import split_top_level
    preds = split_top_level(inner)
    if len(preds) < 2:
        return pddl

    # Reverse order
    preds_reversed = list(reversed(preds))
    new_inner = "\n                ".join(preds_reversed)
    new_block = "(:predicates " + new_inner + ")"
    return pddl[:block_start] + new_block + pddl[block_end:]


def alter_reorder_requirements(pddl: str) -> str:
    """T03: Reorder :requirements flags -- reverse the order."""
    def replacer(m):
        flags = m.group(1).split()
        flags.reverse()
        return "(:requirements " + " ".join(flags) + ")"
    return re.sub(r"\(:requirements\s+([^)]+)\)", replacer, pddl, count=1, flags=re.I)


def alter_reorder_types(pddl: str) -> str:
    """T04: Reorder type declaration lines within the :types block.
    Uses balanced extraction to avoid corrupting the PDDL."""
    m = re.search(r"\(:types", pddl, re.I)
    if not m:
        return pddl
    block_start = m.start()
    depth = 0
    block_end = None
    for i in range(block_start, len(pddl)):
        if pddl[i] == "(":
            depth += 1
        elif pddl[i] == ")":
            depth -= 1
            if depth == 0:
                block_end = i + 1
                break
    if block_end is None:
        return pddl

    inner = pddl[m.end():block_end - 1].strip()
    # Split by newlines and reverse non-empty lines
    parts = [l.strip() for l in inner.split("\n") if l.strip()]
    if len(parts) < 2:
        return pddl
    parts_reversed = list(reversed(parts))
    new_inner = "\n          ".join(parts_reversed)
    new_block = "(:types " + new_inner + ")"
    return pddl[:block_start] + new_block + pddl[block_end:]


def alter_reorder_preconditions(pddl: str) -> str:
    """T05: Reorder preconditions within the first action that has (and ...).
    Uses balanced parenthesis extraction."""
    text = pddl
    action_matches = list(re.finditer(r"\(:action\s+", text, re.I))
    for am in action_matches:
        # Find the balanced end of this action
        action_start = am.start()
        depth = 0
        action_end = None
        for i in range(action_start, len(text)):
            if text[i] == "(":
                depth += 1
            elif text[i] == ")":
                depth -= 1
                if depth == 0:
                    action_end = i + 1
                    break
        if action_end is None:
            continue

        action_block = text[action_start:action_end]

        # Find :precondition (and ...)
        pre_m = re.search(r":precondition\s*", action_block, re.I)
        if not pre_m:
            continue

        # Find the balanced precondition expression
        ps = pre_m.end()
        while ps < len(action_block) and action_block[ps] in " \t\n\r":
            ps += 1
        if ps >= len(action_block) or action_block[ps] != "(":
            continue

        depth = 0
        pe = None
        for i in range(ps, len(action_block)):
            if action_block[i] == "(":
                depth += 1
            elif action_block[i] == ")":
                depth -= 1
                if depth == 0:
                    pe = i + 1
                    break
        if pe is None:
            continue

        pre_expr = action_block[ps:pe].strip()
        if not pre_expr.lower().startswith("(and"):
            continue

        # Strip comments before parsing to avoid commented-out PDDL
        # being treated as real atoms (e.g., ricochet-robots has
        # commented examples inside preconditions)
        pre_expr_clean = re.sub(r";;.*", "", pre_expr)

        # Split into atoms
        from v4_semantic_equivalence import split_top_level
        inner = pre_expr_clean[4:-1]  # Strip (and ... )
        atoms = split_top_level(inner)
        if len(atoms) < 2:
            continue

        # Reverse atoms
        atoms_reversed = list(reversed(atoms))
        new_pre = "(and " + " ".join(atoms_reversed) + ")"
        new_action = action_block[:ps] + new_pre + action_block[pe:]
        text = text[:action_start] + new_action + text[action_end:]
        return text

    return pddl


def alter_reorder_add_effects(pddl: str) -> str:
    """T06: Reorder add-effects within an action's :effect block."""
    text = pddl
    action_matches = list(re.finditer(r"\(:action\s+", text, re.I))
    for am in action_matches:
        action_block_start = am.start()
        # Find the balanced end of this action
        depth = 0
        action_block_end = None
        for i in range(action_block_start, len(text)):
            if text[i] == "(":
                depth += 1
            elif text[i] == ")":
                depth -= 1
                if depth == 0:
                    action_block_end = i + 1
                    break
        if action_block_end is None:
            continue

        action_block = text[action_block_start:action_block_end]
        eff_m = re.search(r":effect\s*\(\s*and\b", action_block, re.I)
        if not eff_m:
            continue

        eff_start = eff_m.end()
        # Find all effect atoms
        depth = 1
        eff_end = None
        for i in range(eff_start, len(action_block)):
            if action_block[i] == "(":
                depth += 1
            elif action_block[i] == ")":
                depth -= 1
                if depth == 0:
                    eff_end = i
                    break
        if eff_end is None:
            continue

        eff_content = action_block[eff_start:eff_end]
        atoms = []
        atom_depth = 0
        atom_start_pos = None
        for i, ch in enumerate(eff_content):
            if ch == "(":
                if atom_depth == 0:
                    atom_start_pos = i
                atom_depth += 1
            elif ch == ")":
                atom_depth -= 1
                if atom_depth == 0 and atom_start_pos is not None:
                    atoms.append(eff_content[atom_start_pos:i+1])

        if len(atoms) < 2:
            continue

        # Reverse
        atoms_reversed = list(reversed(atoms))
        new_eff = "\n\t\t\t".join(atoms_reversed)
        new_action_block = action_block[:eff_start] + " " + new_eff + action_block[eff_end:]
        text = text[:action_block_start] + new_action_block + text[action_block_end:]
        return text

    return pddl


def alter_reorder_del_effects(pddl: str) -> str:
    """T07: Reorder delete-effects -- swap (not ...) atoms in first action with multiple."""
    text = pddl
    action_matches = list(re.finditer(r"\(:action\s+", text, re.I))
    for am in action_matches:
        action_block_start = am.start()
        depth = 0
        action_block_end = None
        for i in range(action_block_start, len(text)):
            if text[i] == "(":
                depth += 1
            elif text[i] == ")":
                depth -= 1
                if depth == 0:
                    action_block_end = i + 1
                    break
        if action_block_end is None:
            continue

        action_block = text[action_block_start:action_block_end]
        eff_m = re.search(r":effect\s*\(\s*and\b", action_block, re.I)
        if not eff_m:
            continue

        eff_start = eff_m.end()
        depth = 1
        eff_end = None
        for i in range(eff_start, len(action_block)):
            if action_block[i] == "(":
                depth += 1
            elif action_block[i] == ")":
                depth -= 1
                if depth == 0:
                    eff_end = i
                    break
        if eff_end is None:
            continue

        eff_content = action_block[eff_start:eff_end]
        # Find (not ...) atoms
        not_atoms = list(re.finditer(r"\(not\s+", eff_content, re.I))
        if len(not_atoms) < 2:
            continue

        # Swap the first two (not ...) blocks
        # Find balanced end of each
        def find_balanced_end(text, start):
            d = 0
            for i in range(start, len(text)):
                if text[i] == "(":
                    d += 1
                elif text[i] == ")":
                    d -= 1
                    if d == 0:
                        return i + 1
            return len(text)

        s1 = not_atoms[0].start()
        e1 = find_balanced_end(eff_content, s1)
        s2 = not_atoms[1].start()
        e2 = find_balanced_end(eff_content, s2)

        block1 = eff_content[s1:e1]
        block2 = eff_content[s2:e2]

        new_eff = eff_content[:s1] + block2 + eff_content[e1:s2] + block1 + eff_content[e2:]
        new_action_block = action_block[:eff_start] + new_eff + action_block[eff_end:]
        text = text[:action_block_start] + new_action_block + text[action_block_end:]
        return text

    return pddl


def alter_reorder_parameters(pddl: str) -> str:
    """T08: Reorder parameters within an action -- reverse parameter tokens."""
    # Find :parameters (...) and reverse the parameter pairs
    # This swaps typed parameter groups, e.g. ?h - hand ?c - container -> ?c - container ?h - hand
    m = re.search(r"(:parameters\s*\()([^)]+)(\))", pddl, re.I)
    if not m:
        return pddl
    params = m.group(2).strip()
    # Split into individual parameter tokens
    parts = params.split()
    # Group into pairs: [?var, -, type]
    groups = []
    i = 0
    while i < len(parts):
        if i + 2 < len(parts) and parts[i+1] == "-":
            groups.append(f"{parts[i]} {parts[i+1]} {parts[i+2]}")
            i += 3
        else:
            groups.append(parts[i])
            i += 1

    if len(groups) < 2:
        return pddl

    groups.reverse()
    new_params = " ".join(groups)
    return pddl[:m.start(2)] + new_params + pddl[m.end(2):]


def alter_combined_reorder(pddl: str) -> str:
    """T09: Combined reorder -- actions + predicates + requirements."""
    result = alter_reorder_actions(pddl)
    result = alter_reorder_predicates(result)
    result = alter_reorder_requirements(result)
    return result


# === SEMANTIC CHANGE ALTERATIONS (should be INVALID) ===

def alter_add_predicate(pddl: str) -> str:
    """T10: Add a new predicate to the :predicates block."""
    return pddl.replace(
        "(:predicates",
        "(:predicates\n    (injected-fake-predicate ?x)"
    )


def alter_remove_predicate(pddl: str) -> str:
    """T11: Remove the last predicate declaration."""
    lines = pddl.split("\n")
    # Find predicate lines
    pred_lines = []
    in_pred = False
    for i, l in enumerate(lines):
        if ":predicates" in l.lower():
            in_pred = True
        if in_pred:
            stripped = l.strip()
            if stripped.startswith("(") and "?" in stripped and not stripped.startswith("(:"):
                pred_lines.append(i)
            if stripped == ")" and in_pred and len(pred_lines) > 0:
                in_pred = False
                break

    if not pred_lines:
        return pddl

    # Remove the last predicate line
    del lines[pred_lines[-1]]
    return "\n".join(lines)


def alter_add_action(pddl: str) -> str:
    """T12: Add a completely new fake action."""
    fake_action = """
  (:action fake-injected-action
           :parameters (?x)
           :precondition ()
           :effect ())
"""
    # Insert before the closing paren of the domain
    idx = pddl.rfind(")")
    return pddl[:idx] + fake_action + pddl[idx:]


def alter_remove_action(pddl: str) -> str:
    """T13: Remove the last action from the domain."""
    lines = pddl.split("\n")
    starts = [i for i, l in enumerate(lines) if re.match(r"\s*\(:action\s+", l, re.I)]
    if not starts:
        return pddl
    last_start = starts[-1]
    # Find balanced end
    depth = 0
    last_end = last_start
    for i in range(last_start, len(lines)):
        for ch in lines[i]:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    last_end = i + 1
                    break
        if depth == 0:
            break

    return "\n".join(lines[:last_start] + lines[last_end:])


def alter_add_precondition(pddl: str) -> str:
    """T14: Add a fake precondition to the first (and ...) precondition block."""
    m = re.search(r":precondition\s*\(\s*and\b", pddl, re.I)
    if not m:
        return pddl
    insert_pos = m.end()
    return pddl[:insert_pos] + " (injected-pre ?x)" + pddl[insert_pos:]


def alter_remove_precondition(pddl: str) -> str:
    """T15: Remove one precondition from the first action with multiple."""
    text = pddl
    m = re.search(r":precondition\s*\(\s*and\b", text, re.I)
    if not m:
        return text
    start = m.end()
    # Find the first atom inside (and ...)
    atom_start = None
    atom_end = None
    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == "(":
            if depth == 0:
                atom_start = i
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0 and atom_start is not None:
                atom_end = i + 1
                break
    if atom_start is None or atom_end is None:
        return text
    # Remove that atom
    return text[:atom_start] + text[atom_end:]


def alter_add_add_effect(pddl: str) -> str:
    """T16: Add a fake positive effect to the first action's :effect."""
    m = re.search(r":effect\s*\(\s*and\b", pddl, re.I)
    if not m:
        return pddl
    insert_pos = m.end()
    return pddl[:insert_pos] + " (injected-add-effect ?x)" + pddl[insert_pos:]


def alter_remove_add_effect(pddl: str) -> str:
    """T17: Remove a positive (non-not) effect from first action."""
    text = pddl
    m = re.search(r":effect\s*\(\s*and\b", text, re.I)
    if not m:
        return text
    start = m.end()
    # Find first positive atom (not starting with (not )
    depth = 0
    atom_start = None
    atom_end = None
    for i in range(start, len(text)):
        ch = text[i]
        if ch == "(":
            if depth == 0:
                # Check if this is a (not ...) or positive
                remaining = text[i:i+5].lower()
                if not remaining.startswith("(not "):
                    atom_start = i
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0 and atom_start is not None:
                atom_end = i + 1
                break
    if atom_start is None or atom_end is None:
        return text
    return text[:atom_start] + text[atom_end:]


def alter_add_del_effect(pddl: str) -> str:
    """T18: Add a fake delete-effect to the first action's :effect."""
    m = re.search(r":effect\s*\(\s*and\b", pddl, re.I)
    if not m:
        return pddl
    insert_pos = m.end()
    return pddl[:insert_pos] + " (not (injected-del-effect ?x))" + pddl[insert_pos:]


def alter_remove_del_effect(pddl: str) -> str:
    """T19: Remove a (not ...) effect from the first action."""
    text = pddl
    m = re.search(r":effect\s*\(\s*and\b", text, re.I)
    if not m:
        return text
    start = m.end()
    # Find first (not ...) atom
    not_m = re.search(r"\(not\s+", text[start:], re.I)
    if not not_m:
        return text
    not_start = start + not_m.start()
    depth = 0
    not_end = None
    for i in range(not_start, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                not_end = i + 1
                break
    if not_end is None:
        return text
    return text[:not_start] + text[not_end:]


def alter_change_requirement(pddl: str) -> str:
    """T20: Add a fake requirement flag."""
    return re.sub(
        r"\(:requirements\s+([^)]+)\)",
        r"(:requirements \1 :fake-requirement)",
        pddl, count=1, flags=re.I
    )


def alter_add_type(pddl: str) -> str:
    """T21: Add a new type declaration."""
    m = re.search(r"(:types\s+)", pddl, re.I)
    if not m:
        return pddl
    insert_pos = m.end()
    return pddl[:insert_pos] + "injected-type - object\n          " + pddl[insert_pos:]


def alter_remove_type(pddl: str) -> str:
    """T22: Remove the first type line after :types."""
    lines = pddl.split("\n")
    for i, l in enumerate(lines):
        if ":types" in l.lower():
            # Remove the next non-empty line that has type content
            for j in range(i + 1, len(lines)):
                stripped = lines[j].strip()
                if stripped and not stripped.startswith("(:") and stripped != ")":
                    del lines[j]
                    return "\n".join(lines)
    return pddl


def alter_rename_action(pddl: str) -> str:
    """T23: Rename the first action to a different name."""
    m = re.search(r"\(:action\s+([^\s()]+)", pddl, re.I)
    if not m:
        return pddl
    old_name = m.group(1)
    new_name = old_name + "-RENAMED"
    return pddl[:m.start(1)] + new_name + pddl[m.end(1):]


def alter_modify_precondition_text(pddl: str) -> str:
    """T24: Modify a predicate name inside a precondition (change text)."""
    text = pddl
    m = re.search(r":precondition\s*\(\s*and\s*\((\w+)", text, re.I)
    if not m:
        m = re.search(r":precondition\s*\((\w+)", text, re.I)
    if not m:
        return text
    old = m.group(1)
    return text[:m.start(1)] + old + "-MODIFIED" + text[m.end(1):]


def alter_add_parameter(pddl: str) -> str:
    """T25: Add an extra parameter to the first action."""
    m = re.search(r"(:parameters\s*\()([^)]+)(\))", pddl, re.I)
    if not m:
        return pddl
    return pddl[:m.end(2)] + " ?injected-param" + pddl[m.end(2):]


def alter_remove_parameter(pddl: str) -> str:
    """T26: Remove a complete typed parameter group from the first action."""
    m = re.search(r"(:parameters\s*\()([^)]+)(\))", pddl, re.I)
    if not m:
        return pddl
    params = m.group(2).strip().split()
    if len(params) < 2:
        return pddl
    # Group into typed parameter groups: ["?var - type", ...]
    groups = []
    i = 0
    while i < len(params):
        if i + 2 < len(params) and params[i+1] == "-":
            groups.append(f"{params[i]} {params[i+1]} {params[i+2]}")
            i += 3
        else:
            groups.append(params[i])
            i += 1
    if len(groups) < 2:
        return pddl
    # Remove the last complete group
    groups = groups[:-1]
    new_params = " ".join(groups)
    return pddl[:m.start(2)] + new_params + pddl[m.end(2):]


# =====================================================================
# Test Registry
# =====================================================================

@dataclass
class TestCase:
    test_id: str
    description: str
    alter_fn: Callable[[str], str]
    expected_valid: bool  # True = VALID (no semantic change), False = INVALID


TEST_CASES = [
    # === REORDERING-ONLY (should be VALID) ===
    TestCase("T01", "reorder_actions",            alter_reorder_actions,        True),
    TestCase("T02", "reorder_predicates",         alter_reorder_predicates,     True),
    TestCase("T03", "reorder_requirements",       alter_reorder_requirements,   True),
    TestCase("T04", "reorder_types",              alter_reorder_types,          True),
    TestCase("T05", "reorder_preconditions",      alter_reorder_preconditions,  True),
    TestCase("T06", "reorder_add_effects",        alter_reorder_add_effects,    True),
    TestCase("T07", "reorder_del_effects",        alter_reorder_del_effects,    True),
    TestCase("T08", "reorder_parameters",         alter_reorder_parameters,     True),
    TestCase("T09", "combined_reorder_multi",     alter_combined_reorder,       True),

    # === SEMANTIC CHANGES (should be INVALID) ===
    TestCase("T10", "add_predicate",              alter_add_predicate,          False),
    TestCase("T11", "remove_predicate",           alter_remove_predicate,       False),
    TestCase("T12", "add_action",                 alter_add_action,             False),
    TestCase("T13", "remove_action",              alter_remove_action,          False),
    TestCase("T14", "add_precondition",           alter_add_precondition,       False),
    TestCase("T15", "remove_precondition",        alter_remove_precondition,    False),
    TestCase("T16", "add_add_effect",             alter_add_add_effect,         False),
    TestCase("T17", "remove_add_effect",          alter_remove_add_effect,      False),
    TestCase("T18", "add_del_effect",             alter_add_del_effect,         False),
    TestCase("T19", "remove_del_effect",          alter_remove_del_effect,      False),
    TestCase("T20", "change_requirement",         alter_change_requirement,     False),
    TestCase("T21", "add_type",                   alter_add_type,               False),
    TestCase("T22", "remove_type",                alter_remove_type,            False),
    TestCase("T23", "rename_action",              alter_rename_action,          False),
    TestCase("T24", "modify_precondition_text",   alter_modify_precondition_text, False),
    TestCase("T25", "add_parameter",              alter_add_parameter,          False),
    TestCase("T26", "remove_parameter",           alter_remove_parameter,       False),
]


# =====================================================================
# Test Runner
# =====================================================================

def run_single_test(
    domain_name: str,
    original_pddl: str,
    test_case: TestCase,
    csv_writer,
) -> bool:
    """Run a single test case and record results."""
    global PASSED, FAILED

    # Apply alteration
    altered_pddl = test_case.alter_fn(original_pddl)

    # Check if alteration actually changed anything
    if altered_pddl == original_pddl and not test_case.expected_valid:
        # Alteration didn't apply (domain too simple for this test)
        print(f"  [SKIP] {test_case.test_id} {test_case.description} -- alteration not applicable to {domain_name}")
        return True  # Not a failure

    # Run V4
    result = check_semantic_equivalence(altered_pddl, original_pddl)

    # Determine verdict
    actual_valid = result.is_equivalent
    test_pass = (actual_valid == test_case.expected_valid)

    if test_pass:
        PASSED += 1
        status = "PASS"
    else:
        FAILED += 1
        status = "FAIL"

    expected_str = "VALID" if test_case.expected_valid else "INVALID"
    actual_str = "VALID" if actual_valid else "INVALID"

    # Print
    print(f"  [{status}] {test_case.test_id} {test_case.description:35s} "
          f"expected={expected_str:7s} actual={actual_str:7s} "
          f"sem_change={result.diff_features.get('has_semantic_change', 0)}")

    # Save JSON report
    domain_diff_dir = DIFFS_DIR / domain_name
    domain_diff_dir.mkdir(parents=True, exist_ok=True)
    json_filename = f"{domain_name}__{test_case.test_id}__{test_case.description}.details.json"
    json_path = domain_diff_dir / json_filename
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump({
            "domain": domain_name,
            "test_id": test_case.test_id,
            "test_description": test_case.description,
            "expected_verdict": expected_str,
            "actual_verdict": actual_str,
            "pass_fail": status,
            "diff_features": result.diff_features,
            "diff_details": result.diff_details,
        }, jf, indent=2, ensure_ascii=False)

    # Write CSV row
    features = result.diff_features
    row = {col: 0 for col in CSV_HEADER}
    row.update({
        "domain": domain_name,
        "test_id": test_case.test_id,
        "test_description": test_case.description,
        "expected_verdict": expected_str,
        "actual_verdict": actual_str,
        "pass_fail": status,
        "has_semantic_change": features.get("has_semantic_change", 0),
        "req_semantic_change": features.get("req_semantic_change", 0),
        "req_reordered": features.get("req_reordered", 0),
        "type_semantic_change": features.get("type_semantic_change", 0),
        "type_reordered": features.get("type_reordered", 0),
        "pred_semantic_change": features.get("pred_semantic_change", 0),
        "pred_reordered": features.get("pred_reordered", 0),
        "func_semantic_change": features.get("func_semantic_change", 0),
        "func_reordered": features.get("func_reordered", 0),
        "actions_semantic_change": features.get("actions_semantic_change", 0),
        "actions_reordered": features.get("actions_reordered", 0),
        "params_semantic_change": features.get("params_semantic_change", 0),
        "params_reordered": features.get("params_reordered", 0),
        "pre_semantic_change": features.get("pre_semantic_change", 0),
        "pre_reordered": features.get("pre_reordered", 0),
        "eff_add_semantic_change": features.get("eff_add_semantic_change", 0),
        "eff_add_reordered": features.get("eff_add_reordered", 0),
        "eff_del_semantic_change": features.get("eff_del_semantic_change", 0),
        "eff_del_reordered": features.get("eff_del_reordered", 0),
        "json_report_path": str(json_path.relative_to(PROJECT_ROOT)),
    })
    csv_writer.writerow(row)

    return test_pass


def main():
    global PASSED, FAILED

    print("=" * 70)
    print("COMPREHENSIVE V4 SEMANTIC EQUIVALENCE TEST SUITE")
    print(f"Domains: {len(DOMAINS)}")
    print(f"Test cases per domain: {len(TEST_CASES)}")
    print(f"Total tests: {len(DOMAINS) * len(TEST_CASES)}")
    print("=" * 70)
    print(f"\nOutput CSV:  {CSV_PATH.relative_to(PROJECT_ROOT)}")
    print(f"Output JSON: {DIFFS_DIR.relative_to(PROJECT_ROOT)}/<domain>/")
    print()

    # Create output directories
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DIFFS_DIR.mkdir(parents=True, exist_ok=True)

    # Delete old CSV if exists (fresh run)
    if CSV_PATH.exists():
        CSV_PATH.unlink()

    # Open CSV
    with CSV_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_HEADER)
        writer.writeheader()

        # Run all tests for all domains
        for domain_name, domain_path in DOMAINS.items():
            print(f"\n{'='*70}")
            print(f"DOMAIN: {domain_name}")
            print(f"{'='*70}")

            if not domain_path.exists():
                print(f"  [ERROR] Domain file not found: {domain_path}")
                continue

            original_pddl = domain_path.read_text(encoding="utf-8")

            for test_case in TEST_CASES:
                run_single_test(domain_name, original_pddl, test_case, writer)

    # Summary
    total = PASSED + FAILED
    print(f"\n{'='*70}")
    print("TEST RESULTS SUMMARY")
    print(f"{'='*70}")
    print(f"  PASSED:  {PASSED}")
    print(f"  FAILED:  {FAILED}")
    print(f"  TOTAL:   {total}")
    print(f"\n  CSV:  {CSV_PATH.relative_to(PROJECT_ROOT)}")
    print(f"  JSON: {DIFFS_DIR.relative_to(PROJECT_ROOT)}/<domain>/")
    print()

    # List output files
    print(f"{'='*70}")
    print("OUTPUT FILE ORGANIZATION")
    print(f"{'='*70}")
    for domain_name in DOMAINS:
        domain_dir = DIFFS_DIR / domain_name
        if domain_dir.exists():
            json_count = len(list(domain_dir.glob("*.json")))
            print(f"  {domain_dir.relative_to(PROJECT_ROOT)}/  ({json_count} JSON reports)")

    print(f"\n  {CSV_PATH.relative_to(PROJECT_ROOT)} ({total} rows)")
    print(f"{'='*70}")

    if FAILED > 0:
        print("\nSome tests FAILED. Review output above.")
        sys.exit(1)
    else:
        print("\nAll tests PASSED!")
        sys.exit(0)


if __name__ == "__main__":
    main()
