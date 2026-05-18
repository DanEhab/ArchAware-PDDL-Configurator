import numpy as np

def calculate_simple_ipc(baseline_stats, current_stats):
    ipc_gains = []
    base_insts = baseline_stats["instances"]
    cur_insts = current_stats["instances"]
    
    for inst_name, base_data in base_insts.items():
        t_base = base_data.get("runtime")
        cur_data = cur_insts.get(inst_name, {})
        t_cur = cur_data.get("runtime", None)
        
        score_base = 0.0
        score_cur = 0.0
        
        if t_base is not None and t_cur is not None:
            t_star = min(t_base, t_cur)
            if t_star == 0: t_star = 0.001
            ratio_base = max(1.0, t_base / t_star)
            ratio_cur = max(1.0, t_cur / t_star)
            score_base = 1.0 / (1.0 + np.log10(ratio_base))
            score_cur = 1.0 / (1.0 + np.log10(ratio_cur))
        elif t_base is not None:
            score_base = 1.0
            score_cur = 0.0
        elif t_cur is not None:
            score_base = 0.0
            score_cur = 1.0
            
        ipc_gains.append(score_cur - score_base)
        
    return np.mean(ipc_gains) if ipc_gains else 0.0

def build_telemetry_table(baseline_stats, current_stats):
    table = []
    table.append("┌──────────────┬──────────┬────────────┬─────────────┬──────────────┬───────────┐")
    table.append("│ Instance     │ Status   │ Search (s) │ States Exp. │ IPC Score    │ IPC Gain  │")
    table.append("├──────────────┼──────────┼────────────┼─────────────┼──────────────┼───────────┤")
    
    base_insts = baseline_stats["instances"]
    cur_insts = current_stats["instances"]
    
    for inst_name in sorted(base_insts.keys()):
        base_data = base_insts[inst_name]
        cur_data = cur_insts.get(inst_name, {})
        
        status = cur_data.get("status", "TIMEOUT")
        t_cur = cur_data.get("runtime", None)
        t_base = base_data.get("runtime", None)
        states = cur_data.get("states", "N/A")
        
        score_base = 0.0
        score_cur = 0.0
        if t_base is not None and t_cur is not None:
            t_star = min(t_base, t_cur)
            if t_star == 0: t_star = 0.001
            ratio_base = max(1.0, t_base / t_star)
            ratio_cur = max(1.0, t_cur / t_star)
            score_base = 1.0 / (1.0 + np.log10(ratio_base))
            score_cur = 1.0 / (1.0 + np.log10(ratio_cur))
        elif t_base is not None:
            score_base = 1.0
            score_cur = 0.0
        elif t_cur is not None:
            score_base = 0.0
            score_cur = 1.0
            
        gain = score_cur - score_base
        t_cur_str = f"{t_cur:.2f}" if t_cur is not None else "N/A"
        states_str = str(states) if states is not None else "N/A"
        
        status_v = status.ljust(8)
        time_v = t_cur_str.ljust(10)
        state_v = states_str.ljust(11)
        score_v = f"{score_cur:.3f}".ljust(12)
        gain_v = f"{gain:+.3f}".ljust(9)
        
        name_v = inst_name.ljust(12)[:12]
        
        table.append(f"│ {name_v} │ {status_v} │ {time_v} │ {state_v} │ {score_v} │ {gain_v} │")
        
    table.append("└──────────────┴──────────┴────────────┴─────────────┴──────────────┴───────────┘")
    return "\n".join(table)

