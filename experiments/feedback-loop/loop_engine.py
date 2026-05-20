import os
import sys
import datetime
from datetime import timezone
from pathlib import Path

REPO_ROOT = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

# Handle directories with hyphens
sys.path.insert(0, str(REPO_ROOT / "experiments" / "general-prompt"))
sys.path.insert(0, str(REPO_ROOT / "experiments" / "feedback-loop"))

from validation_and_evaluation.scripts.validation.validation_pipeline import validate_domain
from experiments.base.planner_runner import execute_planner
from llms.llm_providers import get_provider, TokenLimitError, RateLimitError, LLMProviderError  # type: ignore
import yaml
import json
import numpy as np

from csv_manager_stage3 import log_to_csv, log_diff_metrics, log_planner_execution, log_llm_generation  # type: ignore
from rationale_extractor import extract_rationale  # type: ignore
from meta_controller import calculate_simple_ipc, build_telemetry_table, meta_controller_diagnostics  # type: ignore
from prompt_builder import build_feedback_prompt  # type: ignore
from validation_and_evaluation.scripts.validation.validation_pipeline import save_validation_json
from baseline_loader import load_baseline_stats, load_stage2_stats, compute_seed_ipc  # type: ignore
from error_handler_stage3 import ErrorHandlerStage3  # type: ignore

CONFIG_PATH = REPO_ROOT / "config" / "experiment_config.yaml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)
DOCKER_CFG = CONFIG["docker"]

# --- Error handlers (module-level singletons, thread-safe) ---
PLANNER_ERROR_HANDLER = ErrorHandlerStage3(
    error_register_path=REPO_ROOT / "logs" / "stage3" / "error_register.csv",
    error_dumps_dir=REPO_ROOT / "logs" / "stage3" / "error_dumps",
)
LLM_ERROR_HANDLER = ErrorHandlerStage3(
    error_register_path=REPO_ROOT / "logs" / "stage3" / "LLM_run" / "error_register.csv",
    error_dumps_dir=REPO_ROOT / "logs" / "stage3" / "LLM_run" / "error_dumps",
)

UI_QUEUE = None

def set_ui_queue(q):
    global UI_QUEUE
    UI_QUEUE = q

def push_log(llm, event_type, message):
    if UI_QUEUE:
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        llm_pad = f"{llm:<8}"[:8]
        evt_pad = f"[{event_type}]"
        raw_msg = f"[{timestamp}] [{llm_pad}] {evt_pad:<11} {message}"
        UI_QUEUE.put(("LOG", llm, event_type, message, raw_msg))
    else:
        print(f"[{llm}] [{event_type}] {message}")

def push_pipeline(llm, current, total, text):
    if UI_QUEUE:
        UI_QUEUE.put(("PIPELINE_UPDATE", llm, current, total, text))

def push_complete(triple_id, total_iters, verdict, delta):
    if UI_QUEUE:
        UI_QUEUE.put(("TRIPLE_COMPLETE", triple_id, total_iters, verdict, delta))


