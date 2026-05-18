import os
import csv
import threading
from pathlib import Path
from datetime import datetime, timezone

# Global lock for thread-safe CSV writes
csv_lock = threading.Lock()

def log_to_csv(csv_path, row_data):
    """
    Appends a row of data to the specified CSV file.
    Writes the header if the file does not exist.
    """
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
    
    row = {
        "LLM_ID": llm_id,
        "domain": domain,
        "LLM_Model": model_id,
        "stage": stage_name,
        "validation_status": status,
        "rejection_reason": reason if reason else "N/A",
        "failed_stage": failed_stage if failed_stage else "N/A",
        "has_semantic_change": diff_features.get("has_semantic_change", "N/A") if diff_features else "N/A",
        "json_report_path": str(Path(json_path).relative_to(repo_root)).replace("\\", "/") if json_path else "N/A",
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
    
    default_val = 0 if diff_features else "N/A"
    for key in flag_keys:
        row[key] = diff_features.get(key, default_val) if diff_features else "N/A"
        
    diff_csv_relative = Path("validation_and_evaluation/data/production/feedback_loop/feedback_loop_pddl_diff_metrics.csv")
    global_diff_csv_relative = Path("validation_and_evaluation/data/production/pddl_diff_metrics.csv")
    
    diff_csv_path = Path(repo_root) / diff_csv_relative
    global_diff_csv_path = Path(repo_root) / global_diff_csv_relative
    
    diff_csv_path.parent.mkdir(parents=True, exist_ok=True)
    global_diff_csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    with csv_lock:
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
