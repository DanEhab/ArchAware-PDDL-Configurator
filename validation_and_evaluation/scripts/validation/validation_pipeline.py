"""
Validation Pipeline Orchestrator
==================================
Chains all 4 validation stages together into a single function.

Production Usage (real experiment run):
    from validation_pipeline import validate_domain, record_validation

    result = validate_domain(
        raw_llm_response=llm_output,
        original_domain_path=Path("benchmarks/barman/domain.pddl"),
        problem_file_path=Path("benchmarks/barman/instances/instance-01.pddl"),
    )

    record_validation(
        result=result,
        stage="general_prompt",
        model="gpt-5.4",
        domain="barman",
        run_id="run-01",
        project_root=Path("."),
    )

Output structure (production):
    results/<stage>/<model>/<domain>/validation/
        <domain>__<model>__<stage>__<run_id>.validation.json
    validation_and_evaluation/data/production/
        pddl_diff_metrics.csv   (one row per validated domain)

Pipeline flow:
    LLM Raw Response
      -> V1: PDDL Extraction        -> REJECTED (extraction_failed)
      -> V2: Syntactic Validation    -> REJECTED (syntactic_error)
      -> V3: Identity Check          -> REJECTED (no_transformation)
      -> V4: Semantic Equivalence    -> INVALID  (semantic_change_detected)
      -> VALID (proceed to planner)
"""

import csv
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from .v1_extraction import extract_pddl_from_response
from .v2_syntactic_validation import validate_with_val, check_docker_available
from .v3_identity_check import is_identical_to_original
from .v4_semantic_equivalence import check_semantic_equivalence

# Logger
logger = logging.getLogger("validation_pipeline")

# =====================================================================
# Production CSV Column Definitions
# =====================================================================
# These are the columns written to pddl_diff_metrics.csv for real runs.
# No test_id, test_description, expected_verdict, or pass_fail —
# those exist only in the test suite.

PRODUCTION_CSV_HEADER = [
    # ── Experiment identifiers ──
    "domain",
    "model",
    "stage",
    "run_id",
    # ── Pipeline verdict ──
    "validation_status",        # VALID | REJECTED | INVALID
    "rejection_reason",         # null | extraction_failed | syntactic_error | no_transformation | semantic_change_detected
    "failed_stage",             # null | V1 | V2 | V3 | V4
    # ── V4 semantic diff flags (binary 0/1) ──
    "has_semantic_change",
    "req_semantic_change",      "req_reordered",
    "type_semantic_change",     "type_reordered",
    "pred_semantic_change",     "pred_reordered",
    "func_semantic_change",     "func_reordered",
    "actions_semantic_change",  "actions_reordered",
    "params_semantic_change",   "params_reordered",
    "pre_semantic_change",      "pre_reordered",
    "eff_add_semantic_change",  "eff_add_reordered",
    "eff_del_semantic_change",  "eff_del_reordered",
    # ── File references ──
    "json_report_path",
    # ── Metadata ──
    "timestamp",
    "extracted_pddl_length",
]


