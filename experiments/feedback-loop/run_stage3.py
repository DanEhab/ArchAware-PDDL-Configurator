import os
import sys
import glob
import time
import concurrent.futures
import pandas as pd
from pathlib import Path
import datetime
import threading
import queue

from rich.console import Console
from rich.text import Text
from collections import deque

REPO_ROOT = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

# Handle directory with hyphen
sys.path.insert(0, str(REPO_ROOT / "experiments" / "feedback-loop"))

import loop_engine
from loop_engine import run_feedback_loop  # type: ignore
from meta_controller import build_telemetry_for_valid_full, get_6A_telemetry, get_6C_telemetry  # type: ignore

UI_QUEUE = queue.Queue()
loop_engine.set_ui_queue(UI_QUEUE)


def generate_run_summary():
    """Generate post-run summary to logs/stage3/run_summaries/."""
    output_dir = os.path.join(REPO_ROOT, "results", "feedback_loop")
    final_domains_csv = os.path.join(output_dir, "stage3_final_domains.csv")
    if not os.path.exists(final_domains_csv):
        return
    df = pd.read_csv(final_domains_csv)
    
    total_triples = len(df)
    improved = len(df[df['Improvement_vs_Seed'] > 0]) if 'Improvement_vs_Seed' in df.columns else 0
    
    summary_txt = "==================================================\n"
    summary_txt += "           STAGE 3 EXECUTION SUMMARY              \n"
    summary_txt += "==================================================\n\n"
    summary_txt += f"Total Triples Processed: {total_triples}\n"
    summary_txt += f"Total Triples Improved (vs Seed): {improved} ({(improved/total_triples*100) if total_triples > 0 else 0:.1f}%)\n\n"
    
    summary_txt += "BREAKDOWN BY LLM:\n"
    summary_txt += "-----------------\n"
    for llm in df['LLM'].unique():
        llm_df = df[df['LLM'] == llm]
        llm_imp = len(llm_df[llm_df['Improvement_vs_Seed'] > 0]) if 'Improvement_vs_Seed' in llm_df.columns else 0
        summary_txt += f"- {llm}: {llm_imp}/{len(llm_df)} Improved\n"
    
    summary_txt += "\nBREAKDOWN BY PLANNER:\n"
    summary_txt += "---------------------\n"
    for planner in df['Target_Planner'].unique():
        pl_df = df[df['Target_Planner'] == planner]
        pl_imp = len(pl_df[pl_df['Improvement_vs_Seed'] > 0]) if 'Improvement_vs_Seed' in pl_df.columns else 0
        summary_txt += f"- {planner}: {pl_imp}/{len(pl_df)} Improved\n"
        
    summary_txt += "\nBREAKDOWN BY DOMAIN:\n"
    summary_txt += "--------------------\n"
    for dom in df['Domain'].unique():
        dom_df = df[df['Domain'] == dom]
        dom_imp = len(dom_df[dom_df['Improvement_vs_Seed'] > 0]) if 'Improvement_vs_Seed' in dom_df.columns else 0
        summary_txt += f"- {dom}: {dom_imp}/{len(dom_df)} Improved\n"
    
    # Save to logs/stage3/run_summaries/ (not results/feedback_loop/)
    summary_dir = os.path.join(REPO_ROOT, "logs", "stage3", "run_summaries")
    os.makedirs(summary_dir, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_path = os.path.join(summary_dir, f"run_summary_{ts}.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary_txt)
    print(f"\n[SUMMARY] Saved completed run summary to {summary_path}")


shutdown_flag = threading.Event()

DOMAINS = ["barman", "depots", "ricochet-robots", "snake", "visitall"]
PLANNERS = ["lama", "decstar", "bfws", "madagascar"]
LLMS = ["claude-opus-4.6", "deepseek-r1", "gemini-3.1-pro", "gpt-5.4"]

def get_test_instances(domain):
    indices = [1, 2, 3, 4, 7, 8, 9, 11, 12, 13, 14, 16, 17, 18, 19]
    domain_benchmark_dir = os.path.join(REPO_ROOT, "benchmarks", domain)
    if not os.path.exists(domain_benchmark_dir):
        domain_benchmark_dir = os.path.join(REPO_ROOT, "benchmark_samples", domain)
        
    # Prioritize specific problem directories to avoid recursively picking up domain files or duplicate folders
    if os.path.exists(os.path.join(domain_benchmark_dir, "instances")):
        all_files = glob.glob(os.path.join(domain_benchmark_dir, "instances", "*.pddl"))
    elif os.path.exists(os.path.join(domain_benchmark_dir, "all_instances")):
        all_files = glob.glob(os.path.join(domain_benchmark_dir, "all_instances", "*.pddl"))
    else:
        all_files = glob.glob(os.path.join(domain_benchmark_dir, "**", "*.pddl"), recursive=True)
        
    test_instances = []
    seen_basenames = set()
    for f in all_files:
        name = os.path.basename(f)
        if not name.startswith("instance-"): continue
        if name in seen_basenames: continue
        
        num_str = ''.join(filter(str.isdigit, name))
        if num_str and int(num_str) in indices:
            test_instances.append(f)
            seen_basenames.add(name)
            
    return sorted(test_instances)

def resolve_seed_domain(domain, planner, llm):
    # This enforces Point 6: Iteration 1 Routing.
    stage0_path = os.path.join(REPO_ROOT, "benchmarks", domain, "domain.pddl")
    if not os.path.exists(stage0_path):
        stage0_path = os.path.join(REPO_ROOT, "benchmark_samples", domain, "domain.pddl")
    
    with open(stage0_path, 'r', encoding='utf-8') as f:
        baseline_pddl = f.read()

    # Look up in LLM Gen Data
    gen_csv = os.path.join(REPO_ROOT, "results", "arch_aware", "LLM Results", "arch_aware_llm_generation_data.csv")
    
    # Defaults
    is_valid_seed = False
    seed_domain_path = stage0_path
    init_hist = []
    init_tel = ""
    stage2_ipc = 0.0 # Will be 0.0 unless valid
    
    if os.path.exists(gen_csv):
        df = pd.read_csv(gen_csv)
        PROMPT_ID_MAP = {"lama":1, "decstar":2, "bfws":3, "madagascar":4}
        pid = PROMPT_ID_MAP.get(planner, 1)
        
        # Match llm via contains (since string names vary: gpt-5.4 vs gpt-5.4-2026-03-05)
        llm_search = llm
        if 'gpt' in llm.lower() and '5.4' in llm:
            llm_search = 'gpt-5.4'
        elif 'deepseek' in llm.lower():
            llm_search = 'deepseek-reasoner'
            
        match = df[(df['Domain Name'] == domain) & (df['Prompt ID'] == pid) & (df['LLM Model'].str.contains(llm_search))]
        
        if match.empty:
            # 6A: Not in CSV -> likely API failure
            init_hist = ["PREVIOUS ATTEMPT HISTORY:\n\nStage 2 Attempt:\n  • Status: FAILED — Unknown API Error.\n  • No valid PDDL domain was produced."]
            init_tel = get_6A_telemetry("Unknown API Error", baseline_pddl)
        else:
            row = match.iloc[0]
            val_status = str(row['Validation Status'])
            llm_status = str(row['LLM_Status'])
            v4_pass = str(row['Passed V4'])
            
            if 'token_limit' in llm_status.lower() or 'tokenlimit' in llm_status.lower() or val_status == 'TokenLimitExceeded':
                # 6A-i TokenLimit
                init_hist = ["PREVIOUS ATTEMPT HISTORY:\n\nStage 2 Attempt:\n  • Status: FAILED — Your response exceeded the maximum token output\n    limit (4,096 tokens) and was truncated before completion.\n  • No valid PDDL domain was produced."]
                init_tel = get_6A_telemetry("TokenLimitExceeded", baseline_pddl)
            elif 'ratelimit' in llm_status.lower():
                init_hist = ["PREVIOUS ATTEMPT HISTORY:\n\nStage 2 Attempt:\n  • Status: FAILED — The API rate limit was exceeded.\n  • No valid PDDL domain was produced."]
                init_tel = get_6A_telemetry("RateLimit", baseline_pddl)
            elif 'filter' in llm_status.lower() or 'safety' in llm_status.lower():
                init_hist = ["PREVIOUS ATTEMPT HISTORY:\n\nStage 2 Attempt:\n  • Status: FAILED — The response was blocked by the provider's\n    content safety filter.\n  • No valid PDDL domain was produced."]
                init_tel = get_6A_telemetry("Filter", baseline_pddl)
            elif 'server' in llm_status.lower() or 'timeout' in llm_status.lower():
                init_hist = [f"PREVIOUS ATTEMPT HISTORY:\n\nStage 2 Attempt:\n  • Status: FAILED — The API call failed due to a server/network error.\n    Error: \"{llm_status}\"\n  • No valid PDDL domain was produced."]
                init_tel = get_6A_telemetry("Server", baseline_pddl)
            elif val_status == 'VALID' and row['Passed Stage V1'] == True and v4_pass == "True":
                # 6B: Valid Domain
                is_valid_seed = True
                
                # Bug fix #1: Cross-platform domain path resolution.
                # CSV paths may use macOS paths that don't exist on Windows.
                # Try multiple resolution strategies:
                extracted_path = str(row['Path to Extracted PDDL'])
                resolved = False
                
                # Strategy 1: Direct path (works if same machine)
                if os.path.exists(extracted_path):
                    seed_domain_path = extracted_path
                    resolved = True
                
                # Strategy 2: Extract relative path and resolve against REPO_ROOT
                if not resolved:
                    for marker in ["results/arch_aware/", "results\\arch_aware\\"]:
                        if marker in extracted_path.replace("\\", "/") or marker.replace("/", "\\") in extracted_path:
                            # Extract relative portion
                            norm = extracted_path.replace("\\", "/")
                            idx = norm.find("results/arch_aware/")
                            if idx >= 0:
                                rel = norm[idx:]
                                candidate = os.path.join(REPO_ROOT, rel)
                                if os.path.exists(candidate):
                                    seed_domain_path = candidate
                                    resolved = True
                                    break
                
                # Strategy 3: Known directory structure lookup
                # Validated Domains: results/arch_aware/Validated Domains/{domain}/{planner}/{domain}_{llm_short}_Arch_Aware_{planner}.pddl
                if not resolved:
                    llm_short_map = {
                        "gpt-5.4": "gpt-5.4",
                        "claude-opus-4.6": "claude-opus-4.6",
                        "gemini-3.1-pro": "gemini-3.1-pro",
                        "deepseek-r1": "deepseek-r1",
                    }
                    llm_short = llm
                    for k, v in llm_short_map.items():
                        if k in llm or llm in k:
                            llm_short = v
                            break
                    
                    # Try Validated Domains first (only contains V1-V4 passed files)
                    validated_path = os.path.join(REPO_ROOT, "results", "arch_aware", "Validated Domains",
                                                  domain, planner, f"{domain}_{llm_short}_Arch_Aware_{planner}.pddl")
                    if os.path.exists(validated_path):
                        seed_domain_path = validated_path
                        resolved = True
                    else:
                        # Try "ArchAware" variant naming
                        validated_path2 = os.path.join(REPO_ROOT, "results", "arch_aware", "Validated Domains",
                                                       domain, planner, f"{domain}_{llm_short}_ArchAware_{planner}.pddl")
                        if os.path.exists(validated_path2):
                            seed_domain_path = validated_path2
                            resolved = True
                    
                    # Try Extracted PDDL as fallback (has more files but includes invalid ones)
                    if not resolved:
                        extracted_dir = os.path.join(REPO_ROOT, "results", "arch_aware", "Extracted PDDL",
                                                     domain, f"{domain}_{llm_short}_Arch_Aware_{planner}.pddl")
                        if os.path.exists(extracted_dir):
                            seed_domain_path = extracted_dir
                            resolved = True
                
                if not resolved:
                    # Last resort: use baseline
                    seed_domain_path = stage0_path
                
                imp_csv = os.path.join(REPO_ROOT, "results", "arch_aware", "improvement", "improvement_results.csv")
                
                try:
                    id_df = pd.read_csv(imp_csv)
                    llm_map = {
                        "gpt-5.4-2026-03-05": "gpt-5.4",
                        "claude-opus-4.6": "claude-opus-4-6",
                        "gemini-3.1-pro": "gemini-3.1-pro",
                        "deepseek-r1": "deepseek-reasoner"
                    }
                    llm_search_id = llm
                    for k, v in llm_map.items():
                        if k in llm or llm in k:
                            llm_search_id = v
                            break
                    m2 = id_df[(id_df['Domain'] == domain) & (id_df['Target_Planner'] == planner) & (id_df['LLM'].str.contains(llm_search_id, regex=False, na=False))]
                    if not m2.empty:
                        imp_detected = m2.iloc[0]['IMPROVEMENT_DETECTED'] == True
                        if imp_detected:
                            init_hist = ["PREVIOUS ATTEMPT HISTORY:\n\nStage 2 Attempt:\n  • Status: VALID — Your reordered domain passed all validation checks.\n  • Result: IMPROVEMENT DETECTED (passed all 3 conditions: statistical\n    significance, practical significance, coverage preservation).\n  • No rationale was recorded for this attempt."]
                        else:
                            fails = []
                            if not m2.iloc[0]['Condition_A_StatSig']: fails.append("Statistical_Significance")
                            if not m2.iloc[0]['Condition_B_PractSig']: fails.append("Practical_Significance")
                            if not m2.iloc[0]['Condition_C_Coverage']: fails.append("Coverage_Preserved")
                            f_str = ", ".join(fails)
                            init_hist = [f"PREVIOUS ATTEMPT HISTORY:\n\nStage 2 Attempt:\n  • Status: VALID — Your reordered domain passed all validation checks.\n  • Result: NO IMPROVEMENT detected. Failed conditions: {f_str}\n  • No rationale was recorded for this attempt."]
                    else:
                        init_hist = ["PREVIOUS ATTEMPT HISTORY:\n\nStage 2 Attempt:\n  • Status: VALID — Your reordered domain passed all validation checks.\n  • No rationale was recorded for this attempt."]
                except Exception:
                    init_hist = ["PREVIOUS ATTEMPT HISTORY:\n\nStage 2 Attempt:\n  • Status: VALID — Your reordered domain passed all validation checks.\n  • No rationale was recorded for this attempt."]
                
                # Best score gets set to Stage 2 IPC (approx logic: we lookup real later)
                stage2_ipc = 1.0 # placeholder for valid IPC, will be overwritten by point 5
                
                # NOTE: For valid domains, we must DELAY telemetry generation until run_feedback_loop
                # because we need the Stage 2 and Baseline statistics blocks from soft critics to build it.
                # We signal this by passing a placeholder list.
                init_tel = "DELAY_VALID_TELEMETRY"
            else:
                # 6C: Invalid Domain
                error_str = str(row['VAL_error_string']) if pd.notna(row['VAL_error_string']) else "Unknown semantic violation"
                failed_str = "V4" if v4_pass == "False" else "V2"
                if "V1" in val_status: failed_str = "V1"
                if "V3" in val_status: failed_str = "V3"
                
                det = ""
                if failed_str == "V4": det = f"  • Detail: Your reordering CHANGED the logical semantics of the\n    domain. The following differences were detected:\n    {error_str}"
                elif failed_str == "V2": det = f"  • Detail: The VAL validator reported the following syntax errors:\n    \"{error_str}\""
                elif failed_str == "V3": det = f"  • Detail: Your output was identical to the input domain. No\n    reordering was performed."
                elif failed_str == "V1": det = f"  • Detail: No valid PDDL block starting with \"(define\" was found in\n    your response. Your output contained conversational text or\n    malformed code that could not be parsed as PDDL."
                
                init_hist = [f"PREVIOUS ATTEMPT HISTORY:\n\nStage 2 Attempt:\n  • Status: FAILED — {failed_str} Check\n{det}"]
                init_tel = get_6C_telemetry(failed_str, error_str, baseline_pddl)
                
    return seed_domain_path, stage0_path, init_hist, init_tel, stage2_ipc, is_valid_seed

def run_pipeline_for_llm(llm):
    UI_QUEUE.put(("LOG", llm, "INFO", f"=== Starting Pipeline for LLM: {llm} ===", None))
    output_dir = os.path.join(REPO_ROOT, "results", "feedback_loop")
    os.makedirs(output_dir, exist_ok=True)
    
    # Checkpointing: Load completed triples
    completed_triples = set()
    final_domains_csv = os.path.join(output_dir, "stage3_final_domains.csv")
    if os.path.exists(final_domains_csv):
        try:
            df = pd.read_csv(final_domains_csv)
            # Reverse-map canonical LLM names back to the friendly names used in LLMS
            CANONICAL_TO_FRIENDLY = {
                "gpt-5.4-2026-03-05": "gpt-5.4",
                "claude-opus-4-6": "claude-opus-4.6",
                "gemini-3.1-pro-preview-customtools": "gemini-3.1-pro",
                "deepseek-reasoner": "deepseek-r1",
            }
            for _, row in df.iterrows():
                dom = row['Domain']
                plnr = row['Target_Planner']
                canonical_llm = str(row['LLM'])
                friendly_llm = CANONICAL_TO_FRIENDLY.get(canonical_llm, canonical_llm)
                completed_triples.add(f"{dom}_{plnr}_{friendly_llm}")
        except Exception as e:
            pass
    
    # Per-LLM triple counter for pipeline progress bar
    triple_counter = 0
    
    for domain in DOMAINS:
        test_instances = get_test_instances(domain)
        if not test_instances: continue
            
        for planner in PLANNERS:
            if shutdown_flag.is_set():
                UI_QUEUE.put(("LOG", llm, "INFO", "[Shutdown] Stopping thread...", None))
                return
            
            triple_id = f"{domain}_{planner}_{llm}"
            if triple_id in completed_triples:
                triple_counter += 1
                UI_QUEUE.put(("PIPELINE_UPDATE", llm, triple_counter, 20, f"⏭ {domain}+{planner} (skipped)"))
                UI_QUEUE.put(("LOG", llm, "INFO", f"[{triple_id}] Skipping - already completed (checkpoint).", None))
                continue
                
            try:
                seed_domain_path, stage0_baseline_path, init_hist, init_tel, stage2_ipc, is_valid_seed = resolve_seed_domain(domain, planner, llm)
                
                run_feedback_loop(
                    domain_name=domain,
                    planner_name=planner,
                    llm_model=llm,
                    base_domain_path=seed_domain_path,
                    test_instances=test_instances,
                    output_dir=output_dir,
                    stage0_baseline_path=stage0_baseline_path,
                    initial_history_buffer=init_hist,
                    initial_telemetry_feedback=init_tel,
                    stage2_best_score=stage2_ipc,
                    is_valid_seed=is_valid_seed,
                    max_iter=3
                )
            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                UI_QUEUE.put(("LOG", llm, "LLM_ERROR", f"Error processing {domain} | {planner} | {llm}: {e}", None))
            
            # Update pipeline bar after each triple (whether success or exception)
            triple_counter += 1
            UI_QUEUE.put(("PIPELINE_UPDATE", llm, triple_counter, 20, f"✓ {domain}+{planner} done"))
            
            # Update overall progress from final_domains CSV
            final_domains_csv = os.path.join(output_dir, "stage3_final_domains.csv")
            comp_count = 0
            if os.path.exists(final_domains_csv):
                try:
                    comp_count = len(pd.read_csv(final_domains_csv))
                except:
                    pass
            UI_QUEUE.put(("OVERALL_PROGRESS", comp_count, 80))

def run_pipelines_orchestrator():
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(run_pipeline_for_llm, llm): llm for llm in LLMS}
            for future in concurrent.futures.as_completed(futures):
                llm = futures[future]
                try:
                    future.result()
                    UI_QUEUE.put(("LOG", llm, "INFO", f"Pipeline finished successfully.", None))
                except Exception as e:
                    UI_QUEUE.put(("FATAL_ERROR", f"Pipeline {llm} crashed: {e}"))
        UI_QUEUE.put(("DONE", None))
    except Exception as e:
        UI_QUEUE.put(("FATAL_ERROR", f"Orchestrator failed: {e}"))

def main():
    log_dir = os.path.join(REPO_ROOT, "logs", "stage3", "terminal_output")
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"run_{timestamp}.log")
    
    heartbeat_path = os.path.join(REPO_ROOT, "logs", "stage3", "pipeline_heartbeat.log")
    os.makedirs(os.path.dirname(heartbeat_path), exist_ok=True)
    
    console = Console()
    
    from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
    from rich.console import Group
    from rich.live import Live
    from rich.layout import Layout
    from rich.panel import Panel
    
    overall_progress = Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total} Triples)"),
        TimeElapsedColumn()
    )
    overall_task = overall_progress.add_task("[bold cyan]OVERALL PROGRESS:", total=80)
    
    pipeline_progress = Progress(
        TextColumn("[bold]{task.description:<20}"),
        BarColumn(),
        TextColumn("{task.completed:>2}/{task.total} | {task.fields[status]}"),
    )
    
    pipeline_tasks = {}
    for llm in LLMS:
        pipeline_tasks[llm] = pipeline_progress.add_task(f"Pipeline: {llm[:10]}", total=20, status="Starting...")

    # Load initial completed count
    output_dir = os.path.join(REPO_ROOT, "results", "feedback_loop")
    final_domains_csv = os.path.join(output_dir, "stage3_final_domains.csv")
    if os.path.exists(final_domains_csv):
        try:
            df = pd.read_csv(final_domains_csv)
            comp_count = len(df)
            overall_progress.update(overall_task, completed=comp_count)
        except Exception:
            pass

    header_text = Text(
        "================================================================================\n"
        "  [PHASE 3] ARCH-AWARE FEEDBACK LOOP EXECUTOR \n"
        "  [Engine: Antigravity | Container Runtime: Docker]\n"
        "================================================================================",
        style="bold bright_blue", justify="center"
    )
    
    # Define Layout
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=5),
        Layout(name="progress", size=9),
        Layout(name="logs")
    )
    
    layout["header"].update(header_text)
    layout["progress"].update(
        Group(
            Panel(overall_progress, border_style="cyan"),
            Panel(pipeline_progress, title="[ ⚡ PARALLEL PIPELINE STATUS ]", border_style="cyan")
        )
    )
    
    # Split the logs area horizontally into 4 columns
    llm_layouts = [Layout(name=f"log_{llm}") for llm in LLMS]
    layout["logs"].split_row(*llm_layouts)
    
    llm_logs = {llm: deque(maxlen=25) for llm in LLMS}
    
    for llm in LLMS:
        layout[f"log_{llm}"].update(Panel(Text(""), title=f"[ {llm} ]", border_style="green"))

    # Start background thread
    threading.Thread(target=run_pipelines_orchestrator, daemon=True).start()

    last_heartbeat = 0
    
    # Stream Isolation: Open 5 separate log files
    master_log_path = os.path.join(log_dir, "master_orchestrator.log")
    file_handles = {}
    file_handles["master"] = open(master_log_path, "a", encoding="utf-8")
    for llm in LLMS:
        llm_log_path = os.path.join(log_dir, f"{llm}_run.log")
        file_handles[llm] = open(llm_log_path, "a", encoding="utf-8")
        
    try:
        with Live(layout, console=console, refresh_per_second=4, screen=True):
            while True:
                now = time.time()
                if now - last_heartbeat > 60:
                    last_heartbeat = now
                    try:
                        with open(heartbeat_path, "a", encoding="utf-8") as hb:
                            hb.write(f"[{datetime.datetime.now().isoformat()}] Heartbeat: {overall_progress.tasks[overall_task].completed}/80 triples complete.\n")
                    except: pass

                try:
                    event = UI_QUEUE.get(timeout=0.25)
                    etype = event[0]
                    
                    if etype == "LOG":
                        _, llm, tag, msg, raw_msg = event
                        
                        # Determine color
                        color = "white"
                        if tag == "LLM_GEN": color = "cyan"
                        elif tag == "LLM_RECV": color = "blue"
                        elif tag == "VALIDATE": color = "magenta" if "Failure" in msg or "Error" in msg else "green"
                        elif tag == "RUN": color = "yellow"
                        elif tag == "SUCCESS": color = "green"
                        elif tag == "TIMEOUT": color = "red"
                        elif tag == "CRITIQUE": color = "yellow"
                        elif tag == "RESULT": color = "bold green" if "IMPROVEMENT" in msg else "bold yellow"
                        elif tag == "LLM_ERROR" or tag == "FATAL_ERROR": color = "bold red"
                        elif tag == "TERMINATE": color = "red"
                        
                        ts = datetime.datetime.now().strftime("%H:%M:%S")
                        tag_pad = f"[{tag}]"
                        
                        colored_msg = f"[{ts}] [{color}]{tag_pad:<12}[/] {msg}"
                        
                        # Append to that specific LLM's deque
                        if llm in llm_logs:
                            llm_logs[llm].append(colored_msg)
                            layout[f"log_{llm}"].update(Panel(Text.from_markup("\n".join(llm_logs[llm])), title=f"[ {llm} ]", border_style="green"))
                        
                        # Write raw unformatted log to isolated LLM file
                        llm_pad = f"{llm:<10}"[:10]
                        raw_str = raw_msg if raw_msg else f"[{ts}] [{llm_pad}] {tag_pad:<12} {msg}"
                        if llm in file_handles:
                            file_handles[llm].write(raw_str + "\n")
                            file_handles[llm].flush()
                        else:
                            file_handles["master"].write(raw_str + "\n")
                            file_handles["master"].flush()
                        
                    elif etype == "PIPELINE_UPDATE":
                        _, llm, current, total, text = event
                        if llm in pipeline_tasks:
                            if current >= 0:
                                pipeline_progress.update(pipeline_tasks[llm], completed=current, status=text)
                            else:
                                # Text-only update (per-iteration status)
                                pipeline_progress.update(pipeline_tasks[llm], status=text)
                            
                    elif etype == "TRIPLE_COMPLETE":
                        _, triple_id, total_iters, verdict, delta = event
                        icon = "✔" if verdict == "IMPROVEMENT" else "✖"
                        color = "green" if verdict == "IMPROVEMENT" else "red" if verdict == "ALL_TIMEOUT" else "yellow"
                        comp_msg = f"[{color}]{icon} ({triple_id}) | Iters: {total_iters} | Result: {verdict} ({delta:+.2f})[/]"
                        
                        # Find the corresponding LLM to append the completion message to
                        llm_match = None
                        for llm in LLMS:
                            if llm in triple_id:
                                llm_match = llm
                                break
                        if llm_match:
                            llm_logs[llm_match].append(comp_msg)
                            layout[f"log_{llm_match}"].update(Panel(Text.from_markup("\n".join(llm_logs[llm_match])), title=f"[ {llm_match} ]", border_style="green"))
                            
                        # Write to master orchestrator log
                        ts = datetime.datetime.now().strftime("%H:%M:%S")
                        file_handles["master"].write(f"[{ts}] TRIPLE_COMPLETE | {triple_id} | Result: {verdict} | Delta: {delta:+.2f}\n")
                        file_handles["master"].flush()
                        
                    elif etype == "OVERALL_PROGRESS":
                        _, current, total = event
                        overall_progress.update(overall_task, completed=current)
                        
                    elif etype == "FATAL_ERROR":
                        _, err_msg = event
                        # Broadcast fatal error to all panels
                        for llm in LLMS:
                            llm_logs[llm].append(f"[bold red]FATAL ERROR: {err_msg}[/]")
                            layout[f"log_{llm}"].update(Panel(Text.from_markup("\n".join(llm_logs[llm])), title=f"[ {llm} ]", border_style="red"))
                            
                        # Write to master orchestrator log
                        ts = datetime.datetime.now().strftime("%H:%M:%S")
                        file_handles["master"].write(f"[{ts}] FATAL_ERROR | {err_msg}\n")
                        file_handles["master"].flush()
                        break
                        
                    elif etype == "DONE":
                        # Broadcast success
                        for llm in LLMS:
                            llm_logs[llm].append("[bold bright_green]All pipelines completed successfully![/]")
                            layout[f"log_{llm}"].update(Panel(Text.from_markup("\n".join(llm_logs[llm])), title=f"[ {llm} ]", border_style="green"))
                            
                        # Write to master orchestrator log
                        ts = datetime.datetime.now().strftime("%H:%M:%S")
                        file_handles["master"].write(f"[{ts}] DONE | All pipelines completed successfully.\n")
                        file_handles["master"].flush()
                        break
                        
                except queue.Empty:
                    pass
    finally:
        for f in file_handles.values():
            f.close()
                    
    print("\nOrchestrator Shutdown Complete.")

    # Generate final summary
    print("\nAll threads finished. Generating combined run summary...")
    try:
        generate_run_summary()
    except Exception as e:
        print(f"Failed to generate run summary: {e}")

if __name__ == "__main__":
    main()
