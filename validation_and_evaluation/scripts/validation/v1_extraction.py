"""
Stage V1: PDDL Extraction
==========================
Extracts a valid PDDL domain definition from a raw LLM response.

Based on Eli's extraction.py, adapted for the ArchAware pipeline.

Steps:
  1. Detect and unescape JSON-encoded strings (\\n -> \n)
  2. Strip markdown code fences (```pddl, ```)
  3. Locate the (define ...) keyword
  4. Perform parenthesis balancing to extract the complete S-expression
  5. Strip leading/trailing whitespace

If no balanced (define ...) block is found, extraction fails.
"""

import json
import re


def extract_pddl_from_response(response_text: str) -> str:
    """
    Extract the PDDL domain definition from a raw LLM response string.

    Args:
        response_text: The raw text output from the LLM.

    Returns:
        The extracted PDDL string, or "" if extraction fails.
    """
    if not isinstance(response_text, str) or not response_text.strip():
        return ""

    # Step 1: Unescape JSON-encoded strings
    # Some LLMs return the response wrapped in JSON quotes with escaped newlines
    if response_text.strip().startswith('"') and "\\n" in response_text:
        try:
            response_text = json.loads(response_text)
        except json.JSONDecodeError:
            pass

    # Also handle literal \\n sequences that weren't JSON-decoded
    response_text = response_text.replace("\\n", "\n")

    # Step 2: Strip markdown code fences
    # Handles ```pddl, ```lisp, ```PDDL, plain ```, etc.
    response_text = re.sub(r"```(?:pddl|lisp|PDDL)?", "", response_text)

    # Step 3: Locate (define ...)
    start_idx = response_text.find("(define")
    if start_idx == -1:
        # Also try case-insensitive search as a fallback
        match = re.search(r"\(define", response_text, re.IGNORECASE)
        if match:
            start_idx = match.start()
        else:
            return ""

    pddl_candidate = response_text[start_idx:]

    # Step 4: Parenthesis balancing to extract the complete S-expression
    balance = 0
    end_idx = None
    for i, char in enumerate(pddl_candidate):
        if char == "(":
            balance += 1
        elif char == ")":
            balance -= 1
            if balance == 0:
                end_idx = i + 1
                break

    if end_idx is None:
        # Unbalanced parentheses - extraction fails
        return ""

    # Step 5: Strip whitespace and return
    return pddl_candidate[:end_idx].strip()
