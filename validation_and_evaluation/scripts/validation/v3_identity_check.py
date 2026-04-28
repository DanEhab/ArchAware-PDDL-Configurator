"""
Stage V3: Identity Check (Normalised Comparison)
==================================================
After syntactic validation, this stage checks whether the LLM simply
reproduced the original domain without any transformation.

Both domains are normalised:
  1. Remove all PDDL comments (lines starting with ;)
  2. Collapse all whitespace to single spaces
  3. Strip leading/trailing whitespace

If the normalised candidate is character-for-character identical to
the normalised original, the domain is REJECTED -- the LLM provided
no transformation and the domain has no experimental value.
"""

import re


def normalise_pddl(pddl_text: str) -> str:
    """
    Normalise a PDDL string for identity comparison.

    Steps:
      1. Remove all comment lines (starting with ;)
      2. Collapse all whitespace (spaces, tabs, newlines) to single spaces
      3. Strip leading/trailing whitespace
      4. Lowercase for case-insensitive comparison

    Args:
        pddl_text: Raw PDDL content string.

    Returns:
        Normalised PDDL string.
    """
    # Step 1: Remove comment lines
    text = re.sub(r";.*", "", pddl_text)

    # Step 2: Collapse all whitespace to single spaces
    text = re.sub(r"\s+", " ", text)

    # Step 3: Strip leading/trailing whitespace
    text = text.strip()

    # Step 4: Lowercase for case-insensitive comparison
    text = text.lower()

    return text


def is_identical_to_original(candidate_pddl: str, original_pddl: str) -> bool:
    """
    Check if the candidate domain is identical to the original after
    normalisation.

    Args:
        candidate_pddl: The extracted PDDL from the LLM response.
        original_pddl: The original domain PDDL content.

    Returns:
        True if both normalised forms are identical (meaning the LLM
        did NOT transform anything -- this is a rejection condition).
        False if they differ (the LLM made some change -- proceed to V4).
    """
    return normalise_pddl(candidate_pddl) == normalise_pddl(original_pddl)