# =====================================================================
# Validation Result Dataclass
# =====================================================================

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

    # Which stage produced the verdict (V1, V2, V3, V4, or None if VALID)
    failed_stage: Optional[str] = None

    # The extracted PDDL string (empty if V1 failed)
    extracted_pddl: str = ""

    # VAL tool stderr output (for debugging V2 failures)
    val_output: str = ""

    # V4 results: diff features and details
    diff_features: Dict[str, int] = field(default_factory=dict)
    diff_details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-serializable dictionary (basic)."""
        return {
            "status": self.status,
            "reason": self.reason,
            "failed_stage": self.failed_stage,
            "extracted_pddl_length": len(self.extracted_pddl),
            "val_output": self.val_output[:500] if self.val_output else "",
            "diff_features": self.diff_features,
        }

    def to_production_dict(
        self,
        domain: str,
        model: str,
        stage: str,
        run_id: str,
    ) -> Dict[str, Any]:
        """
        Convert to a full production JSON report with experiment context.

        This is what gets saved to the JSON file for real runs.
        """
        return {
            # ── Experiment context ──
            "domain": domain,
            "model": model,
            "stage": stage,
            "run_id": run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            # ── Pipeline verdict ──
            "validation_status": self.status,
            "rejection_reason": self.reason,
            "failed_stage": self.failed_stage,
            # ── V4 detailed analysis ──
            "diff_features": self.diff_features,
            "diff_details": self.diff_details,
            # ── Diagnostics ──
            "extracted_pddl_length": len(self.extracted_pddl),
            "val_output": self.val_output[:1000] if self.val_output else "",
        }


# =====================================================================
# Core Validation Pipeline
# =====================================================================

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


# =====================================================================
# Production Output: JSON Report
# =====================================================================

def save_validation_json(
    result: ValidationResult,
    domain: str,
    model: str,
    stage: str,
    run_id: str,
    project_root: Path,
) -> Path:
    """
    Save a validation result as a production JSON report.

    File naming convention:
        <domain>__<model>__<stage>__<run_id>.validation.json

    Saved to:
        results/<stage>/<model>/<domain>/validation/

    Args:
        result: The ValidationResult from validate_domain().
        domain: Domain name (e.g., "barman").
        model: Model name (e.g., "gpt-5.4").
        stage: Experiment stage (e.g., "general_prompt", "arch_aware").
        run_id: Run identifier (e.g., "run-01").
        project_root: Path to the project root directory.

    Returns:
        Path to the saved JSON file.
    """
    # Build output path
    output_dir = project_root / "results" / stage / model / domain / "validation"
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{domain}__{model}__{stage}__{run_id}.validation.json"
    json_path = output_dir / filename

    # Build production report
    report = result.to_production_dict(domain, model, stage, run_id)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.info(f"JSON report saved to {json_path}")
    return json_path


# =====================================================================
# Production Output: CSV Row
# =====================================================================

def append_validation_csv(
    result: ValidationResult,
    domain: str,
    model: str,
    stage: str,
    run_id: str,
    json_report_path: Path,
    project_root: Path,
) -> Path:
    """
    Append a validation result as a row in the production CSV.

    CSV location:
        validation_and_evaluation/data/production/pddl_diff_metrics.csv

    Creates the CSV with header if it doesn't exist yet.

    Args:
        result: The ValidationResult from validate_domain().
        domain, model, stage, run_id: Experiment identifiers.
        json_report_path: Path to the associated JSON report.
        project_root: Path to the project root directory.

    Returns:
        Path to the CSV file.
    """
    csv_dir = project_root / "validation_and_evaluation" / "data" / "production"
    csv_dir.mkdir(parents=True, exist_ok=True)
    csv_path = csv_dir / "pddl_diff_metrics.csv"

    # Check if file exists (to decide whether to write header)
    write_header = not csv_path.exists()

    features = result.diff_features

    row = {
        # ── Experiment identifiers ──
        "domain": domain,
        "model": model,
        "stage": stage,
        "run_id": run_id,
        # ── Pipeline verdict ──
        "validation_status": result.status,
        "rejection_reason": result.reason or "",
        "failed_stage": result.failed_stage or "",
        # ── V4 diff flags ──
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
        # ── File reference ──
        "json_report_path": str(json_report_path.relative_to(project_root)),
        # ── Metadata ──
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "extracted_pddl_length": len(result.extracted_pddl),
    }

    with csv_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=PRODUCTION_CSV_HEADER)
        if write_header:
            writer.writeheader()
        writer.writerow(row)

    logger.info(f"CSV row appended to {csv_path}")
    return csv_path


# =====================================================================
# Production Convenience: Combined Record Function
# =====================================================================

def record_validation(
    result: ValidationResult,
    stage: str,
    model: str,
    domain: str,
    run_id: str,
    project_root: Path,
) -> Dict[str, Path]:
    """
    One-call function to save both the JSON report and append the CSV row.

    This is the main entry point for recording validation results
    during a real experiment run.

    Usage:
        result = validate_domain(...)
        paths = record_validation(
            result=result,
            stage="general_prompt",
            model="gpt-5.4",
            domain="barman",
            run_id="run-01",
            project_root=Path("."),
        )
        print(paths["json"])  # results/general_prompt/gpt-5.4/barman/validation/...
        print(paths["csv"])   # validation_and_evaluation/data/production/pddl_diff_metrics.csv

    Also saves the extracted PDDL to the results directory if extraction succeeded.

    Returns:
        Dict with keys "json", "csv", and optionally "extracted_pddl".
    """
    paths = {}

    # 1. Save JSON report
    json_path = save_validation_json(
        result, domain, model, stage, run_id, project_root
    )
    paths["json"] = json_path

    # 2. Save extracted PDDL (if V1 passed)
    if result.extracted_pddl:
        pddl_dir = project_root / "results" / stage / model / domain
        pddl_dir.mkdir(parents=True, exist_ok=True)
        pddl_path = pddl_dir / f"{domain}__{model}__{stage}__{run_id}.pddl"
        pddl_path.write_text(result.extracted_pddl, encoding="utf-8")
        paths["extracted_pddl"] = pddl_path
        logger.info(f"Extracted PDDL saved to {pddl_path}")

    # 3. Append CSV row
    csv_path = append_validation_csv(
        result, domain, model, stage, run_id, json_path, project_root
    )
    paths["csv"] = csv_path

    return paths

