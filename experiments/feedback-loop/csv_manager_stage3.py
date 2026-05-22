"""
CSV Manager — Stage 3 Feedback Loop
====================================
Thread-safe CSV logging for:
  - Iteration tracking (local)
  - Diff metrics (local + global)
  - LLM generation data (local + global)
  - Planner execution data (local + global)
"""

import os
import csv
import threading
from pathlib import Path
from datetime import datetime, timezone

# Global lock for thread-safe CSV writes
csv_lock = threading.Lock()

# ── LLM Name Normalisation ──────────────────────────────────────────
# Stage 3 friendly names  →  names already used in the global CSVs
LLM_NAME_MAP = {
    "gpt-5.4":        "gpt-5.4-2026-03-05",
    "claude-opus-4.6": "claude-opus-4-6",
    "gemini-3.1-pro":  "gemini-3.1-pro-preview-customtools",
    "deepseek-r1":     "deepseek-reasoner",
}

def _normalise_llm_name(raw_name: str) -> str:
    """Map a Stage-3 friendly LLM name to the canonical name used in
    the global results CSVs so that every file is consistent."""
    for key, canonical in LLM_NAME_MAP.items():
        if key in raw_name or raw_name in key:
            return canonical
    return raw_name




def log_to_csv(csv_path, row_data):
    """
    Appends a row of data to the specified CSV file.
    Writes the header if the file does not exist.
    """
    Path(csv_path).parent.mkdir(parents=True, exist_ok=True)
    file_exists = os.path.isfile(csv_path)
    with csv_lock:
        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=row_data.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(row_data)

