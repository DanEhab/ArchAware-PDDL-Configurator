"""
Stage V4: Semantic Equivalence Check
======================================
The critical validation step that ensures the LLM has ONLY reordered
elements and has not added, removed, or modified any domain components.

Based on Eli's validator.py (PDDL Domain Diff), refactored into a
clean function interface for the ArchAware pipeline.

For each PDDL component, elements are extracted from both the original
and candidate domains, then compared as UNORDERED SETS:

  - :requirements   -- list of requirement flags
  - :types          -- list of type declarations
  - :predicates     -- list of predicate signatures
  - Action names    -- list of action identifiers
  - Per action:
      - :parameters     -- parameter declarations
      - :precondition   -- atomic formulas (after flattening (and ...))
      - add-effects     -- positive effect atoms
      - delete-effects  -- (not ...) effect atoms

If set(original) == set(candidate) for EVERY component:
  -> VALID (only ordering changed, semantics preserved)

If any set differs:
  -> INVALID (semantic_change_detected)

Additionally, ordered list comparison is performed for logging
which specific reorderings occurred.

Output artifacts:
  - diff_features: dict of binary flags (has_semantic_change, *_reordered, etc.)
  - diff_details: full structural comparison (JSON-serializable)
"""

import re
from collections import defaultdict
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass, field


# =====================================================================
# Utility Functions
# =====================================================================

def strip_comments(text: str) -> str:
    """Remove PDDL comment lines (starting with ;)."""
    return re.sub(r";.*", "", text)


def norm(expr: str) -> str:
    """Normalise whitespace in a PDDL expression."""
    return re.sub(r"\s+", " ", expr.strip())


def split_top_level(block: str) -> List[str]:
    """
    Split a PDDL block into its top-level parenthesised sub-expressions.

    For example, given:
      (pred1 ?x) (pred2 ?x ?y) (pred3 ?z)
    Returns:
      ['(pred1 ?x)', '(pred2 ?x ?y)', '(pred3 ?z)']
    """
    out, depth, start = [], 0, None
    for i, ch in enumerate(block):
        if ch == "(":
            if depth == 0:
                start = i
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0 and start is not None:
                out.append(block[start : i + 1].strip())
    return out


def flatten_conjunction(expr: str) -> List[str]:
    """
    Flatten an (and ...) conjunction into its individual atoms.
    If the expression is not a conjunction, return it as a single-element list.
    """
    expr = expr.strip()
    if expr.lower().startswith("(and"):
        return split_top_level(expr[4:])
    return [expr] if expr else []


def canonicalise(exprs: List[str]) -> List[str]:
    """Sort and normalise a list of expressions for comparison."""
    return sorted(norm(e) for e in exprs)


# =====================================================================
# PDDL Domain Parser (parenthesis-balanced, no fragile regex)
# =====================================================================


