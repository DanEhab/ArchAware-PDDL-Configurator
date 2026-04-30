"""
Stage 1 Validation Pipeline Orchestrator
==========================================
Processes all 20 raw LLM text files through the 4-stage validation
pipeline (V1→V2→V3→V4) and produces all required output artifacts.

Usage:
    python -m experiments.general-prompt.run_stage1_validation
    python -m experiments.general-prompt.run_stage1_validation --skip-docker

Output artifacts:
    - Updated general_llm_generation_data.csv (validation columns filled)
    - validation_and_evaluation/data/production/pddl_diff_metrics.csv
    - JSON reports per stage in validation_and_evaluation/data/production/diffs/
    - Extracted PDDL in results/general_prompt/Extracted PDDL/<domain>/
    - Validated domains in results/general_prompt/Validated Domains/<domain>/
"""

import sys
import csv
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime, timezone

# ── Project root ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Add project root to sys.path so validation package is importable
sys.path.insert(0, str(PROJECT_ROOT))

from validation_and_evaluation.scripts.validation.v1_extraction import extract_pddl_from_response
from validation_and_evaluation.scripts.validation.v2_syntactic_validation import validate_with_val, check_docker_available
from validation_and_evaluation.scripts.validation.v3_identity_check import is_identical_to_original
from validation_and_evaluation.scripts.validation.v4_semantic_equivalence import check_semantic_equivalence

# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("stage1_validation")

# ── Paths ──
LLM_RESULTS_DIR = PROJECT_ROOT / "results" / "general_prompt" / "LLM Results"
LLM_CSV_PATH = LLM_RESULTS_DIR / "general_llm_generation_data.csv"
UNIFIED_LLM_CSV_PATH = PROJECT_ROOT / "results" / "llm_generation_data.csv"
BENCHMARKS_DIR = PROJECT_ROOT / "benchmarks"
EXTRACTED_PDDL_DIR = PROJECT_ROOT / "results" / "general_prompt" / "Extracted PDDL"
VALIDATED_DOMAINS_DIR = PROJECT_ROOT / "results" / "general_prompt" / "Validated Domains"
PRODUCTION_DIR = PROJECT_ROOT / "validation_and_evaluation" / "data" / "production"
DIFFS_DIR = PRODUCTION_DIR / "diffs"
DIFF_METRICS_CSV_PATH = PRODUCTION_DIR / "pddl_diff_metrics.csv"

# ── Mapping from config short name to CSV model_id ──
# Built dynamically from experiment_config.yaml
def load_config():
    import yaml
    config_path = PROJECT_ROOT / "config" / "experiment_config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# ── pddl_diff_metrics.csv columns ──
DIFF_CSV_HEADER = [
    "LLM_ID", "domain", "LLM_Model", "stage",
    "validation_status", "rejection_reason", "failed_stage",
    "has_semantic_change",
    "req_semantic_change", "req_reordered",
    "type_semantic_change", "type_reordered",
    "pred_semantic_change", "pred_reordered",
    "func_semantic_change", "func_reordered",
    "actions_semantic_change", "actions_reordered",
    "params_semantic_change", "params_reordered",
    "pre_semantic_change", "pre_reordered",
    "eff_add_semantic_change", "eff_add_reordered",
    "eff_del_semantic_change", "eff_del_reordered",
    "json_report_path", "extracted_pddl_length", "timestamp",
]


def build_llm_name_to_model_id(config: dict) -> dict:
    """Map LLM short name (used in filenames) to full model_id (used in CSV)."""
    return {llm["name"]: llm["model_id"] for llm in config["llms"]}


def find_llm_csv_row_index(rows: list, domain_name: str, model_id: str) -> int:
    """Find the row index in the LLM CSV matching domain + model_id."""
    for i, row in enumerate(rows):
        if row["Domain Name"] == domain_name and row["LLM Model"] == model_id:
            return i
    return -1


