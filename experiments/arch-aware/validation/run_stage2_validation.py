"""
Stage 2 Validation Pipeline Orchestrator (Phase B)
==========================================
Processes all 80 raw LLM text files through the 4-stage validation
pipeline (V1→V2→V3→V4) and produces all required output artifacts.

Usage:
    python -m experiments.arch-aware.validation.run_stage2_validation
    python -m experiments.arch-aware.validation.run_stage2_validation --skip-docker
"""

import sys
import csv
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime, timezone

# ── Project root ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
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
logger = logging.getLogger("stage2_validation")

# ── Paths ──
LLM_RESULTS_DIR = PROJECT_ROOT / "results" / "arch_aware" / "LLM Results"
LLM_CSV_PATH = LLM_RESULTS_DIR / "arch_aware_llm_generation_data.csv"
UNIFIED_LLM_CSV_PATH = PROJECT_ROOT / "results" / "llm_generation_data.csv"
BENCHMARKS_DIR = PROJECT_ROOT / "benchmarks"
EXTRACTED_PDDL_DIR = PROJECT_ROOT / "results" / "arch_aware" / "Extracted PDDL"
VALIDATED_DOMAINS_DIR = PROJECT_ROOT / "results" / "arch_aware" / "Validated Domains"
PRODUCTION_DIR = PROJECT_ROOT / "validation_and_evaluation" / "data" / "production"
DIFFS_DIR = PRODUCTION_DIR / "arch_aware" / "diffs"
DIFF_METRICS_CSV_PATH = PRODUCTION_DIR / "arch_aware" / "arch_aware_pddl_diff_metrics.csv"
GLOBAL_DIFF_METRICS_CSV_PATH = PRODUCTION_DIR / "pddl_diff_metrics.csv"

# ── Dictionary mapping ──
PLANNER_TO_PROMPT_ID = {
    "lama": "1",
    "decstar": "2",
    "bfws": "3",
    "madagascar": "4"
}

def load_config():
    import yaml
    config_path = PROJECT_ROOT / "config" / "experiment_config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

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
    return {llm["name"]: llm["model_id"] for llm in config["llms"]}

def find_llm_csv_row_index(rows: list, domain_name: str, model_id: str, prompt_id: str) -> int:
    for i, row in enumerate(rows):
        if row["Domain Name"] == domain_name and row["LLM Model"] == model_id and str(row["Prompt ID"]) == str(prompt_id):
            return i
    return -1

def get_first_instance(domain_name: str) -> Path:
    instances_dir = BENCHMARKS_DIR / domain_name / "instances"
    instances = sorted(instances_dir.glob("instance-*.pddl"))
    if not instances:
        raise FileNotFoundError(f"No instances found in {instances_dir}")
    return instances[0]

def save_json_report(report: dict, stage_folder: str, domain: str, llm_short: str, planner: str) -> Path:
    out_dir = DIFFS_DIR / stage_folder / domain
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{domain}_{llm_short}_Arch_Aware_{planner}.json"
    json_path = out_dir / filename
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    return json_path

def append_diff_metrics_row(row: dict):
    PRODUCTION_DIR.mkdir(parents=True, exist_ok=True)
    (PRODUCTION_DIR / "arch_aware").mkdir(parents=True, exist_ok=True)
    
    # Write to stage-local CSV
    write_header_local = not DIFF_METRICS_CSV_PATH.exists()
    with DIFF_METRICS_CSV_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=DIFF_CSV_HEADER)
        if write_header_local:
            writer.writeheader()
        writer.writerow(row)

    # Write to global CSV
    write_header_global = not GLOBAL_DIFF_METRICS_CSV_PATH.exists()
    with GLOBAL_DIFF_METRICS_CSV_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=DIFF_CSV_HEADER)
        if write_header_global:
            writer.writeheader()
        writer.writerow(row)