def extract_balanced_block(text: str, keyword: str) -> str:
    """
    Find a keyword (e.g. ':predicates') in the text, then extract the
    balanced parenthesised block that contains it.

    For example, in:
      (:predicates (pred1 ?x) (pred2 ?y))
    With keyword ':predicates', returns the content inside:
      '(pred1 ?x) (pred2 ?y)'

    Works by finding the keyword, then scanning backwards for the
    opening '(' and forward for the matching close ')'.
    """
    m = re.search(keyword, text, flags=re.I)
    if not m:
        return ""

    # Find the opening paren -- it's either right before the keyword
    # (e.g., "(:predicates ...)" ) or at the keyword's start
    # Walk backwards from keyword to find the opening (
    open_pos = None
    for i in range(m.start(), -1, -1):
        if text[i] == "(":
            open_pos = i
            break

    if open_pos is None:
        return ""

    # Now find the matching close paren
    depth = 0
    for i in range(open_pos, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                # Return content after the keyword, before the closing paren
                content_start = m.end()
                return text[content_start:i].strip()
    return ""


def parse_types_block(text: str) -> List[str]:
    """
    Parse the :types block, handling both parenthesised and
    flat 'type1 type2 - parent' style declarations.
    """
    text = text.strip()
    if not text:
        return []

    # Check if types are parenthesised
    if "(" in text:
        return [norm(x) for x in split_top_level(text)]

    # Handle flat style: "type1 type2 - parent type3 - parent2"
    declarations = []
    parts = re.split(r"\s*-\s*", text)
    if len(parts) > 1:
        for i in range(len(parts) - 1):
            types = parts[i].split()
            parent = parts[i + 1].split()[0] if parts[i + 1].strip() else ""
            for t in types:
                t = t.strip()
                if t:
                    declarations.append(norm(f"{t} - {parent}") if parent else norm(t))
            if parts[i + 1].strip():
                remaining = parts[i + 1].split()[1:]
                parts[i + 1] = " ".join(remaining)
    else:
        declarations = [norm(t) for t in text.split() if t.strip()]

    return declarations


def extract_all_actions(text: str) -> Dict[str, Dict]:
    """
    Extract all (:action ...) blocks from PDDL text using
    parenthesis-balanced parsing (no regex).

    Returns a dict mapping action_name -> {params, pre, add, del}
    """
    actions = {}
    search_from = 0

    while True:
        # Find next (:action ...)
        action_match = re.search(r"\(:action\s+", text[search_from:], re.I)
        if not action_match:
            break

        action_start = search_from + action_match.start()

        # Find the balanced end of this action block
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
            break

        action_block = text[action_start:action_end]
        search_from = action_end

        # Extract action name
        name_match = re.search(r"\(:action\s+([^\s()]+)", action_block, re.I)
        if not name_match:
            continue
        action_name = name_match.group(1)

        # Extract :parameters
        params_match = re.search(r":parameters\s*\(([^()]*)\)", action_block, re.I)
        params_raw = params_match.group(1) if params_match else ""

        # Extract :precondition (balanced)
        pre_raw = ""
        pre_match = re.search(r":precondition\s*", action_block, re.I)
        if pre_match:
            pre_start = pre_match.end()
            # Find the start of the next keyword or the precondition block
            # Skip whitespace to find the opening paren
            while pre_start < len(action_block) and action_block[pre_start] in " \t\n\r":
                pre_start += 1
            if pre_start < len(action_block) and action_block[pre_start] == "(":
                depth = 0
                for i in range(pre_start, len(action_block)):
                    if action_block[i] == "(":
                        depth += 1
                    elif action_block[i] == ")":
                        depth -= 1
                        if depth == 0:
                            pre_raw = action_block[pre_start:i + 1]
                            break

        # Extract :effect (balanced)
        eff_raw = ""
        eff_match = re.search(r":effect\s*", action_block, re.I)
        if eff_match:
            eff_start = eff_match.end()
            while eff_start < len(action_block) and action_block[eff_start] in " \t\n\r":
                eff_start += 1
            if eff_start < len(action_block) and action_block[eff_start] == "(":
                depth = 0
                for i in range(eff_start, len(action_block)):
                    if action_block[i] == "(":
                        depth += 1
                    elif action_block[i] == ")":
                        depth -= 1
                        if depth == 0:
                            eff_raw = action_block[eff_start:i + 1]
                            break

        # Parse preconditions (flatten AND)
        pre_list = [norm(x) for x in flatten_conjunction(pre_raw)] if pre_raw else []

        # Parse effects: separate add and delete effects
        add_list, del_list = [], []
        if eff_raw:
            for eff in flatten_conjunction(eff_raw):
                eff_n = norm(eff)
                if re.match(r"\(not\s", eff, re.I):
                    del_list.append(eff_n)
                else:
                    add_list.append(eff_n)

        actions[action_name] = {
            "params": params_raw.split(),
            "pre": pre_list,
            "add": add_list,
            "del": del_list,
        }

    return actions


def parse_domain(pddl_text: str) -> Dict[str, Any]:
    """
    Parse a PDDL domain string into a structured dictionary.

    Returns:
        Dict with keys: requirements, types, predicates, actions, functions
        where actions is a dict mapping action_name -> {params, pre, add, del}
    """
    txt = strip_comments(pddl_text)

    # Requirements
    req_match = re.search(r":requirements\s+([^)]+)\)", txt, re.I)
    req_list = req_match.group(1).split() if req_match else []

    # Types
    typ_raw = extract_balanced_block(txt, r":types")
    types_list = parse_types_block(typ_raw) if typ_raw else []

    # Predicates
    pred_raw = extract_balanced_block(txt, r":predicates")
    pred_list = (
        [norm(x) for x in split_top_level(pred_raw)] if pred_raw else []
    )

    # Functions (for domains that use :action-costs)
    func_raw = extract_balanced_block(txt, r":functions")
    func_list = (
        [norm(x) for x in split_top_level(func_raw)] if func_raw else []
    )

    # Actions (robust parenthesis-balanced extraction)
    actions = extract_all_actions(txt)

    return {
        "requirements": req_list,
        "types": types_list,
        "predicates": pred_list,
        "functions": func_list,
        "actions": actions,
    }


# =====================================================================
# Semantic Equivalence Comparison
# =====================================================================

@dataclass
class SemanticResult:
    """Result of the semantic equivalence check."""
    is_equivalent: bool
    has_semantic_change: bool
    diff_features: Dict[str, int] = field(default_factory=dict)
    diff_details: Dict[str, Any] = field(default_factory=dict)


def compute_diff_features(orig: Dict, candidate: Dict) -> Dict[str, int]:
    """
    Compare original and candidate domain structures.
    Returns a dictionary of binary flags indicating what changed.

    Flags:
      - has_semantic_change: 1 if ANY semantic change detected
      - *_semantic_change: 1 if that component had elements added/removed
      - *_reordered: 1 if that component's elements are the same but reordered
    """
    f: Dict[str, int] = defaultdict(int)

    def cmp_list(a, b, prefix):
        """Compare two lists: check set equality, then order."""
        set_a, set_b = set(a), set(b)
        if set_a != set_b:
            f[f"{prefix}_semantic_change"] = 1
        elif list(a) != list(b):
            f[f"{prefix}_reordered"] = 1

    # Top-level comparisons
    cmp_list(orig["requirements"], candidate["requirements"], "req")
    cmp_list(orig["types"],        candidate["types"],         "type")
    cmp_list(orig["predicates"],   candidate["predicates"],    "pred")
    cmp_list(orig.get("functions", []), candidate.get("functions", []), "func")
    cmp_list(list(orig["actions"]), list(candidate["actions"]), "actions")

    # Per-action comparisons (only for actions that exist in both)
    shared_actions = set(orig["actions"]) & set(candidate["actions"])

    def cmp_action_list(key, prefix):
        sem, reordered = 0, 0
        for act in shared_actions:
            a = orig["actions"][act][key]
            b = candidate["actions"][act][key]
            if set(a) != set(b):
                sem = 1
            elif list(a) != list(b):
                reordered = 1
        if sem:
            f[f"{prefix}_semantic_change"] = 1
        elif reordered:
            f[f"{prefix}_reordered"] = 1

    for key, prefix in [
        ("params", "params"),
        ("pre",    "pre"),
        ("add",    "eff_add"),
        ("del",    "eff_del"),
    ]:
        cmp_action_list(key, prefix)

    # Master flag
    f["has_semantic_change"] = 1 if any(
        v for k, v in f.items() if k.endswith("_semantic_change")
    ) else 0

    return dict(f)


def compute_diff_details(orig: Dict, candidate: Dict) -> Dict[str, Any]:
    """
    Build a detailed diff report showing exactly what changed.
    Returns a JSON-serializable dictionary.
    """
    details = {"semantic": [], "syntactic": []}

    def record(kind, a, b, is_semantic=False):
        """Record a diff entry."""
        can_a, can_b = canonicalise(a), canonicalise(b)
        if can_a != can_b:
            entry = {
                "type": f"{kind}-set",
                "original": a,
                "candidate": b,
                "added": sorted(set(b) - set(a)),
                "removed": sorted(set(a) - set(b)),
            }
            details["semantic" if is_semantic else "syntactic"].append(entry)
        elif a != b:
            details["syntactic"].append({
                "type": f"{kind}-order",
                "original": a,
                "candidate": b,
            })

    # Top-level diffs
    record("requirements", orig["requirements"], candidate["requirements"], is_semantic=True)
    record("types",        orig["types"],        candidate["types"],        is_semantic=True)
    record("predicates",   orig["predicates"],   candidate["predicates"],   is_semantic=True)
    record("functions",    orig.get("functions", []), candidate.get("functions", []), is_semantic=True)
    record("actions",      list(orig["actions"]), list(candidate["actions"]), is_semantic=True)

    # Per-action diffs
    for act in set(orig["actions"]) & set(candidate["actions"]):
        A = orig["actions"][act]
        B = candidate["actions"][act]
        record(f"{act}-params",       A["params"], B["params"])
        record(f"{act}-precondition", A["pre"],    B["pre"])
        record(f"{act}-eff-add",      A["add"],    B["add"], is_semantic=True)
        record(f"{act}-eff-del",      A["del"],    B["del"], is_semantic=True)

    return details


def check_semantic_equivalence(
    candidate_pddl: str,
    original_pddl: str,
) -> SemanticResult:
    """
    Check semantic equivalence between original and candidate domains.

    This is the main entry point for Stage V4.

    Args:
        candidate_pddl: The extracted PDDL from the LLM response.
        original_pddl: The original domain PDDL content.

    Returns:
        SemanticResult with equivalence verdict, features, and details.
    """
    orig = parse_domain(original_pddl)
    cand = parse_domain(candidate_pddl)

    features = compute_diff_features(orig, cand)
    details = compute_diff_details(orig, cand)

    has_semantic_change = features.get("has_semantic_change", 0) == 1

    return SemanticResult(
        is_equivalent=not has_semantic_change,
        has_semantic_change=has_semantic_change,
        diff_features=features,
        diff_details=details,
    )