def log_diff_metrics(diff_features, status, reason, failed_stage, llm_id, domain, model_id, iteration, json_path, pddl_length, repo_root):
    """
    Write to production/feedback_loop/feedback_loop_pddl_diff_metrics.csv
    and production/pddl_diff_metrics.csv (global)
    """
    stage_name = f"Feedback_Loop{iteration}"
    canonical_model = _normalise_llm_name(model_id)
    
    row = {
        "LLM_ID": "N/A",  # Placeholder, will be auto-incremented
        "domain": domain,
        "LLM_Model": canonical_model,
        "stage": stage_name,
        "validation_status": status,
        "rejection_reason": reason if reason else "N/A",
        "failed_stage": failed_stage if failed_stage else "N/A",
        "has_semantic_change": diff_features.get("has_semantic_change", "N/A") if diff_features else "N/A",
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
    
    default_val = 0 if diff_features else "N/A"
    for key in flag_keys:
        row[key] = diff_features.get(key, default_val) if diff_features else "N/A"

    # These two fields must come AFTER the flag columns (matching global CSV column order)
    row["json_report_path"] = str(Path(json_path).relative_to(repo_root)).replace("\\", "/") if json_path else "N/A"
    row["extracted_pddl_length"] = pddl_length if pddl_length is not None else "N/A"
    row["timestamp"] = datetime.now(timezone.utc).isoformat()
        
    diff_csv_relative = Path("validation_and_evaluation/data/production/feedback_loop/feedback_loop_pddl_diff_metrics.csv")
    global_diff_csv_relative = Path("validation_and_evaluation/data/production/pddl_diff_metrics.csv")
    
    diff_csv_path = Path(repo_root) / diff_csv_relative
    global_diff_csv_path = Path(repo_root) / global_diff_csv_relative
    
    diff_csv_path.parent.mkdir(parents=True, exist_ok=True)
    global_diff_csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    with csv_lock:
        new_llm_id = _get_next_numeric_id(global_diff_csv_path, "LLM_ID")
        row["LLM_ID"] = new_llm_id
        
        write_header_local = not diff_csv_path.exists()
        with diff_csv_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            if write_header_local: writer.writeheader()
            writer.writerow(row)
            
        write_header_global = not global_diff_csv_path.exists()
        with global_diff_csv_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            if write_header_global: writer.writeheader()
            writer.writerow(row)


def log_llm_generation(row_data, repo_root):
    """
    Append an LLM generation record to both local and global CSVs.
    Local:  results/feedback_loop/feedback_loop_llm_generation_data.csv
    Global: results/llm_generation_data.csv
    
    The ID is auto-incremented from the global CSV's max numeric ID.
    The LLM Model name is normalised to match existing CSV conventions.
    """
    local_path = Path(repo_root) / "results/feedback_loop/feedback_loop_llm_generation_data.csv"
    global_path = Path(repo_root) / "results/llm_generation_data.csv"
    
    local_path.parent.mkdir(parents=True, exist_ok=True)
    global_path.parent.mkdir(parents=True, exist_ok=True)
    
    expected_keys = [
        "ID", "Domain Name", "LLM Model", "Prompt ID", "LLM_Status", "LLM API Time S",
        "Input Tokens Consumed", "Output Tokens Generated", "Path to Raw LLM Response",
        "Passed Stage V1", "Path to Extracted PDDL", "Passed VAL Syntactic Check (V2)",
        "VAL_error_string", "Passed V3", "Passed V4", "Validation Status", "Timestamp"
    ]
    
    filled_row = {k: row_data.get(k, "N/A") for k in expected_keys}
    if "Timestamp" not in row_data or row_data["Timestamp"] == "N/A":
        filled_row["Timestamp"] = datetime.now(timezone.utc).isoformat()

    # Normalise the LLM Model name
    if "LLM Model" in filled_row:
        filled_row["LLM Model"] = _normalise_llm_name(str(filled_row["LLM Model"]))

    with csv_lock:
        # Auto-increment numeric ID from global CSV
        next_id = _get_next_numeric_id(global_path, "ID")
        filled_row["ID"] = next_id

        local_hdr = not local_path.exists()
        with local_path.open("a", newline="", encoding="utf-8") as lf:
            w = csv.DictWriter(lf, fieldnames=expected_keys)
            if local_hdr: w.writeheader()
            w.writerow(filled_row)
            
        global_hdr = not global_path.exists()
        with global_path.open("a", newline="", encoding="utf-8") as gf:
            w = csv.DictWriter(gf, fieldnames=expected_keys)
            if global_hdr: w.writeheader()
            w.writerow(filled_row)


def _get_next_numeric_id(global_csv_path: Path, id_col: str) -> int:
    """Read the global CSV and return max(existing numeric ID) + 1."""
    max_id = 0
    if global_csv_path.exists():
        try:
            with open(global_csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    raw = row.get(id_col, "0")
                    try:
                        val = int(raw)
                        if val > max_id:
                            max_id = val
                    except (ValueError, TypeError):
                        pass
        except Exception:
            pass
    return max_id + 1


def log_planner_execution(row_data, repo_root) -> int:
    """
    Append a planner execution record to both local and global CSVs.
    Local:  results/feedback_loop/feedback_loop_planner_execution_data.csv
    Global: results/planner_execution_data.csv
    
    Run_ID is auto-incremented from the global CSV's max numeric Run_ID.
    Returns the newly assigned Run_ID.
    """
    local_path = Path(repo_root) / "results/feedback_loop/feedback_loop_planner_execution_data.csv"
    global_path = Path(repo_root) / "results/planner_execution_data.csv"
    
    local_path.parent.mkdir(parents=True, exist_ok=True)
    global_path.parent.mkdir(parents=True, exist_ok=True)
    
    expected_keys = [
        "Run_ID", "Domain_Name", "Domain_File", "Problem_Instance", "Planner_Used",
        "Stage", "LLM_Used", "PromptID", "PlanCost", "Runtime_internal_s",
        "Runtime_wall_s", "Output_Status", "StatesExpanded", "StatesGenerated",
        "StatesEvaluated", "PeakMemoryKB", "Timestamp"
    ]
    
    filled_row = {k: row_data.get(k, "N/A") for k in expected_keys}
    if "Timestamp" not in row_data or row_data["Timestamp"] == "N/A":
        filled_row["Timestamp"] = datetime.now(timezone.utc).isoformat()

    # Normalise the LLM_Used name
    if "LLM_Used" in filled_row:
        filled_row["LLM_Used"] = _normalise_llm_name(str(filled_row["LLM_Used"]))
        
    with csv_lock:
        # Auto-increment numeric Run_ID from global CSV
        new_run_id = _get_next_numeric_id(global_path, "Run_ID")
        filled_row["Run_ID"] = new_run_id
        
        local_hdr = not local_path.exists()
        with local_path.open("a", newline="", encoding="utf-8") as lf:
            w = csv.DictWriter(lf, fieldnames=expected_keys)
            if local_hdr: w.writeheader()
            w.writerow(filled_row)
            
        global_hdr = not global_path.exists()
        with global_path.open("a", newline="", encoding="utf-8") as gf:
            w = csv.DictWriter(gf, fieldnames=expected_keys)
            if global_hdr: w.writeheader()
            w.writerow(filled_row)

    return new_run_id