def build_diff_row(
    llm_id, domain, model_id, status, reason, failed_stage,
    features: dict, json_path: Path, pddl_length
) -> dict:
    row = {
        "LLM_ID": llm_id,
        "domain": domain,
        "LLM_Model": model_id,
        "stage": "Arch_Aware",
        "validation_status": status,
        "rejection_reason": reason if reason else "N/A",
        "failed_stage": failed_stage if failed_stage else "N/A",
        "has_semantic_change": features.get("has_semantic_change", "N/A") if features else "N/A",
        "json_report_path": str(json_path.relative_to(PROJECT_ROOT)) if json_path else "N/A",
        "extracted_pddl_length": pddl_length if pddl_length is not None else "N/A",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
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
    default_val = 0 if features else "N/A"
    for key in flag_keys:
        row[key] = features.get(key, default_val) if features else "N/A"
    return row

def process_single_file(
    domain_name: str,
    llm_short_name: str,
    model_id: str,
    planner_name: str,
    llm_id: str,
    raw_txt_path: Path,
    csv_row: dict,
    skip_docker: bool,
) -> dict:
    logger.info(f"{'='*60}")
    logger.info(f"Processing: {domain_name} / {llm_short_name} / {planner_name} (ID={llm_id})")

    raw_response = raw_txt_path.read_text(encoding="utf-8")
    original_domain_path = BENCHMARKS_DIR / domain_name / "domain.pddl"
    original_pddl = original_domain_path.read_text(encoding="utf-8")

    # V1: Extraction
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
            "stage": "Arch_Aware", "validation_status": "REJECTED",
            "failed_stage": "V1: Extraction",
            "rejection_reason": "No balanced (define ...) block found in LLM response",
            "raw_response_length": len(raw_response),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        json_path = save_json_report(report, "V1_extraction", domain_name, llm_short_name, planner_name)
        diff_row = build_diff_row(
            llm_id, domain_name, model_id, "REJECTED",
            "No balanced (define ...) block found", "V1: Extraction",
            {}, json_path, None
        )
        append_diff_metrics_row(diff_row)
        return csv_row

    logger.info(f"  V1: PASSED - extracted {len(extracted)} chars")

    extracted_dir = EXTRACTED_PDDL_DIR / domain_name
    extracted_dir.mkdir(parents=True, exist_ok=True)
    extracted_pddl_filename = f"{domain_name}_{llm_short_name}_Arch_Aware_{planner_name}.pddl"
    extracted_pddl_path = extracted_dir / extracted_pddl_filename
    extracted_pddl_path.write_text(extracted, encoding="utf-8")
    
    # V2: Syntactic Validation
    if skip_docker:
        logger.info("  V2: SKIPPED (--skip-docker flag)")
        v2_passed = True
        val_stderr = ""
    else:
        logger.info("  V2: Running VAL syntactic validation...")
        problem_file = get_first_instance(domain_name)
        val_result = validate_with_val(extracted, str(problem_file))
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
            "stage": "Arch_Aware", "validation_status": "REJECTED",
            "failed_stage": "V2: VAL",
            "rejection_reason": f"VAL syntactic error: {val_stderr[:300]}",
            "extracted_pddl_length": len(extracted),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        json_path = save_json_report(report, "V2_syntactic", domain_name, llm_short_name, planner_name)
        diff_row = build_diff_row(
            llm_id, domain_name, model_id, "REJECTED",
            f"VAL syntactic error: {val_stderr[:200]}", "V2: VAL",
            {}, json_path, len(extracted)
        )
        append_diff_metrics_row(diff_row)
        return csv_row

    # V3: Identity Check
    logger.info("  V3: Checking for identity...")
    if is_identical_to_original(extracted, original_pddl):
        logger.warning("  V3: REJECTED - no_transformation")
        csv_row["Passed Stage V1"] = True
        csv_row["Path to Extracted PDDL"] = str(extracted_pddl_path)
        csv_row["Passed VAL Syntactic Check (V2)"] = True
        csv_row["VAL_error_string"] = "N/A"
        csv_row["Passed V3"] = False
        csv_row["Passed V4"] = "N/A"
        csv_row["Validation Status"] = "REJECTED"

        report = {
            "domain": domain_name, "LLM_Model": model_id, "LLM_ID": llm_id,
            "stage": "Arch_Aware", "validation_status": "REJECTED",
            "failed_stage": "V3: Identity",
            "rejection_reason": "LLM output identical to original",
            "extracted_pddl_length": len(extracted),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        json_path = save_json_report(report, "V3_identity", domain_name, llm_short_name, planner_name)
        diff_row = build_diff_row(
            llm_id, domain_name, model_id, "REJECTED",
            "Identical to original", "V3: Identity",
            {}, json_path, len(extracted)
        )
        append_diff_metrics_row(diff_row)
        return csv_row

    # V4: Semantic Equivalence
    logger.info("  V4: Checking semantic equivalence...")
    sem_result = check_semantic_equivalence(extracted, original_pddl)
    features = sem_result.diff_features
    details = sem_result.diff_details

    if sem_result.has_semantic_change:
        logger.warning("  V4: INVALID - semantic change detected")
        csv_row["Passed Stage V1"] = True
        csv_row["Path to Extracted PDDL"] = str(extracted_pddl_path)
        csv_row["Passed VAL Syntactic Check (V2)"] = True
        csv_row["VAL_error_string"] = "N/A"
        csv_row["Passed V3"] = True
        csv_row["Passed V4"] = False
        csv_row["Validation Status"] = "INVALID"

        changed = [k.replace("_semantic_change", "") for k, v in features.items()
                    if k.endswith("_semantic_change") and v == 1 and k != "has_semantic_change"]
        reason_str = f"Semantic change in: {', '.join(changed)}" if changed else "Semantic change detected"

        report = {
            "domain": domain_name, "LLM_Model": model_id, "LLM_ID": llm_id,
            "stage": "Arch_Aware", "validation_status": "INVALID",
            "failed_stage": "V4: Semantic",
            "rejection_reason": reason_str,
            "diff_features": features,
            "diff_details": details,
            "extracted_pddl_length": len(extracted),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        json_path = save_json_report(report, "V4_semantic", domain_name, llm_short_name, planner_name)
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

    # Save validated domain copy (planner subfolder)
    validated_dir = VALIDATED_DOMAINS_DIR / domain_name / planner_name
    validated_dir.mkdir(parents=True, exist_ok=True)
    validated_path = validated_dir / extracted_pddl_filename
    validated_path.write_text(extracted, encoding="utf-8")

    reordered = [k.replace("_reordered", "") for k, v in features.items()
                 if k.endswith("_reordered") and v == 1]
    
    report = {
        "domain": domain_name, "LLM_Model": model_id, "LLM_ID": llm_id,
        "stage": "Arch_Aware", "validation_status": "VALID",
        "failed_stage": None, "rejection_reason": None,
        "diff_features": features,
        "diff_details": details,
        "extracted_pddl_length": len(extracted),
        "reordered_elements": reordered,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    json_path = save_json_report(report, "V4_semantic", domain_name, llm_short_name, planner_name)
    diff_row = build_diff_row(
        llm_id, domain_name, model_id, "VALID",
        None, None, features, json_path, len(extracted)
    )
    append_diff_metrics_row(diff_row)
    return csv_row

def main():
    parser = argparse.ArgumentParser("Stage 2 Validation Pipeline")
    parser.add_argument("--skip-docker", action="store_true", help="Skip V2")
    args = parser.parse_args()

    if not args.skip_docker and not check_docker_available():
        logger.error("Docker is not available.")
        sys.exit(1)

    config = load_config()
    domains = config["domains"]
    llms = config["llms"]

    if not LLM_CSV_PATH.exists():
        logger.error(f"LLM CSV not found: {LLM_CSV_PATH}")
        sys.exit(1)

    with open(LLM_CSV_PATH, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        local_rows = list(reader)

    # Read global unified CSV
    unified_rows = []
    unified_fieldnames = []
    if UNIFIED_LLM_CSV_PATH.exists():
        with open(UNIFIED_LLM_CSV_PATH, "r", encoding="utf-8-sig") as f:
            u_reader = csv.DictReader(f)
            unified_fieldnames = u_reader.fieldnames
            unified_rows = list(u_reader)

    # REMOVED: Do not unlink DIFF_METRICS_CSV_PATH so it can safely append

    processed, total = 0, 0
    results_summary = {"VALID": 0, "REJECTED": 0, "INVALID": 0}

    for domain_cfg in domains:
        domain_name = domain_cfg["name"]
        for llm_cfg in llms:
            llm_short = llm_cfg["name"]
            model_id = llm_cfg["model_id"]
            
            for planner, prompt_id in PLANNER_TO_PROMPT_ID.items():
                total += 1
                raw_path = LLM_RESULTS_DIR / domain_name / f"{domain_name}_{llm_short}_Arch_Aware_{planner}.txt"
                if not raw_path.exists():
                    continue

                row_idx = find_llm_csv_row_index(local_rows, domain_name, model_id, prompt_id)
                if row_idx == -1:
                    continue

                llm_id = local_rows[row_idx]["ID"]
                
                # CHECKPOINT CHECK: Skip if already validated
                status = local_rows[row_idx].get("Validation Status", "N/A")
                if status in ["VALID", "INVALID", "REJECTED"]:
                    logger.info(f"Skipping: {domain_name} / {llm_short} / {planner} (ID={llm_id}) — already {status}")
                    results_summary[status] = results_summary.get(status, 0) + 1
                    processed += 1
                    continue

                local_rows[row_idx] = process_single_file(
                    domain_name, llm_short, model_id, planner, llm_id,
                    raw_path, local_rows[row_idx], args.skip_docker
                )

                # Find and update corresponding row in the global CSV
                if unified_rows:
                    for u_row in unified_rows:
                        if u_row["ID"] == llm_id:
                            # Update all validation columns correctly
                            for col in ["Passed Stage V1", "Path to Extracted PDDL", 
                                        "Passed VAL Syntactic Check (V2)", "VAL_error_string",
                                        "Passed V3", "Passed V4", "Validation Status"]:
                                u_row[col] = local_rows[row_idx][col]
                            break

                final_status = local_rows[row_idx].get("Validation Status", "UNKNOWN")
                results_summary[final_status] = results_summary.get(final_status, 0) + 1
                processed += 1

                # Checkpoint Execution:
                # Save local CSV incrementally after each processed file
                with open(LLM_CSV_PATH, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(local_rows)

                # Save global CSV incrementally after each processed file
                if unified_rows and unified_fieldnames:
                    with open(UNIFIED_LLM_CSV_PATH, "w", newline="", encoding="utf-8") as f:
                        writer = csv.DictWriter(f, fieldnames=unified_fieldnames)
                        writer.writeheader()
                        writer.writerows(unified_rows)

    logger.info(f"Processed: {processed}/{total}")
    logger.info(f"Summary: {results_summary}")

if __name__ == "__main__":
    main()
