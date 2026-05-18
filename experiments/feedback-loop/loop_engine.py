import os
import sys
import datetime
from pathlib import Path

REPO_ROOT = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

# Handle directories with hyphens
sys.path.insert(0, str(REPO_ROOT / "experiments" / "general-prompt"))
sys.path.insert(0, str(REPO_ROOT / "experiments" / "feedback-loop"))

from validation_and_evaluation.scripts.validation.validation_pipeline import validate_domain
from experiments.base.planner_runner import execute_planner
from llms.llm_providers import get_provider  # type: ignore
import yaml
import numpy as np

from csv_manager_stage3 import log_to_csv  # type: ignore
from rationale_extractor import extract_rationale  # type: ignore
from meta_controller import calculate_simple_ipc, build_telemetry_table, meta_controller_diagnostics  # type: ignore
from prompt_builder import build_feedback_prompt  # type: ignore

CONFIG_PATH = REPO_ROOT / "config" / "experiment_config.yaml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)
DOCKER_CFG = CONFIG["docker"]

def run_soft_critic(domain_pddl_path, planner_name, test_instances):
    results = {
        "coverage": 0,
        "total_instances": len(test_instances),
        "total_search_time": 0.0,
        "total_expanded_states": 0,
        "total_generated_states": 0,
        "instance_statuses": [],
        "instances": {} 
    }
    for instance_path in test_instances:
        docker_image = f"{planner_name}_planner"
        res = execute_planner(
            planner_name=planner_name, 
            docker_image=docker_image, 
            domain_path=Path(domain_pddl_path), 
            problem_path=Path(instance_path),
            docker_cfg=DOCKER_CFG
        )
        status = res.get("Output_Status", "FAILURE")
        inst_name = os.path.basename(instance_path)
        results["instance_statuses"].append((inst_name, status))
        
        runtime = float(res.get("Runtime_wall_s") or 0.0) if status == "SUCCESS" else None
        states = int(res.get("StatesExpanded") or 0) if status == "SUCCESS" else None
        
        results["instances"][inst_name] = {
            "status": status,
            "runtime": runtime,
            "states": states
        }
        
        if status == "SUCCESS":
            results["coverage"] += 1
            results["total_search_time"] += float(res.get("Runtime_wall_s") or 0.0)
            results["total_expanded_states"] += int(res.get("StatesExpanded") or 0)
            results["total_generated_states"] += int(res.get("StatesGenerated") or 0)
    return results


