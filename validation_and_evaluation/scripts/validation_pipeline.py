"""
Validation Pipeline Orchestrator
==================================
Chains all 4 validation stages together into a single function.

Usage:
    from validation_pipeline import validate_domain

    result = validate_domain(
        raw_llm_response=llm_output,
        original_domain_path=Path("benchmarks/barman/domain.pddl"),
        problem_file_path=Path("benchmarks/barman/instances/instance-01.pddl"),
    )

    if result.status == "VALID":
        # Proceed to planner execution
        ...

Pipeline flow:
    LLM Raw Response
      -> V1: PDDL Extraction        -> REJECTED (extraction_failed)
      -> V2: Syntactic Validation    -> REJECTED (syntactic_error)
      -> V3: Identity Check          -> REJECTED (no_transformation)
      -> V4: Semantic Equivalence    -> INVALID  (semantic_change_detected)
      -> VALID (proceed to planner)
"""

import json
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from v1_extraction import extract_pddl_from_response
from v2_syntactic_validation import validate_with_val, check_docker_available
from v3_identity_check import is_identical_to_original
from v4_semantic_equivalence import check_semantic_equivalence

# Logger
logger = logging.getLogger("validation_pipeline")


@dataclass
class ValidationResult:
    """Complete result of the 4-stage validation pipeline."""

    # Final verdict: "VALID", "REJECTED", or "INVALID"
    status: str

    # Rejection/invalidity reason (None if VALID):
    #   - "extraction_failed"         (V1)
    #   - "syntactic_error"           (V2)
    #   - "no_transformation"         (V3)
    #   - "semantic_change_detected"  (V4)
    reason: Optional[str] = None

    # Which stage produced the verdict (V1, V2, V3, V4, or PASS)
    failed_stage: Optional[str] = None

    # The extracted PDDL string (empty if V1 failed)
    extracted_pddl: str = ""

    # VAL tool stderr output (for debugging V2 failures)
    val_output: str = ""

    # V4 results: diff features and details
    diff_features: Dict[str, int] = field(default_factory=dict)
    diff_details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-serializable dictionary."""
        return {
            "status": self.status,
            "reason": self.reason,
            "failed_stage": self.failed_stage,
            "extracted_pddl_length": len(self.extracted_pddl),
            "val_output": self.val_output[:500] if self.val_output else "",
            "diff_features": self.diff_features,
        }


def validate_domain(
    raw_llm_response: str,
    original_domain_path: Path,
    problem_file_path: Path,
    skip_docker: bool = False,
) -> ValidationResult:
    """
    Run the full 4-stage validation pipeline on an LLM-generated domain.

    Args:
        raw_llm_response: The raw text output from the LLM.
        original_domain_path: Path to the original domain.pddl file.
        problem_file_path: Path to a problem instance file (for VAL).
        skip_docker: If True, skip Stage V2 (useful for testing without Docker).

    Returns:
        ValidationResult with the pipeline verdict.
    """
    original_pddl = Path(original_domain_path).read_text(encoding="utf-8")

    # ── Stage V1: PDDL Extraction ──
    logger.info("V1: Extracting PDDL from LLM response...")
    extracted = extract_pddl_from_response(raw_llm_response)

    if not extracted:
        logger.warning("V1: REJECTED - extraction_failed")
        return ValidationResult(
            status="REJECTED",
            reason="extraction_failed",
            failed_stage="V1",
        )
    logger.info(f"V1: PASSED - extracted {len(extracted)} chars")

    # ── Stage V2: Syntactic Validation (VAL Tool) ──
    if skip_docker:
        logger.info("V2: SKIPPED (--skip-docker flag)")
    else:
        logger.info("V2: Running VAL syntactic validation...")
        val_result = validate_with_val(
            domain_pddl_str=extracted,
            problem_file_path=str(problem_file_path),
        )
        if not val_result.is_valid:
            logger.warning(
                f"V2: REJECTED - syntactic_error (exit code {val_result.exit_code})"
            )
            return ValidationResult(
                status="REJECTED",
                reason="syntactic_error",
                failed_stage="V2",
                extracted_pddl=extracted,
                val_output=val_result.stderr,
            )
        logger.info("V2: PASSED - VAL returned exit code 0")

    # ── Stage V3: Identity Check ──
    logger.info("V3: Checking for identity (no transformation)...")
    if is_identical_to_original(extracted, original_pddl):
        logger.warning("V3: REJECTED - no_transformation")
        return ValidationResult(
            status="REJECTED",
            reason="no_transformation",
            failed_stage="V3",
            extracted_pddl=extracted,
        )
    logger.info("V3: PASSED - domain differs from original")

    # ── Stage V4: Semantic Equivalence ──
    logger.info("V4: Checking semantic equivalence...")
    sem_result = check_semantic_equivalence(extracted, original_pddl)

    if sem_result.has_semantic_change:
        logger.warning("V4: INVALID - semantic_change_detected")
        return ValidationResult(
            status="INVALID",
            reason="semantic_change_detected",
            failed_stage="V4",
            extracted_pddl=extracted,
            diff_features=sem_result.diff_features,
            diff_details=sem_result.diff_details,
        )

    logger.info("V4: PASSED - semantic equivalence confirmed")
    return ValidationResult(
        status="VALID",
        reason=None,
        failed_stage=None,
        extracted_pddl=extracted,
        diff_features=sem_result.diff_features,
        diff_details=sem_result.diff_details,
    )


def save_validation_report(
    result: ValidationResult,
    output_path: Path,
) -> None:
    """Save a validation result as a JSON report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
    logger.info(f"Report saved to {output_path}")
