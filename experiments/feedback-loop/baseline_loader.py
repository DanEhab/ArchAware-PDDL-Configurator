"""
Baseline & Seed Data Loader — Stage 3 Feedback Loop
====================================================
Loads pre-computed baseline (Stage 0) and arch-aware (Stage 2) planner
execution statistics from existing CSV files instead of re-running
Docker planners. This eliminates ~2,325 unnecessary planner runs.

Returns the same dict format that `run_soft_critic()` produces so it
can be used as a drop-in replacement for the baseline/seed computation.
"""

import csv
import numpy as np
from pathlib import Path


def _load_stats_from_csv(csv_path, domain, planner, stage_filter=None,
                         llm_filter=None, domain_file_filter=None):
    """
    Read a planner execution CSV and filter by domain + planner (+ optional
    stage/llm/domain_file). Returns the same dict format as run_soft_critic().
    """
    results = {
        "coverage": 0,
        "total_instances": 0,
        "total_search_time": 0.0,
        "total_expanded_states": 0,
        "total_generated_states": 0,
        "instance_statuses": [],
        "instances": {}
    }

    if not Path(csv_path).exists():
        return results

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Basic match
            if row.get("Domain_Name") != domain:
                continue
            if row.get("Planner_Used") != planner:
                continue

            # Stage filter
            if stage_filter is not None:
                row_stage = row.get("Stage", "")
                if isinstance(stage_filter, list):
                    if row_stage not in stage_filter:
                        continue
                elif row_stage != stage_filter:
                    continue

            # LLM filter (substring match, like the orchestrator does)
            if llm_filter is not None:
                row_llm = row.get("LLM_Used", "")
                if llm_filter not in row_llm and row_llm not in llm_filter:
                    continue

            # Domain file filter
            if domain_file_filter is not None:
                row_df = row.get("Domain_File", "")
                if domain_file_filter not in row_df and row_df != domain_file_filter:
                    continue

            inst_name = row.get("Problem_Instance", "")
            status = row.get("Output_Status", "FAILURE")

            # Parse numeric fields safely
            def safe_float(val):
                try:
                    return float(val) if val and val != "N/A" else None
                except (ValueError, TypeError):
                    return None

            def safe_int(val):
                try:
                    return int(float(val)) if val and val != "N/A" else None
                except (ValueError, TypeError):
                    return None

            runtime = safe_float(row.get("Runtime_wall_s"))
            states_expanded = safe_int(row.get("StatesExpanded"))
            states_generated = safe_int(row.get("StatesGenerated"))

            # Only count SUCCESS runtime/states
            if status != "SUCCESS":
                runtime = None
                states_expanded = None

            results["instances"][inst_name] = {
                "status": status,
                "runtime": runtime,
                "states": states_expanded
            }
            results["instance_statuses"].append((inst_name, status))

            if status == "SUCCESS":
                results["coverage"] += 1
                results["total_search_time"] += runtime if runtime else 0.0
                results["total_expanded_states"] += states_expanded if states_expanded else 0
                results["total_generated_states"] += states_generated if states_generated else 0

    results["total_instances"] = len(results["instances"])
    return results


def load_baseline_stats(domain, planner, repo_root):
    """
    Load baseline (Stage 0) planner execution data from
    results/base/base_planner_execution_data.csv.
    """
    csv_path = Path(repo_root) / "results" / "base" / "base_planner_execution_data.csv"
    return _load_stats_from_csv(csv_path, domain, planner, stage_filter="BASELINE")


def load_stage2_stats(domain, planner, llm, repo_root):
    """
    Load Stage 2 (ArchAware) planner execution data from
    results/planner_execution_data.csv.

    The Stage 2 domain file follows the naming convention:
    {domain}_{llm_short}_Arch_Aware_{planner}.pddl

    We filter by Stage=ArchAware and match the domain file name.
    """
    csv_path = Path(repo_root) / "results" / "planner_execution_data.csv"

    # Build the expected domain file pattern from the LLM name
    # The naming convention used in Stage 2 is:
    #   visitall_gpt-5.4_Arch_Aware_lama.pddl
    #   snake_claude-opus-4.6_Arch_Aware_bfws.pddl
    # We match by checking if the domain file contains the planner name
    # and "Arch_Aware" prefix
    llm_short = _llm_to_short(llm)
    domain_file_key = f"{domain}_{llm_short}_Arch_Aware_{planner}"

    return _load_stats_from_csv(
        csv_path, domain, planner,
        stage_filter="Arch_Aware",
        domain_file_filter=domain_file_key
    )


def _llm_to_short(llm):
    """Convert an LLM friendly name to the short form used in file names."""
    mapping = {
        "gpt-5.4": "gpt-5.4",
        "claude-opus-4.6": "claude-opus-4.6",
        "gemini-3.1-pro": "gemini-3.1-pro",
        "deepseek-r1": "deepseek-r1",
    }
    for key, short in mapping.items():
        if key in llm or llm in key:
            return short
    return llm.replace("/", "-")


def compute_seed_ipc(baseline_stats, seed_stats):
    """
    Compute the absolute IPC score of a seed domain relative to the baseline.
    This is the same formula used in loop_engine.py for iter_ipc_abs.
    """
    ipc = 0.0
    for inst_name, base_data in baseline_stats["instances"].items():
        t_base = base_data.get("runtime")
        t_cur = seed_stats["instances"].get(inst_name, {}).get("runtime")

        if t_base is not None and t_cur is not None:
            t_star = min(t_base, t_cur)
            if t_star == 0:
                t_star = 0.001
            ratio_cur = max(1.0, t_cur / t_star)
            ipc += 1.0 / (1.0 + np.log10(ratio_cur))
        elif t_cur is not None:
            # Seed solves it but baseline doesn't → full score
            ipc += 1.0
    return ipc