def meta_controller_diagnostics(baseline_stats, current_stats, mean_ipc_gain):
    old_cov = baseline_stats["coverage"]
    new_cov = current_stats["coverage"]
    baseline_avg_time = baseline_stats["total_search_time"] / old_cov if old_cov > 0 else 0
    stage2_avg_time = current_stats["total_search_time"] / new_cov if new_cov > 0 else 0
    baseline_avg_states = baseline_stats["total_expanded_states"] / old_cov if old_cov > 0 else 0
    stage2_avg_states = current_stats["total_expanded_states"] / new_cov if new_cov > 0 else 0

    diag = []
    delta_cov = new_cov - old_cov
    
    if delta_cov < 0:
        diag.append(f"⚠ WARNING: Your reordering REDUCED coverage from {old_cov}/15 to {new_cov}/15. The planner could not find plans for instances it previously solved.")
    elif delta_cov > 0:
        diag.append(f"✓ POSITIVE: Your reordering INCREASED coverage from {old_cov}/15 to {new_cov}/15.")
        
    if old_cov > 0 and new_cov > 0:
        if stage2_avg_states > 1.1 * baseline_avg_states:
            diag.append(f"The planner expanded significantly more states ({int(stage2_avg_states)} vs {int(baseline_avg_states)}), suggesting the ordering causes less productive search branches.")
        elif stage2_avg_states < 0.95 * baseline_avg_states:
            diag.append(f"✓ POSITIVE: Fewer states expanded ({int(stage2_avg_states)} vs {int(baseline_avg_states)}), indicating improved heuristic pruning.")
            
        if stage2_avg_time > 1.1 * baseline_avg_time:
            diag.append(f"Average run wall time increased from {baseline_avg_time:.2f}s to {stage2_avg_time:.2f}s, indicating slower convergence.")
        elif stage2_avg_time < 0.95 * baseline_avg_time:
            diag.append(f"✓ POSITIVE: Average run wall time decreased from {baseline_avg_time:.2f}s to {stage2_avg_time:.2f}s.")
            
    if mean_ipc_gain < -0.001:
        diag.append(f"Mean IPC Gain is negative ({mean_ipc_gain:.3f}), indicating overall performance degradation.")
    elif mean_ipc_gain > 0.001:
        diag.append(f"✓ POSITIVE: Mean IPC Gain is positive ({mean_ipc_gain:.3f}), indicating overall performance improvement.")
        
    if new_cov == 0 and old_cov == 0:
        diag.append("Both original and reordered domains timed out on all instances. This pair may be inherently unsolvable within the time limit.")
        
    if not diag:
        diag.append("No measurable change detected. Try a more substantial structural rearrangement.")
        
    improvement_detected = mean_ipc_gain > 0
    
    direc = []
    if improvement_detected:
        t_outs = 15 - new_cov
        direc.append(f"Your previous reordering already shows improvement (Mean IPC Gain: {mean_ipc_gain:.3f}). Try to further optimize for the {t_outs} instances that still timed out.")
    else:
        if delta_cov < 0:
            direc.append("Your reordering lost coverage. Prioritize structural orderings that maintain solvability before optimizing speed.")
        elif stage2_avg_states > 1.05 * baseline_avg_states:
            direc.append("Your reordering caused more search states. Re-examine predicate and action ordering to improve heuristic guidance.")
        elif new_cov == 0 and old_cov == 0:
             direc.append("Both baseline and reordered domains timed out on all instances. Try a fundamentally different structural approach.")
        else:
             direc.append("Your previous reordering did not produce a statistically significant improvement. Try a different structural strategy.")

    return "\n".join(diag), "\n".join(direc)

def build_telemetry_for_valid(row, domain, planner, llm):
    # This retrieves improvement data, but expects a pre-loaded pandas row 
    # Because of dependency, we pass the row data directly if possible.
    # Actually, the logic looks up CSV directly, so we can keep the CSV lookup here if we pass REPO_ROOT.
    pass

# We will adapt build_telemetry_for_valid to be independent of REPO_ROOT by passing df or path.
def build_telemetry_for_valid_full(domain, planner, llm, imp_csv_path, stage2_stats, baseline_stats):
    import os
    import pandas as pd
    
    if not os.path.exists(imp_csv_path):
        return "[EXECUTION FEEDBACK]\nError tracking improvement."
        
    df = pd.read_csv(imp_csv_path)
    
    # Map raw LLM name to Stage 2 CSV format
    llm_map = {
        "gpt-5.4-2026-03-05": "gpt-5.4",
        "claude-opus-4.6": "claude-opus-4-6",
        "gemini-3.1-pro": "gemini-3.1-pro",
        "deepseek-r1": "deepseek-reasoner"
    }
    
    llm_search = llm
    for k, v in llm_map.items():
        if k in llm or llm in k:
            llm_search = v
            break
            
    match = df[(df['Domain'] == domain) & (df['Target_Planner'] == planner) & (df['LLM'].str.contains(llm_search, regex=False, na=False))]
    if match.empty:
        return "[EXECUTION FEEDBACK]\nNo precise improvement data found for your previous reordering."
        
    m = match.iloc[0]
    imp_detected = m['IMPROVEMENT_DETECTED'] == True
    mean_ipc = m['Mean_IPC_Gain']
    failed_conditions = []
    
    if not imp_detected:
        if not m['Statistical_Significance']: failed_conditions.append("Statistical_Significance")
        if not m['Practical_Significance']: failed_conditions.append("Practical_Significance")
        if not m['Coverage_Preserved']: failed_conditions.append("Coverage_Preserved")
    
    stage2_solved = stage2_stats["coverage"]
    baseline_solved = baseline_stats["coverage"]
    
    stage2_avg_time = stage2_stats["total_search_time"] / stage2_solved if stage2_solved > 0 else 0
    baseline_avg_time = baseline_stats["total_search_time"] / baseline_solved if baseline_solved > 0 else 0
    
    stage2_avg_states = int(stage2_stats["total_expanded_states"] / stage2_solved) if stage2_solved > 0 else 0
    baseline_avg_states = int(baseline_stats["total_expanded_states"] / baseline_solved) if baseline_solved > 0 else 0
    
    fb = []
    fb.append("[EXECUTION FEEDBACK]\n")
    fb.append(f"Your previous reordering was tested on {planner} across all 15")
    fb.append("problem instances. Here are the results compared to the BASELINE:\n")
    fb.append("OVERALL PERFORMANCE SUMMARY:")
    fb.append(f"• Instances solved: {stage2_solved}/15 (Baseline: {baseline_solved}/15)")
    fb.append(f"• Average run wall time (solved): {stage2_avg_time:.2f}s (Baseline: {baseline_avg_time:.2f}s)")
    fb.append(f"• Average states expanded (solved): {stage2_avg_states} (Baseline: {baseline_avg_states})")
    fb.append(f"• Mean IPC Gain: {mean_ipc:.3f} (from improvement_results.csv)")
    
    if imp_detected:
        fb.append(f"• Verdict: IMPROVEMENT DETECTED\n")
    else:
        fails_str = ", ".join(failed_conditions)
        fb.append(f"• Verdict: NO IMPROVEMENT — Failed: {fails_str}\n")
        
    fb.append("PER-INSTANCE BREAKDOWN:")
    fb.append(build_telemetry_table(baseline_stats, stage2_stats))
    
    diag_str, direc_str = meta_controller_diagnostics(baseline_stats, stage2_stats, mean_ipc)
    fb.append(f"\nDIAGNOSTIC ANALYSIS:\n{diag_str}")
    fb.append(f"\nIMPROVEMENT DIRECTION:\n{direc_str}")
            
    return "\n".join(fb)