def get_first_instance(domain_name: str) -> Path:
    """Get the first problem instance file for VAL validation."""
    instances_dir = BENCHMARKS_DIR / domain_name / "instances"
    instances = sorted(instances_dir.glob("instance-*.pddl"))
    if not instances:
        raise FileNotFoundError(f"No instances found in {instances_dir}")
    return instances[0]


def save_json_report(report: dict, stage_folder: str, domain: str, llm_short: str) -> Path:
    """Save a JSON report to the appropriate diffs subfolder."""
    out_dir = DIFFS_DIR / stage_folder / domain
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{domain}_{llm_short}_General.json"
    json_path = out_dir / filename
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    return json_path


def append_diff_metrics_row(row: dict):
    """Append a row to pddl_diff_metrics.csv, creating it if needed."""
    PRODUCTION_DIR.mkdir(parents=True, exist_ok=True)
    write_header = not DIFF_METRICS_CSV_PATH.exists()
    with DIFF_METRICS_CSV_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=DIFF_CSV_HEADER)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def build_diff_row(
    llm_id, domain, model_id, status, reason, failed_stage,
    features: dict, json_path: Path, pddl_length
) -> dict:
    """Build a pddl_diff_metrics.csv row dict."""
    row = {
        "LLM_ID": llm_id,
        "domain": domain,
        "LLM_Model": model_id,
        "stage": "General",
        "validation_status": status,
        "rejection_reason": reason if reason else "N/A",
        "failed_stage": failed_stage if failed_stage else "N/A",
        "has_semantic_change": features.get("has_semantic_change", "N/A"),
        "json_report_path": str(json_path.relative_to(PROJECT_ROOT)) if json_path else "N/A",
        "extracted_pddl_length": pddl_length if pddl_length is not None else "N/A",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    # Fill all binary flags
    # For V4 results: unset flags default to 0. For V1/V2/V3 failures: N/A.
    flag_keys = [
        "req_semantic_change", "req_reordered",
        "type_semantic_change", "type_reordered",
        "pred_semantic_change", "pred_reordered",
        "func_semantic_change", "func_reordered",
        "actions_semantic_change", "actions_reordered",
        "params_semantic_change", "params_reordered",
        "pre_semantic_change", "pre_reordered",
        "eff_add_semantic_change", "eff_add_reordered",
        "eff_del_semantic_change", "eff_del_reordered",
    ]
    # features dict is populated only when V4 runs (non-empty dict)
    default_val = 0 if features else "N/A"
    for key in flag_keys:
        row[key] = features.get(key, default_val) if features else "N/A"
    return row


def process_single_file(
    domain_name: str,
    llm_short_name: str,
    model_id: str,
    llm_id: str,
    raw_txt_path: Path,
    csv_row: dict,
    skip_docker: bool,
) -> dict:
    """
    Run the full validation pipeline on a single LLM response file.
    Returns the updated csv_row dict.
    """
    logger.info(f"{'='*60}")
    logger.info(f"Processing: {domain_name} / {llm_short_name} (ID={llm_id})")
    logger.info(f"  File: {raw_txt_path.name}")

    # Read the raw LLM response
    raw_response = raw_txt_path.read_text(encoding="utf-8")
    original_domain_path = BENCHMARKS_DIR / domain_name / "domain.pddl"
    original_pddl = original_domain_path.read_text(encoding="utf-8")

    # ── Stage V1: PDDL Extraction ──
    logger.info("  V1: Extracting PDDL...")
    extracted = extract_pddl_from_response(raw_response)

    if not extracted:
        logger.warning("  V1: REJECTED - extraction_failed")
        csv_row["Passed Stage V1"] = False
        csv_row["Path to Extracted PDDL"] = "N/A"
        csv_row["Passed VAL Syntactic Check (V2)"] = "N/A"
        csv_row["VAL_error_string"] = "N/A"
        csv_row["Passed V3"] = "N/A"
        csv_row["Passed V4"] = "N/A"
        csv_row["Validation Status"] = "REJECTED"

        report = {
            "domain": domain_name, "LLM_Model": model_id, "LLM_ID": llm_id,
            "stage": "General", "validation_status": "REJECTED",
            "failed_stage": "V1: Extraction",
            "rejection_reason": "No balanced (define ...) block found in LLM response",
            "raw_response_length": len(raw_response),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        json_path = save_json_report(report, "V1_extraction", domain_name, llm_short_name)
        diff_row = build_diff_row(
            llm_id, domain_name, model_id, "REJECTED",
            "No balanced (define ...) block found", "V1: Extraction",
            {}, json_path, None
        )
        append_diff_metrics_row(diff_row)
        return csv_row

    logger.info(f"  V1: PASSED - extracted {len(extracted)} chars")

    # Save extracted PDDL
    extracted_dir = EXTRACTED_PDDL_DIR / domain_name
    extracted_dir.mkdir(parents=True, exist_ok=True)
    extracted_pddl_filename = f"{domain_name}_{llm_short_name}_General.pddl"
    extracted_pddl_path = extracted_dir / extracted_pddl_filename
    extracted_pddl_path.write_text(extracted, encoding="utf-8")
    logger.info(f"  Extracted PDDL saved: {extracted_pddl_path.relative_to(PROJECT_ROOT)}")

    # ── Stage V2: Syntactic Validation (VAL Tool) ──
    if skip_docker:
        logger.info("  V2: SKIPPED (--skip-docker flag)")
        v2_passed = True
        val_stderr = ""
    else:
        logger.info("  V2: Running VAL syntactic validation...")
        problem_file = get_first_instance(domain_name)
        val_result = validate_with_val(
            domain_pddl_str=extracted,
            problem_file_path=str(problem_file),
        )
        v2_passed = val_result.is_valid
        val_stderr = val_result.stderr

    if not v2_passed:
        logger.warning(f"  V2: REJECTED - syntactic_error")
        csv_row["Passed Stage V1"] = True
        csv_row["Path to Extracted PDDL"] = str(extracted_pddl_path)
        csv_row["Passed VAL Syntactic Check (V2)"] = False
        csv_row["VAL_error_string"] = val_stderr[:500] if val_stderr else "N/A"
        csv_row["Passed V3"] = "N/A"
        csv_row["Passed V4"] = "N/A"
        csv_row["Validation Status"] = "REJECTED"

        report = {
            "domain": domain_name, "LLM_Model": model_id, "LLM_ID": llm_id,
            "stage": "General", "validation_status": "REJECTED",
            "failed_stage": "V2: VAL",
            "rejection_reason": f"VAL syntactic error: {val_stderr[:300]}",
            "extracted_pddl_length": len(extracted),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        json_path = save_json_report(report, "V2_syntactic", domain_name, llm_short_name)
        diff_row = build_diff_row(
            llm_id, domain_name, model_id, "REJECTED",
            f"VAL syntactic error: {val_stderr[:200]}", "V2: VAL",
            {}, json_path, len(extracted)
        )
        append_diff_metrics_row(diff_row)
        return csv_row

    if not skip_docker:
        logger.info("  V2: PASSED")

    # ── Stage V3: Identity Check ──
    logger.info("  V3: Checking for identity (no transformation)...")
    if is_identical_to_original(extracted, original_pddl):
        logger.warning("  V3: REJECTED - no_transformation (identical to original)")
        csv_row["Passed Stage V1"] = True
        csv_row["Path to Extracted PDDL"] = str(extracted_pddl_path)
        csv_row["Passed VAL Syntactic Check (V2)"] = True
        csv_row["VAL_error_string"] = "N/A"
        csv_row["Passed V3"] = False
        csv_row["Passed V4"] = "N/A"
        csv_row["Validation Status"] = "REJECTED"

        report = {
            "domain": domain_name, "LLM_Model": model_id, "LLM_ID": llm_id,
            "stage": "General", "validation_status": "REJECTED",
            "failed_stage": "V3: Identity",
            "rejection_reason": "LLM output identical to original after normalisation",
            "extracted_pddl_length": len(extracted),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        json_path = save_json_report(report, "V3_identity", domain_name, llm_short_name)
        diff_row = build_diff_row(
            llm_id, domain_name, model_id, "REJECTED",
            "Identical to original after normalisation", "V3: Identity",
            {}, json_path, len(extracted)
        )
        append_diff_metrics_row(diff_row)
        return csv_row

    logger.info("  V3: PASSED - domain differs from original")

    # ── Stage V4: Semantic Equivalence ──
    logger.info("  V4: Checking semantic equivalence...")
    sem_result = check_semantic_equivalence(extracted, original_pddl)
    features = sem_result.diff_features
    details = sem_result.diff_details

    if sem_result.has_semantic_change:
        # INVALID
        logger.warning("  V4: INVALID - semantic change detected")
        csv_row["Passed Stage V1"] = True
        csv_row["Path to Extracted PDDL"] = str(extracted_pddl_path)
        csv_row["Passed VAL Syntactic Check (V2)"] = True
        csv_row["VAL_error_string"] = "N/A"
        csv_row["Passed V3"] = True
        csv_row["Passed V4"] = False
        csv_row["Validation Status"] = "INVALID"

        # Build a readable rejection reason from the semantic changes
        changed = [k.replace("_semantic_change", "") for k, v in features.items()
                    if k.endswith("_semantic_change") and v == 1 and k != "has_semantic_change"]
        reason_str = f"Semantic change in: {', '.join(changed)}" if changed else "Semantic change detected"

        report = {
            "domain": domain_name, "LLM_Model": model_id, "LLM_ID": llm_id,
            "stage": "General", "validation_status": "INVALID",
            "failed_stage": "V4: Semantic",
            "rejection_reason": reason_str,
            "diff_features": features,
            "diff_details": details,
            "extracted_pddl_length": len(extracted),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        json_path = save_json_report(report, "V4_semantic", domain_name, llm_short_name)
        diff_row = build_diff_row(
            llm_id, domain_name, model_id, "INVALID",
            reason_str, "V4: Semantic",
            features, json_path, len(extracted)
        )
        append_diff_metrics_row(diff_row)
        return csv_row

    # VALID
    logger.info("  V4: PASSED - semantic equivalence confirmed → VALID")
    csv_row["Passed Stage V1"] = True
    csv_row["Path to Extracted PDDL"] = str(extracted_pddl_path)
    csv_row["Passed VAL Syntactic Check (V2)"] = True
    csv_row["VAL_error_string"] = "N/A"
    csv_row["Passed V3"] = True
    csv_row["Passed V4"] = True
    csv_row["Validation Status"] = "VALID"

    # Save validated domain copy
    validated_dir = VALIDATED_DOMAINS_DIR / domain_name
    validated_dir.mkdir(parents=True, exist_ok=True)
    validated_path = validated_dir / extracted_pddl_filename
    validated_path.write_text(extracted, encoding="utf-8")
    logger.info(f"  Validated domain saved: {validated_path.relative_to(PROJECT_ROOT)}")

    # Determine which elements were reordered
    reordered = [k.replace("_reordered", "") for k, v in features.items()
                 if k.endswith("_reordered") and v == 1]
    logger.info(f"  Reordered elements: {reordered if reordered else 'none'}")

    report = {
        "domain": domain_name, "LLM_Model": model_id, "LLM_ID": llm_id,
        "stage": "General", "validation_status": "VALID",
        "failed_stage": None, "rejection_reason": None,
        "diff_features": features,
        "diff_details": details,
        "extracted_pddl_length": len(extracted),
        "reordered_elements": reordered,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    json_path = save_json_report(report, "V4_semantic", domain_name, llm_short_name)

    # For VALID: all semantic_change flags = 0, has_semantic_change = 0
    # reorder flags are set from features
    diff_row = build_diff_row(
        llm_id, domain_name, model_id, "VALID",
        None, None, features, json_path, len(extracted)
    )
    append_diff_metrics_row(diff_row)
    return csv_row


def main():
    parser = argparse.ArgumentParser(description="Stage 1 Validation Pipeline")
    parser.add_argument("--skip-docker", action="store_true",
                        help="Skip V2 (VAL syntactic validation via Docker)")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Stage 1 Validation Pipeline — Starting")
    logger.info(f"  Skip Docker: {args.skip_docker}")
    logger.info("=" * 60)

    # Check Docker availability if not skipping
    if not args.skip_docker:
        if not check_docker_available():
            logger.error("Docker is not available. Use --skip-docker or start Docker Desktop.")
            sys.exit(1)
        logger.info("Docker is available ✓")

    # Load config
    config = load_config()
    domains = config["domains"]
    llms = config["llms"]
    name_to_model_id = build_llm_name_to_model_id(config)

    # Load existing LLM generation CSV
    if not LLM_CSV_PATH.exists():
        logger.error(f"LLM generation CSV not found: {LLM_CSV_PATH}")
        sys.exit(1)

    with open(LLM_CSV_PATH, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    logger.info(f"Loaded {len(rows)} rows from LLM generation CSV")

    # Clean up old production diff metrics CSV if it exists
    if DIFF_METRICS_CSV_PATH.exists():
        logger.info(f"Removing old pddl_diff_metrics.csv")
        DIFF_METRICS_CSV_PATH.unlink()

    # Process each domain × LLM combination
    processed = 0
    total = 0
    results_summary = {"VALID": 0, "REJECTED": 0, "INVALID": 0}

    for domain_cfg in domains:
        domain_name = domain_cfg["name"]
        for llm_cfg in llms:
            llm_short = llm_cfg["name"]
            model_id = llm_cfg["model_id"]
            total += 1

            # Find the raw .txt file
            raw_path = LLM_RESULTS_DIR / domain_name / f"{domain_name}_{llm_short}_General.txt"
            if not raw_path.exists():
                logger.warning(f"  SKIP: File not found: {raw_path.relative_to(PROJECT_ROOT)}")
                continue

            # Find the matching CSV row
            row_idx = find_llm_csv_row_index(rows, domain_name, model_id)
            if row_idx == -1:
                logger.warning(f"  SKIP: No CSV row for {domain_name}/{model_id}")
                continue

            llm_id = rows[row_idx]["ID"]

            # Process
            rows[row_idx] = process_single_file(
                domain_name=domain_name,
                llm_short_name=llm_short,
                model_id=model_id,
                llm_id=llm_id,
                raw_txt_path=raw_path,
                csv_row=rows[row_idx],
                skip_docker=args.skip_docker,
            )

            status = rows[row_idx].get("Validation Status", "UNKNOWN")
            results_summary[status] = results_summary.get(status, 0) + 1
            processed += 1

    # Write updated LLM CSV back (both general and unified)
    logger.info(f"\nWriting updated LLM generation CSVs ({len(rows)} rows)...")
    for csv_target in [LLM_CSV_PATH, UNIFIED_LLM_CSV_PATH]:
        with open(csv_target, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        logger.info(f"  Written: {csv_target.relative_to(PROJECT_ROOT)}")

    # Summary
    logger.info("=" * 60)
    logger.info("Stage 1 Validation Pipeline — Complete")
    logger.info(f"  Processed: {processed}/{total}")
    logger.info(f"  VALID:     {results_summary.get('VALID', 0)}")
    logger.info(f"  REJECTED:  {results_summary.get('REJECTED', 0)}")
    logger.info(f"  INVALID:   {results_summary.get('INVALID', 0)}")
    logger.info(f"  Diff metrics CSV: {DIFF_METRICS_CSV_PATH.relative_to(PROJECT_ROOT)}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