def run_soft_critic(domain_pddl_path, planner_name, test_instances, llm_model=None, stage=None, prompt_id=None, domain_name=None, iteration=None):
    results = {
        "coverage": 0,
        "total_instances": len(test_instances),
        "total_search_time": 0.0,
        "total_expanded_states": 0,
        "total_generated_states": 0,
        "instance_statuses": [],
        "instances": {} 
    }
    
    # Pre-calculate llm name for logs
    llm_for_log = llm_model if llm_model else "Unknown"
    
    for instance_path in test_instances:
        inst_name = os.path.basename(instance_path)
        iter_str = f"iter{iteration}" if iteration is not None else "iter0"
        d_name = domain_name if domain_name else "unknown"
        short_path = f"{d_name}/{iter_str}/{inst_name}"
        
        push_log(llm_for_log, "RUN", f"{planner_name:<7} | {short_path} ...")
        
        docker_image = f"{planner_name}_planner"
        res = execute_planner(
            planner_name=planner_name, 
            docker_image=docker_image, 
            domain_path=Path(domain_pddl_path), 
            problem_path=Path(instance_path),
            docker_cfg=DOCKER_CFG
        )
        status = res.get("Output_Status", "FAILURE")
        
        results['instance_statuses'].append((inst_name, status))
        
        # Build proper CSV row with all expected fields (Bug fix #5: Stage column)
        stage_name = stage or (f"Feedback_Loop{iteration}" if iteration else "Feedback_Loop")
        
        # Build numeric Prompt ID per spec: 1.iter=lama, 2.iter=decstar, 3.iter=bfws, 4.iter=madagascar
        PROMPT_ID_NUM_MAP = {"lama": 1, "decstar": 2, "bfws": 3, "madagascar": 4}
        numeric_prompt_id = prompt_id
        if prompt_id is None and planner_name and iteration is not None:
            pnum = PROMPT_ID_NUM_MAP.get(planner_name.lower(), 0)
            numeric_prompt_id = f"{pnum}.{iteration}" if pnum else prompt_id
        domain_file_name = os.path.basename(domain_pddl_path)
        csv_row = {
            "Run_ID": f"{d_name}_{planner_name}_{llm_for_log}_iter{iteration}_{inst_name}",
            "Domain_Name": d_name,
            "Domain_File": domain_file_name,
            "Problem_Instance": inst_name,
            "Planner_Used": planner_name,
            "Stage": stage_name,
            "LLM_Used": llm_model or "N/A",
            "PromptID": numeric_prompt_id or "N/A",
            "PlanCost": res.get("PlanCost"),
            "Runtime_internal_s": res.get("Runtime_internal_s"),
            "Runtime_wall_s": res.get("Runtime_wall_s"),
            "Output_Status": status,
            "StatesExpanded": res.get("StatesExpanded"),
            "StatesGenerated": res.get("StatesGenerated"),
            "StatesEvaluated": res.get("StatesEvaluated"),
            "PeakMemoryKB": res.get("PeakMemoryKB"),
            "Timestamp": datetime.datetime.now(timezone.utc).isoformat(),
        }
        log_planner_execution(csv_row, str(REPO_ROOT))
        
        # Bug fix #10: Log planner errors to error handler
        if status in ("TIMEOUT", "MEMOUT", "FAILURE"):
            PLANNER_ERROR_HANDLER.log_planner_error(
                domain=d_name, problem=inst_name, planner=planner_name,
                llm=llm_for_log, iteration=iteration or 0,
                error_type=status,
                stdout=res.get("_stdout", ""), stderr=res.get("_stderr", ""),
            )
        
        runtime = float(res.get("Runtime_wall_s") or 0.0) if status == "SUCCESS" else None
        states = int(res.get("StatesExpanded") or 0) if status == "SUCCESS" else None
        
        if status == "SUCCESS":
            push_log(llm_for_log, "SUCCESS", f"{planner_name:<7} | {short_path} | wall={runtime:.1f}s")
        elif status == "TIMEOUT":
            push_log(llm_for_log, "TIMEOUT", f"{planner_name:<7} | {short_path} | wall=360.0s")
        elif status == "MEMOUT":
            push_log(llm_for_log, "MEMOUT", f"{planner_name:<7} | {short_path} | wall=OOM")
        else:
            push_log(llm_for_log, "ERROR", f"{planner_name:<7} | {short_path} | {status}")
        
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
    # Bug fix #8: Use feedback-loop/prompts (not arch-aware/prompts)
    prompt_dir = os.path.join(REPO_ROOT, "experiments", "feedback-loop", "prompts")

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
    
    # Bug fix #1: Load baseline from CSV instead of re-running planner
    baseline_stats = load_baseline_stats(domain_name, planner_name, str(REPO_ROOT))
    if baseline_stats["total_instances"] == 0:
        push_log(llm_model, "WARN", f"No baseline CSV data for {domain_name}+{planner_name}. Falling back to planner run.")
        baseline_stats = run_soft_critic(stage0_baseline_path, planner_name, test_instances, llm_model=llm_model, domain_name=domain_name, iteration=0)
    
    # Bug fix #2: Load Stage 2 seed data from CSV instead of re-running planner
    stage2_stats = None
    if initial_telemetry_feedback == "DELAY_VALID_TELEMETRY":
        stage2_stats = load_stage2_stats(domain_name, planner_name, llm_model, str(REPO_ROOT))
        
        if stage2_stats["total_instances"] == 0:
            push_log(llm_model, "WARN", f"No Stage 2 CSV data. Falling back to planner run.")
            
            # Put fallback iter0 domain in the benchmark tree so Docker volume mounts correctly (relative_to fix)
            eval_domain_dir = os.path.join(REPO_ROOT, "benchmarks", domain_name, "tmp_stage3")
            os.makedirs(eval_domain_dir, exist_ok=True)
            eval_domain_path = os.path.join(eval_domain_dir, f"domain_iter0.pddl")
            Path(eval_domain_path).write_text(current_domain_str, encoding="utf-8")
            
            stage2_stats = run_soft_critic(eval_domain_path, planner_name, test_instances, llm_model=llm_model, domain_name=domain_name, iteration=0)
        
        from meta_controller import build_telemetry_for_valid_full
        imp_csv = os.path.join(REPO_ROOT, "results", "arch_aware", "improvement", "improvement_results.csv")
        initial_telemetry_feedback = build_telemetry_for_valid_full(domain_name, planner_name, llm_model, imp_csv, stage2_stats, baseline_stats)
        
        # Bug fix #6: Use compute_seed_ipc() instead of inline calc
        best_score = compute_seed_ipc(baseline_stats, stage2_stats)
        seed_score = best_score
        
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

    # Bug fix #6: Only set from stage2_best_score for non-valid seeds.
    # For valid seeds, best_score was already computed above via compute_seed_ipc().
    if stage2_stats is None:
        best_score = float(stage2_best_score)
        seed_score = float(stage2_best_score)
    best_domain_path = None if not is_valid_seed else base_domain_path
    
    verdict = None # Track across iterations
    best_iter_num = 0
    term_reason = "MAX_ITER"
    last_ipc = seed_score
    # Bug fix #7: Initialize all_timeout before the loop
    all_timeout = False
    iteration = 0  # Safe default for post-loop access

    # Prompt ID mapping per spec: 1.x=lama, 2.x=decstar, 3.x=bfws, 4.x=madagascar
    PROMPT_ID_MAP = {"lama": 1, "decstar": 2, "bfws": 3, "madagascar": 4}
    planner_num = PROMPT_ID_MAP.get(planner_name.lower(), 0)
    
    for iteration in range(1, max_iter + 1):
        push_log(llm_model, "INFO", f"{domain_name}+{planner_name} | Starting Iteration {iteration}/{max_iter}")
        
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

        # Numeric Prompt ID per spec: e.g., 1.1 = Lama Iteration 1
        current_prompt_id = f"{planner_num}.{iteration}"
        
        prompt_log_path = os.path.join(prompt_save_dir, f"{domain_name}_{llm_model.replace('/','-')}_{planner_name}_iter{iteration}_prompt.txt")
        Path(prompt_log_path).write_text(prompt_text, encoding="utf-8")

        llm_error_str = "SUCCESS"
        elapsed, input_toks, output_toks = 0.0, 0, 0
        try:
            push_log(llm_model, "LLM_GEN", f"{domain_name}+{planner_name} | Iter {iteration}: Prompt sent, awaiting generation...")
            llm_response, elapsed, input_toks, output_toks = llm.generate(prompt_text)
            push_log(llm_model, "LLM_RECV", f"{domain_name}+{planner_name} | Iter {iteration}: Output received ({output_toks} tokens).")
        except (TokenLimitError, RateLimitError) as e:
            # Recoverable LLM error — retry on next iteration instead of aborting
            llm_error_str = str(e)
            is_token_error = isinstance(e, TokenLimitError)
            error_label = "TokenLimitExceeded" if is_token_error else "RateLimit"
            push_log(llm_model, "LLM_ERROR", f"{domain_name}+{planner_name} | Iter {iteration}: Recoverable {error_label}. Will retry. {llm_error_str[:80]}")
            
            LLM_ERROR_HANDLER.log_llm_error(
                domain=domain_name, planner=planner_name, llm=llm_model,
                iteration=iteration, error_type=f"LLM_{error_label}",
                prompt_text=prompt_text, error_message=llm_error_str,
            )
            
            log_llm_generation({
                "ID": f"{domain_name}_{planner_name}_{llm_model}_iter{iteration}",
                "Domain Name": domain_name, "LLM Model": llm_model,
                "Prompt ID": current_prompt_id,
                "LLM_Status": f"Failed: {llm_error_str[:200]}",
                "LLM API Time S": elapsed,
                "Input Tokens Consumed": input_toks,
                "Output Tokens Generated": output_toks,
                "Path to Raw LLM Response": "N/A",
                "Passed Stage V1": False, "Path to Extracted PDDL": "N/A",
                "Passed VAL Syntactic Check (V2)": False,
                "VAL_error_string": "N/A", "Passed V3": False, "Passed V4": False,
                "Validation Status": "LLM_ERROR",
            }, str(REPO_ROOT))
            
            # Add failure to history buffer so next iteration knows what happened
            if is_token_error:
                history_buffer.append(f"Iteration {iteration}:\n  • Status: FAILED — Your response exceeded the maximum token output limit and was truncated.\n  • No valid PDDL domain was produced.")
                telemetry_feedback = f"[EXECUTION FEEDBACK — ITERATION {iteration + 1}]\n\nYour Iteration {iteration} response was truncated because it exceeded the token output limit.\n\nThe domain below is your current working domain. Output the reordered PDDL efficiently without conversational filler.\nNote: The token output limit is 8,192 tokens."
            else:
                history_buffer.append(f"Iteration {iteration}:\n  • Status: FAILED — API rate limit was exceeded.\n  • No valid PDDL domain was produced.")
                telemetry_feedback = f"[EXECUTION FEEDBACK — ITERATION {iteration + 1}]\n\nYour Iteration {iteration} could not be processed due to API rate limiting. This was not your fault.\n\nThe domain below is your current working domain. Generate a complete, reordered PDDL domain."
            
            # Log to iteration tracking CSV
            log_to_csv(csv_path, {"Triple_ID": f"{domain_name}_{planner_name}_{llm_model}", "Domain": domain_name, "LLM": llm_model, "Target_Planner": planner_name, "Iteration": iteration, "Validation_Status": f"LLM_{error_label}", "V4_Failure_Detail": "N/A", "Coverage": 0.0, "Avg_Run_Wall_s": 0.0, "Avg_StatesExpanded": 0, "IPC_Score": 0.0, "Delta_vs_Baseline": "N/A", "Delta_vs_Previous": "N/A", "Is_Best_So_Far": False, "LLM_Rationale": "N/A", "Termination_Reason": "N/A" if iteration < max_iter else "MAX_ITER", "LLM_Input_Tokens": input_toks, "LLM_Output_Tokens": output_toks, "Domain_File_Path": "N/A", "Timestamp": datetime.datetime.now().isoformat()})
            
            cumulative_failures += 1
            verdict = "FAILED_VALIDATION"  # Treat as failed for next-iteration task block
            continue  # Retry on next iteration
            
        except Exception as e:
            llm_error_str = str(e)
            push_log(llm_model, "LLM_ERROR", f"{domain_name}+{planner_name} | Iter {iteration}: Fatal API Error. {llm_error_str[:100]}")
            
            LLM_ERROR_HANDLER.log_llm_error(
                domain=domain_name, planner=planner_name, llm=llm_model,
                iteration=iteration, error_type="LLM_API_ERROR",
                prompt_text=prompt_text, error_message=llm_error_str,
            )
            
            log_llm_generation({
                "ID": f"{domain_name}_{planner_name}_{llm_model}_iter{iteration}",
                "Domain Name": domain_name, "LLM Model": llm_model,
                "Prompt ID": current_prompt_id,
                "LLM_Status": f"Failed: {llm_error_str[:200]}",
                "LLM API Time S": elapsed,
                "Input Tokens Consumed": input_toks,
                "Output Tokens Generated": output_toks,
                "Path to Raw LLM Response": "N/A",
                "Passed Stage V1": False, "Path to Extracted PDDL": "N/A",
                "Passed VAL Syntactic Check (V2)": False,
                "VAL_error_string": "N/A", "Passed V3": False, "Passed V4": False,
                "Validation Status": "LLM_ERROR",
            }, str(REPO_ROOT))
            
            term_reason = "LLM_ERROR"
            break

        rationale = extract_rationale(llm_response)
        
        llm_resp_path = os.path.join(llm_resp_dir, f"{domain_name}_{llm_model.replace('/','-')}_{planner_name}_iter{iteration}.txt")
        Path(llm_resp_path).write_text(llm_response, encoding="utf-8")

        push_log(llm_model, "VALIDATE", f"{domain_name}+{planner_name} | Iter {iteration}: Running V1-V4 Validation Pipeline (Hard Critics)...")
        tmp_domain_path = os.path.join(run_dir, f"{domain_name}_{llm_model.replace('/','-')}_Feedback_{planner_name}_iter{iteration}.pddl")
        
        problem_file_path_obj = Path(test_instances[0]) if test_instances else None
        val_result = validate_domain(llm_response, Path(stage0_baseline_path), problem_file_path_obj)
        val_status = val_result.status
        
        # Save Validation JSON to feedback_loop directory (not results/Feedback_Loop{N}/)
        # The JSON goes to: validation_and_evaluation/data/production/feedback_loop/diffs/{LLM}/Iteration{N}/...
        json_stage = "feedback_loop"
        run_id = f"{planner_name}_iter{iteration}"
        
        # Override save path to avoid creating spurious results/Feedback_LoopN/ directories
        json_save_dir = REPO_ROOT / "validation_and_evaluation" / "data" / "production" / "feedback_loop" / "diffs" / llm_model.replace('/','-') / f"Iteration{iteration}" / "validation" / domain_name
        json_save_dir.mkdir(parents=True, exist_ok=True)
        json_filename = f"{domain_name}__{llm_model.replace('/','-')}__{json_stage}__{run_id}.validation.json"
        json_path = json_save_dir / json_filename
        
        report = val_result.to_production_dict(domain_name, llm_model.replace('/','-'), json_stage, run_id)
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(report, jf, indent=2, ensure_ascii=False)
        
        pddl_len = len(val_result.extracted_pddl) if val_result.extracted_pddl else 0
        
        log_diff_metrics(
            diff_features=val_result.diff_features,
            status=val_status,
            reason=val_result.reason,
            failed_stage=val_result.failed_stage,
            llm_id=f"{domain_name}_{planner_name}_{llm_model.replace('/','-')}",
            domain=domain_name,
            model_id=llm_model,
            iteration=iteration,
            json_path=str(json_path),
            pddl_length=pddl_len,
            repo_root=REPO_ROOT
        )
        
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
            
            # Bug fix #3: Log LLM generation for failed validation
            log_llm_generation({
                "ID": f"{domain_name}_{planner_name}_{llm_model}_iter{iteration}",
                "Domain Name": domain_name, "LLM Model": llm_model,
                "Prompt ID": current_prompt_id,
                "LLM_Status": "Passed", "LLM API Time S": elapsed,
                "Input Tokens Consumed": input_toks,
                "Output Tokens Generated": output_toks,
                "Path to Raw LLM Response": llm_resp_path,
                "Passed Stage V1": failed_stage != "V1",
                "Path to Extracted PDDL": "N/A",
                "Passed VAL Syntactic Check (V2)": failed_stage not in ("V1", "V2"),
                "VAL_error_string": val_result.reason or "N/A",
                "Passed V3": failed_stage not in ("V1", "V2", "V3"),
                "Passed V4": False,
                "Validation Status": f"INVALID_{failed_stage}",
            }, str(REPO_ROOT))
            
            push_log(llm_model, "VALIDATE", f"{domain_name}+{planner_name} | Iter {iteration}: {failed_stage} Failure! ({reason[:60] if failed_stage != 'V4' else v4_detail[:60]})")
            continue

        Path(tmp_domain_path).write_text(val_result.extracted_pddl, encoding="utf-8")
        
        # Create a temporary file in the benchmark directory for Docker mount compatibility
        eval_domain_dir = os.path.join(REPO_ROOT, "benchmarks", domain_name, "tmp_stage3")
        os.makedirs(eval_domain_dir, exist_ok=True)
        eval_domain_path = os.path.join(eval_domain_dir, f"domain_iter{iteration}.pddl")
        Path(eval_domain_path).write_text(val_result.extracted_pddl, encoding="utf-8")
        
        push_log(llm_model, "VALIDATE", f"{domain_name}+{planner_name} | Iter {iteration}: V1-V4 passed successfully.")
        current_stats = run_soft_critic(eval_domain_path, planner_name, test_instances, llm_model=llm_model, domain_name=domain_name, iteration=iteration)
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

        push_log(llm_model, "CRITIQUE", f"{domain_name}+{planner_name} | Iter {iteration}: {new_cov}/15 Solved | IPC: {iter_ipc_abs:.3f} | Delta: {mean_ipc_gain:+.3f}")
        
        if is_best:
            push_log(llm_model, "RESULT", f"{domain_name}+{planner_name} | Iter {iteration}: IMPROVEMENT detected. Setting as best_so_far.")
        else:
            push_log(llm_model, "RESULT", f"{domain_name}+{planner_name} | Iter {iteration}: {verdict} detected. Reverting to Iter {best_iter_num} best.")

        all_timeout = current_stats["coverage"] == 0 and baseline_stats["coverage"] == 0
        term_reason = "ALL_TIMEOUT" if all_timeout else ("MAX_ITER" if iteration == max_iter else "N/A")
        
        log_to_csv(csv_path, {"Triple_ID": f"{domain_name}_{planner_name}_{llm_model}", "Domain": domain_name, "LLM": llm_model, "Target_Planner": planner_name, "Iteration": iteration, "Validation_Status": "VALID", "V4_Failure_Detail": "N/A", "Coverage": new_cov/15.0, "Avg_Run_Wall_s": stage2_avg_time, "Avg_StatesExpanded": stage2_avg_states, "IPC_Score": iter_ipc_abs, "Delta_vs_Baseline": mean_ipc_gain, "Delta_vs_Previous": delta_prev, "Is_Best_So_Far": is_best, "LLM_Rationale": rationale, "Termination_Reason": term_reason, "LLM_Input_Tokens": input_toks, "LLM_Output_Tokens": output_toks, "Domain_File_Path": tmp_domain_path, "Timestamp": datetime.datetime.now().isoformat()})

        # Bug fix #3: Log LLM generation for valid iterations
        log_llm_generation({
            "ID": f"{domain_name}_{planner_name}_{llm_model}_iter{iteration}",
            "Domain Name": domain_name, "LLM Model": llm_model,
            "Prompt ID": current_prompt_id,
            "LLM_Status": "Passed", "LLM API Time S": elapsed,
            "Input Tokens Consumed": input_toks,
            "Output Tokens Generated": output_toks,
            "Path to Raw LLM Response": llm_resp_path,
            "Passed Stage V1": True, "Path to Extracted PDDL": tmp_domain_path,
            "Passed VAL Syntactic Check (V2)": True,
            "VAL_error_string": "N/A", "Passed V3": True, "Passed V4": True,
            "Validation Status": "VALID",
        }, str(REPO_ROOT))

        if all_timeout:
            push_log(llm_model, "TERMINATE", f"{domain_name}+{planner_name} | ALL_TIMEOUT triggered on Iter {iteration}. Ending loop.")
            break
        
        # Bug fix #9: Update current_domain_str to this iteration's output
        # (even if worse), per spec: "Input Domain: The PDDL that Iteration N produced"
        current_domain_str = val_result.extracted_pddl

    # Determine what domains are finally sent out
    final_best_dir = os.path.join(output_dir, "Best Stage 3 Domains", llm_model.replace('/','-'), planner_name, domain_name)
    os.makedirs(final_best_dir, exist_ok=True)
    final_output_path = os.path.join(final_best_dir, f"{domain_name}_{llm_model.replace('/','-')}_Feedback_{planner_name}.pddl")

    if best_domain_path:
        Path(final_output_path).write_text(Path(best_domain_path).read_text(encoding="utf-8"), encoding="utf-8")
        push_log(llm_model, "TERMINATE", f"{domain_name}+{planner_name} | Loop ended. Saved best to final_domains.")
    else:
        # Defaults to Stage 2 seed if valid, else Stage 0 baseline.
        Path(final_output_path).write_text(Path(base_domain_path).read_text(encoding="utf-8"), encoding="utf-8")
        push_log(llm_model, "TERMINATE", f"{domain_name}+{planner_name} | Loop ended. NO VALID BEST DOMAIN. Used fallback.")
        
    imp_vs_seed = best_score - seed_score
    was_stage2 = not is_valid_seed
    
    # Send completion event
    best_delta = best_score - baseline_stats["coverage"] # approximate delta for UI
    vstr = "IMPROVEMENT" if imp_vs_seed > 0 else "ALL_TIMEOUT" if all_timeout else "REGRESSION"
    push_complete(f"{domain_name}, {llm_model}, {planner_name}", iteration, vstr, imp_vs_seed)
    
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