def run_feedback_loop(domain_name, planner_name, llm_model, base_domain_path, test_instances, output_dir, stage0_baseline_path, initial_history_buffer, initial_telemetry_feedback, stage2_best_score, is_valid_seed, max_iter=3):
    print(f"\n[{domain_name} | {planner_name} | {llm_model}] Starting Stage 3 Feedback Loop")
    
    prompt_dir = os.path.join(REPO_ROOT, "experiments", "arch-aware", "prompts")

    # Setup directories
    run_dir = os.path.join(output_dir, "Iteration Domains", llm_model.replace('/','-'), planner_name, domain_name)
    os.makedirs(run_dir, exist_ok=True)
    
    llm_resp_dir = os.path.join(output_dir, "LLM Responses", llm_model.replace('/','-'), planner_name, domain_name)
    os.makedirs(llm_resp_dir, exist_ok=True)
    
    prompt_save_dir = os.path.join(REPO_ROOT, "logs", "stage3", "feedback_prompts", llm_model.replace('/','-'), planner_name, domain_name)
    os.makedirs(prompt_save_dir, exist_ok=True)
    
    csv_path = os.path.join(output_dir, "iteration_tracking.csv")
    final_domains_csv = os.path.join(output_dir, "stage3_final_domains.csv")

    current_domain_str = Path(base_domain_path).read_text(encoding="utf-8")
    
    # Store initial seed layout as iter0.pddl for precise traceability
    seed_copy_path = os.path.join(run_dir, f"{domain_name}_{llm_model.replace('/','-')}_Feedback_{planner_name}_iter0.pddl")
    Path(seed_copy_path).write_text(current_domain_str, encoding="utf-8")
    
    print(f"[{llm_model} | {planner_name} | {domain_name}] Iteration 0: Computing baseline performance on Target Planner...")
    baseline_stats = run_soft_critic(stage0_baseline_path, planner_name, test_instances)
    
    history_buffer = initial_history_buffer.copy()
    telemetry_feedback = str(initial_telemetry_feedback)
    cumulative_failures = 0
    v4_semantic_failures = 0
    
    # Resolve the correct provider and model_id from the global config based on the friendly name
    provider_name = "openai"
    actual_model_id = llm_model
    if "llms" in CONFIG:
        for cfg_llm in CONFIG["llms"]:
            if cfg_llm.get("name") == llm_model:
                provider_name = cfg_llm.get("provider", "openai")
                actual_model_id = cfg_llm.get("model_id", llm_model)
                break
                
    if "claude" in llm_model.lower() and provider_name == "openai": provider_name = "anthropic"
    elif "gemini" in llm_model.lower() and provider_name == "openai": provider_name = "google"
    elif "deepseek" in llm_model.lower() and provider_name == "openai": provider_name = "deepseek"
    
    llm = get_provider(provider_name, actual_model_id, temp=0.0, top_p=1.0, max_tokens=8192)

    best_score = float(stage2_best_score)
    seed_score = float(stage2_best_score)
    best_domain_path = None if not is_valid_seed else base_domain_path
    
    verdict = None # Track across iterations
    best_iter_num = 0
    term_reason = "MAX_ITER"
    last_ipc = seed_score

    for iteration in range(1, max_iter + 1):
        print(f"\n[{llm_model} | {planner_name} | {domain_name}] --- Starting Iteration {iteration} ---")
        
        history_buffer_str = "\n\n".join(history_buffer)
        
        if iteration > 1:
            if verdict == "REGRESSION":
                current_task_block = f"CURRENT TASK (Iteration {iteration}):\nYour strategy in Iteration {iteration-1} actively harmed performance. Do not repeat these changes. Analyze the current domain and propose a NEW strategy."
                history_buffer_str += "\n\n" + current_task_block
            elif verdict == "IMPROVEMENT":
                current_task_block = f"CURRENT TASK (Iteration {iteration}):\nYour strategy in Iteration {iteration-1} showed improvement. Analyze the current domain and propose a strategy to further optimize the remaining timeouts."
                history_buffer_str += "\n\n" + current_task_block
            elif verdict == "FAILED_VALIDATION":
                current_task_block = f"CURRENT TASK (Iteration {iteration}):\nYour strategy in Iteration {iteration-1} resulted in a broken domain file. Do not repeat these changes. Analyze the current domain and propose a NEW Valid strategy."
                history_buffer_str += "\n\n" + current_task_block

        prompt_text = build_feedback_prompt(
            planner_name, prompt_dir, current_domain_str, history_buffer_str, telemetry_feedback
        )

        prompt_log_path = os.path.join(prompt_save_dir, f"{domain_name}_{llm_model.replace('/','-')}_{planner_name}_iter{iteration}_prompt.txt")
        Path(prompt_log_path).write_text(prompt_text, encoding="utf-8")

        try:
            print(f"[{llm_model} | {planner_name} | {domain_name}] Iteration {iteration}: Generating reordered domain via LLM...")
            llm_response, elapsed, input_toks, output_toks = llm.generate(prompt_text)
        except Exception as e:
            print(f"[{llm_model} | {planner_name} | {domain_name}] LLM Error: {e}")
            break

        rationale = extract_rationale(llm_response)
        
        llm_resp_path = os.path.join(llm_resp_dir, f"{domain_name}_{llm_model.replace('/','-')}_{planner_name}_iter{iteration}.txt")
        Path(llm_resp_path).write_text(llm_response, encoding="utf-8")

        print(f"[{llm_model} | {planner_name} | {domain_name}] Iteration {iteration}: Running V1-V4 Validation Pipeline (Hard Critics)...")
        tmp_domain_path = os.path.join(run_dir, f"{domain_name}_{llm_model.replace('/','-')}_Feedback_{planner_name}_iter{iteration}.pddl")
        
        idx_pddl = llm_response.lower().find("(define (domain")
        if idx_pddl == -1: idx_pddl = llm_response.lower().find("(define(domain")
        extracted_pddl = llm_response if idx_pddl == -1 else llm_response[idx_pddl:]
        extracted_pddl = extracted_pddl.replace("```lisp", "").replace("```pddl", "").replace("```", "").strip()

        problem_file_path_obj = Path(test_instances[0]) if test_instances else None
        val_result = validate_domain(llm_response, Path(stage0_baseline_path), problem_file_path_obj)
        val_status = val_result.status
        
        if val_status != "VALID":
            verdict = "FAILED_VALIDATION"
            cumulative_failures += 1
            reason = val_result.reason or "Unknown"
            failed_stage = val_result.failed_stage or "Unknown"
            v4_detail = str(val_result.diff_features) if failed_stage == "V4" else "N/A"
            if failed_stage == "V4": v4_semantic_failures += 1
            
            if failed_stage == "V4":
                telemetry_feedback = f"[EXECUTION FEEDBACK — ITERATION {iteration + 1}]\n\nYour Iteration {iteration} output was REJECTED because it changed the domain's logical semantics.\nSpecific violations detected: {v4_detail}\n\n⚠ You must ONLY reorder elements. Do NOT modify preconditions, effects, or parameters. Analyze the domain below and try a different structural reordering strategy."
                history_buffer.append(f"Iteration {iteration}:\n  • Your Strategy: \"{rationale}\"\n  • Result: REJECTED — V4 check failed.\n    Changes detected: {v4_detail}")
            elif failed_stage == "V2":
                telemetry_feedback = f"[EXECUTION FEEDBACK — ITERATION {iteration + 1}]\n\nYour Iteration {iteration} output was REJECTED because it contained syntax errors.\nSpecific violations detected: {reason}\n\n⚠ You must ONLY reorder elements. Do NOT modify preconditions, effects, or parameters. Analyze the domain below and try a different structural reordering strategy."
                history_buffer.append(f"Iteration {iteration}:\n  • Your Strategy: \"{rationale}\"\n  • Result: REJECTED — V2 check failed.\n    Changes detected: {reason}")
            elif failed_stage == "V3":
                telemetry_feedback = f"[EXECUTION FEEDBACK — ITERATION {iteration + 1}]\n\nYour Iteration {iteration} output was REJECTED because it was identical to the input domain.\n\n⚠ You must ONLY reorder elements. Do NOT modify preconditions, effects, or parameters. Analyze the domain below and try a different structural reordering strategy."
                history_buffer.append(f"Iteration {iteration}:\n  • Your Strategy: \"{rationale}\"\n  • Result: REJECTED — V3 check failed.\n    Changes detected: Identity.")
            else:
                 telemetry_feedback = f"[EXECUTION FEEDBACK — ITERATION {iteration + 1}]\n\nYour Iteration {iteration} output was REJECTED because it failed V1 extraction.\n\n⚠ You must ONLY reorder elements. Do NOT modify preconditions, effects, or parameters. Analyze the domain below and try a different structural reordering strategy."
                 history_buffer.append(f"Iteration {iteration}:\n  • Your Strategy: \"{rationale}\"\n  • Result: REJECTED — V1 check failed.\n    Changes detected: Malformed.")
            
            log_to_csv(csv_path, {"Triple_ID": f"{domain_name}_{planner_name}_{llm_model}", "Domain": domain_name, "LLM": llm_model, "Target_Planner": planner_name, "Iteration": iteration, "Validation_Status": f"INVALID_{failed_stage}", "V4_Failure_Detail": v4_detail, "Coverage": 0.0, "Avg_Run_Wall_s": 0.0, "Avg_StatesExpanded": 0, "IPC_Score": 0.0, "Delta_vs_Baseline": "N/A", "Delta_vs_Previous": "N/A", "Is_Best_So_Far": False, "LLM_Rationale": rationale, "Termination_Reason": "N/A" if iteration < max_iter else "MAX_ITER", "LLM_Input_Tokens": input_toks, "LLM_Output_Tokens": output_toks, "Domain_File_Path": "N/A", "Timestamp": datetime.datetime.now().isoformat()})
            print(f"[{llm_model} | {planner_name} | {domain_name}] Iteration {iteration}: Validation Failed at {failed_stage}")
            continue

        Path(tmp_domain_path).write_text(val_result.extracted_pddl, encoding="utf-8")
        
        # Create a temporary file in the benchmark directory for Docker mount compatibility
        eval_domain_dir = os.path.join(REPO_ROOT, "benchmarks", domain_name, "tmp_stage3")
        os.makedirs(eval_domain_dir, exist_ok=True)
        eval_domain_path = os.path.join(eval_domain_dir, f"domain_iter{iteration}.pddl")
        Path(eval_domain_path).write_text(val_result.extracted_pddl, encoding="utf-8")
        
        print(f"[{llm_model} | {planner_name} | {domain_name}] Iteration {iteration}: Executing Target Planner on test instances (Soft Critic)...")
        current_stats = run_soft_critic(eval_domain_path, planner_name, test_instances)
        mean_ipc_gain = calculate_simple_ipc(baseline_stats, current_stats)
        
        verdict = "IMPROVEMENT" if mean_ipc_gain > 0 else "REGRESSION"
        
        old_cov = baseline_stats['coverage']
        new_cov = current_stats['coverage']
        baseline_avg_time = baseline_stats['total_search_time'] / old_cov if old_cov > 0 else 0
        stage2_avg_time = current_stats['total_search_time'] / new_cov if new_cov > 0 else 0
        baseline_avg_states = int(baseline_stats['total_expanded_states'] / old_cov) if old_cov > 0 else 0
        stage2_avg_states = int(current_stats['total_expanded_states'] / new_cov) if new_cov > 0 else 0
        
        table_str = build_telemetry_table(baseline_stats, current_stats)
        diag_str, direc_str = meta_controller_diagnostics(baseline_stats, current_stats, mean_ipc_gain)

        telemetry_feedback = f"""[EXECUTION FEEDBACK — ITERATION {iteration + 1}]

Your Iteration {iteration} reordering was tested on {planner_name} across all 15
problem instances. Here are the results compared to the BASELINE:

OVERALL PERFORMANCE SUMMARY:
• Instances solved: {new_cov}/15 (Baseline: {old_cov}/15)
• Average run wall time (solved): {stage2_avg_time:.2f}s (Baseline: {baseline_avg_time:.2f}s)
• Average states expanded (solved): {stage2_avg_states} (Baseline: {baseline_avg_states})
• Mean IPC Gain vs Baseline: {mean_ipc_gain:.3f}
• Verdict: {verdict}

PER-INSTANCE BREAKDOWN:
{table_str}

DIAGNOSTIC ANALYSIS:
{diag_str}

IMPROVEMENT DIRECTION:
{direc_str}"""

        history_buffer.append(f"Iteration {iteration}:\n  • Your Strategy: \"{rationale}\"\n  • Result: {new_cov}/15 solved, avg search time {stage2_avg_time:.2f}s, avg states expanded {stage2_avg_states}, Mean IPC Gain vs baseline: {mean_ipc_gain:.3f}.\n    Verdict: {verdict}.")

        iter_ipc_abs = 0.0
        for inst_name, base_data in baseline_stats["instances"].items():
            t_base = base_data.get("runtime", None)
            t_cur = current_stats["instances"].get(inst_name, {}).get("runtime", None)
            if t_base is not None and t_cur is not None:
                t_star = min(t_base, t_cur)
                if t_star == 0: t_star = 0.001
                ratio_cur = max(1.0, t_cur / t_star)
                iter_ipc_abs += 1.0 / (1.0 + np.log10(ratio_cur))
            elif t_cur is not None:
                iter_ipc_abs += 1.0
                
        delta_prev = iter_ipc_abs - last_ipc
        last_ipc = iter_ipc_abs

        is_best = False
        if iter_ipc_abs > best_score:
            is_best = True
            best_score = iter_ipc_abs
            best_domain_path = tmp_domain_path
            best_iter_num = iteration

        current_domain_str = val_result.extracted_pddl
        
        all_timeout = current_stats["coverage"] == 0 and baseline_stats["coverage"] == 0
        term_reason = "ALL_TIMEOUT" if all_timeout else ("MAX_ITER" if iteration == max_iter else "N/A")
        
        log_to_csv(csv_path, {"Triple_ID": f"{domain_name}_{planner_name}_{llm_model}", "Domain": domain_name, "LLM": llm_model, "Target_Planner": planner_name, "Iteration": iteration, "Validation_Status": "VALID", "V4_Failure_Detail": "N/A", "Coverage": new_cov/15.0, "Avg_Run_Wall_s": stage2_avg_time, "Avg_StatesExpanded": stage2_avg_states, "IPC_Score": iter_ipc_abs, "Delta_vs_Baseline": mean_ipc_gain, "Delta_vs_Previous": delta_prev, "Is_Best_So_Far": is_best, "LLM_Rationale": rationale, "Termination_Reason": term_reason, "LLM_Input_Tokens": input_toks, "LLM_Output_Tokens": output_toks, "Domain_File_Path": tmp_domain_path, "Timestamp": datetime.datetime.now().isoformat()})

        if all_timeout:
            print(f"[{llm_model} | {planner_name} | {domain_name}] Iteration {iteration}: ALL_TIMEOUT activated. Ending loop early.")
            break

    # Determine what domains are finally sent out
    final_best_dir = os.path.join(output_dir, "Best Stage 3 Domains", llm_model.replace('/','-'), planner_name, domain_name)
    os.makedirs(final_best_dir, exist_ok=True)
    final_output_path = os.path.join(final_best_dir, f"{domain_name}_{llm_model.replace('/','-')}_Feedback_{planner_name}.pddl")

    if best_domain_path:
        Path(final_output_path).write_text(Path(best_domain_path).read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Feedback loop complete. Final best domain saved to {final_output_path} (Score: {best_score})")
    else:
        # Defaults to Stage 2 seed if valid, else Stage 0 baseline.
        Path(final_output_path).write_text(Path(base_domain_path).read_text(encoding="utf-8"), encoding="utf-8")
        print("Feedback loop complete, but NO VALID BEST DOMAIN was produced. Used fallback.")
        
    imp_vs_seed = best_score - seed_score
    was_stage2 = not is_valid_seed
    
    log_to_csv(final_domains_csv, {
        "Triple_ID": f"{domain_name}_{planner_name}_{llm_model}",
        "Domain": domain_name,
        "LLM": llm_model,
        "Target_Planner": planner_name,
        "Best_Iteration": best_iter_num,
        "Total_Iterations_Run": iteration,
        "Termination_Reason": term_reason if term_reason != "N/A" else "MAX_ITER",
        "Best_IPC_Score": best_score,
        "Seed_IPC_Score": seed_score,
        "Improvement_vs_Seed": imp_vs_seed,
        "Validation_Failures_Total": cumulative_failures,
        "V4_Semantic_Failures": v4_semantic_failures,
        "Was_Stage2_Failure": was_stage2,
        "Stage3_Domain_Path": final_output_path
    })