def get_6A_telemetry(error_type, baseline_pddl):
    if "TokenLimitExceeded" in error_type:
        return f"[EXECUTION FEEDBACK]\n\nNo execution data is available because your previous attempt did not\nproduce a complete PDDL domain file.\n\nThe domain below is the ORIGINAL unmodified baseline. You are starting\nfrom scratch. Generate a complete, reordered PDDL domain.\n\nNote: The token output limit has been increased to 8,192 tokens.\nOutput the reordered PDDL efficiently without conversational filler."
    elif "RateLimit" in error_type:
        return f"[EXECUTION FEEDBACK]\n\nNo execution data is available because the previous API call was\nrate-limited.\n\nThe domain below is the ORIGINAL unmodified baseline. Generate a\ncomplete, reordered PDDL domain."
    elif "Filter" in error_type or "Safety" in error_type:
        return f"[EXECUTION FEEDBACK]\n\nNo execution data is available because the previous response was\nblocked by safety filters.\n\nThe domain below is the ORIGINAL unmodified baseline. Generate ONLY\nthe reordered PDDL domain file without any additional commentary."
    elif "Server" in error_type or "Network" in error_type or "Timeout" in error_type:
        return f"[EXECUTION FEEDBACK]\n\nNo execution data is available because the previous API call failed.\n\nThe domain below is the ORIGINAL unmodified baseline. Generate a\ncomplete, reordered PDDL domain."
    else:
        return f"[EXECUTION FEEDBACK]\n\nNo execution data is available due to a previous error.\n\nThe domain below is the ORIGINAL unmodified baseline. Generate a\ncomplete, reordered PDDL domain."

def get_6C_telemetry(failed_stage, error_str, baseline_pddl):
    if failed_stage == "V4":
        return f"[EXECUTION FEEDBACK]\n\nNo execution data is available because your previous attempt was\nREJECTED for changing the domain's logical semantics.\n\n⚠ CRITICAL: You must ONLY reorder existing elements. Do NOT:\n  - Add or remove preconditions\n  - Add or remove effects\n  - Change parameter types\n  - Rename predicates or actions\n\nThe domain below is the ORIGINAL unmodified baseline. Start over and\nensure you ONLY change the ORDER of elements, not their content."
    elif failed_stage == "V2":
         return f"[EXECUTION FEEDBACK]\n\nNo execution data is available because your previous attempt contained\nsyntax errors that prevented planner execution.\n\nVAL Error Output:\n{error_str}\n\nThe domain below is the ORIGINAL unmodified baseline. Fix these syntax\nissues. Remember: you must ONLY reorder elements, not modify them."
    elif failed_stage == "V3":
         return f"[EXECUTION FEEDBACK]\n\nNo execution data is available because your previous attempt produced\nan identical copy of the input domain with no changes.\n\nThe domain below is the ORIGINAL unmodified baseline. You MUST reorder\nthe elements (predicates, actions, preconditions, effects) according\nto the architecture-aware rules above. Do not return the domain\nunchanged."
    else:
         return f"[EXECUTION FEEDBACK]\n\nNo execution data is available because your previous attempt did not\nproduce a parseable PDDL domain.\n\nThe domain below is the ORIGINAL unmodified baseline. Output ONLY the\ncomplete reordered PDDL domain file — no explanations, no markdown\nfencing, no commentary. Start your PDDL output directly with\n\"(define (domain ...\"."
