
def generate_run_summary():
    output_dir = os.path.join(REPO_ROOT, "results", "feedback_loop")
    final_domains_csv = os.path.join(output_dir, "stage3_final_domains.csv")
    if not os.path.exists(final_domains_csv):
        return
    import pandas as pd
    df = pd.read_csv(final_domains_csv)
    
    total_triples = len(df)
    improved = len(df[df['Validation_Status'] == 'VALID'])
    
    summary_txt = "==================================================\n"
    summary_txt += "           STAGE 3 EXECUTION SUMMARY              \n"
    summary_txt += "==================================================\n\n"
    summary_txt += f"Total Triples Processed: {total_triples}\n"
    summary_txt += f"Total Triples Improved (VALID): {improved} ({(improved/total_triples*100) if total_triples > 0 else 0:.1f}%)\n\n"
    
    summary_txt += "BREAKDOWN BY LLM:\n"
    summary_txt += "-----------------\n"
    for llm in df['LLM'].unique():
        llm_df = df[df['LLM'] == llm]
        llm_imp = len(llm_df[llm_df['Validation_Status'] == 'VALID'])
        summary_txt += f"- {llm}: {llm_imp}/{len(llm_df)} Improved\n"
    
    summary_txt += "\nBREAKDOWN BY PLANNER:\n"
    summary_txt += "---------------------\n"
    for planner in df['Target_Planner'].unique():
        pl_df = df[df['Target_Planner'] == planner]
        pl_imp = len(pl_df[pl_df['Validation_Status'] == 'VALID'])
        summary_txt += f"- {planner}: {pl_imp}/{len(pl_df)} Improved\n"
        
    summary_txt += "\nBREAKDOWN BY DOMAIN:\n"
    summary_txt += "--------------------\n"
    for dom in df['Domain'].unique():
        dom_df = df[df['Domain'] == dom]
        dom_imp = len(dom_df[dom_df['Validation_Status'] == 'VALID'])
        summary_txt += f"- {dom}: {dom_imp}/{len(dom_df)} Improved\n"
    
    summary_path = os.path.join(output_dir, "run_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary_txt)
    print(f"\n[SUMMARY] Saved completed run summary to {summary_path}")

import os
import sys
import glob
import concurrent.futures
import pandas as pd
from pathlib import Path
import datetime
import threading
import queue
from collections import deque

from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
from rich.console import Group, Console
from rich.text import Text

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

DOMAINS = ["barman", "depots", "ricochet-robots", "snake", "visitall"]
PLANNERS = ["lama", "decstar", "bfws", "madagascar"]
LLMS = ["claude-opus-4.6", "deepseek-r1", "gemini-3.1-pro", "gpt-5.4"]

def get_test_instances(domain):
    indices = [1, 2, 3, 4, 7, 8, 9, 11, 12, 13, 14, 16, 17, 18, 19]
    domain_benchmark_dir = os.path.join(REPO_ROOT, "benchmarks", domain)
    if not os.path.exists(domain_benchmark_dir):
        domain_benchmark_dir = os.path.join(REPO_ROOT, "benchmark_samples", domain)
    all_files = glob.glob(os.path.join(domain_benchmark_dir, "**", "*.pddl"), recursive=True)
    test_instances = []
    for f in all_files:
        name = os.path.basename(f)
        if name == "domain.pddl": continue
        num_str = ''.join(filter(str.isdigit, name))
        if num_str and int(num_str) in indices:
            test_instances.append(f)
    return sorted(list(set(test_instances)))

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
                init_hist = ["PREVIOUS ATTEMPTS HISTORY:\n\nStage 2 Attempt:\n  • Status: FAILED — Your response exceeded the maximum token output\n    limit (4,096 tokens) and was truncated before completion.\n  • No valid PDDL domain was produced."]
                init_tel = get_6A_telemetry("TokenLimitExceeded", baseline_pddl)
            elif 'ratelimit' in llm_status.lower():
                init_hist = ["PREVIOUS ATTEMPTS HISTORY:\n\nStage 2 Attempt:\n  • Status: FAILED — The API rate limit was exceeded.\n  • No valid PDDL domain was produced."]
                init_tel = get_6A_telemetry("RateLimit", baseline_pddl)
            elif 'filter' in llm_status.lower() or 'safety' in llm_status.lower():
                init_hist = ["PREVIOUS ATTEMPTS HISTORY:\n\nStage 2 Attempt:\n  • Status: FAILED — The response was blocked by the provider's\n    content safety filter.\n  • No valid PDDL domain was produced."]
                init_tel = get_6A_telemetry("Filter", baseline_pddl)
            elif 'server' in llm_status.lower() or 'timeout' in llm_status.lower():
                init_hist = [f"PREVIOUS ATTEMPTS HISTORY:\n\nStage 2 Attempt:\n  • Status: FAILED — The API call failed due to a server/network error.\n    Error: \"{llm_status}\"\n  • No valid PDDL domain was produced."]
                init_tel = get_6A_telemetry("Server", baseline_pddl)
            elif val_status == 'VALID' and row['Passed Stage V1'] == True and v4_pass == "True":
                # 6B: Valid Domain
                is_valid_seed = True
                extracted_path = str(row['Path to Extracted PDDL'])
                if os.path.exists(extracted_path):
                    seed_domain_path = extracted_path
                else:
                    seed_domain_path = stage0_path # fallback just in case
                
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
                            init_hist = ["PREVIOUS ATTEMPTS HISTORY:\n\nStage 2 Attempt:\n  • Status: VALID — Your reordered domain passed all validation checks.\n  • Result: IMPROVEMENT DETECTED (passed all 3 conditions: statistical\n    significance, practical significance, coverage preservation).\n  • No rationale was recorded for this attempt."]
                        else:
                            fails = []
                            if not m2.iloc[0]['Statistical_Significance']: fails.append("Statistical_Significance")
                            if not m2.iloc[0]['Practical_Significance']: fails.append("Practical_Significance")
                            if not m2.iloc[0]['Coverage_Preserved']: fails.append("Coverage_Preserved")
                            f_str = ", ".join(fails)
                            init_hist = [f"PREVIOUS ATTEMPTS HISTORY:\n\nStage 2 Attempt:\n  • Status: VALID — Your reordered domain passed all validation checks.\n  • Result: NO IMPROVEMENT detected. Failed conditions: {f_str}\n  • No rationale was recorded for this attempt."]
                    else:
                        init_hist = ["PREVIOUS ATTEMPTS HISTORY:\n\nStage 2 Attempt:\n  • Status: VALID — Your reordered domain passed all validation checks.\n  • No rationale was recorded for this attempt."]
                except Exception:
                    init_hist = ["PREVIOUS ATTEMPTS HISTORY:\n\nStage 2 Attempt:\n  • Status: VALID — Your reordered domain passed all validation checks.\n  • No rationale was recorded for this attempt."]
                
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
                
                init_hist = [f"PREVIOUS ATTEMPTS HISTORY:\n\nStage 2 Attempt:\n  • Status: FAILED — {failed_str} Check\n{det}"]
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
            completed_triples = set(df['Triple_ID'].unique())
        except Exception as e:
            pass
    
    for domain in DOMAINS:
        test_instances = get_test_instances(domain)
        if not test_instances: continue
            
        for planner in PLANNERS:
            if shutdown_flag.is_set():
                UI_QUEUE.put(("LOG", llm, "INFO", "[Shutdown] Stopping thread...", None))
                return
            triple_id = f"{domain}_{planner}_{llm}"
            if triple_id in completed_triples:
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
                
                # Update heartbeat count
                final_domains_csv = os.path.join(output_dir, "stage3_final_domains.csv")
                comp_count = 0
                if os.path.exists(final_domains_csv):
                    import pandas as pd
                    try:
                        comp_count = len(pd.read_csv(final_domains_csv))
                    except:
                        pass
                UI_QUEUE.put(("OVERALL_PROGRESS", comp_count, 80))
            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                UI_QUEUE.put(("LOG", llm, "LLM_ERROR", f"Error processing {domain} | {planner} | {llm}: {e}", None))

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

def build_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=5),
        Layout(name="pipelines", size=6),
        Layout(name="log", size=17),
        Layout(name="completed", size=6)
    )
    return layout

def main():
    log_dir = os.path.join(REPO_ROOT, "logs", "stage3", "terminal_output")
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"run_{timestamp}.log")
    
    # Initialize UI state
    log_messages = deque(maxlen=15)
    completed_messages = deque(maxlen=4)
    
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

    layout = build_layout()
    header_text = Text(
        "================================================================================\n"
        "  [PHASE 3] ARCH-AWARE FEEDBACK LOOP EXECUTOR \n"
        "  [Engine: Antigravity | Container Runtime: Docker]\n"
        "================================================================================",
        style="bold bright_blue", justify="center"
    )
    layout["header"].update(Group(header_text, overall_progress))
    layout["pipelines"].update(Panel(pipeline_progress, title="[ ⚡ PARALLEL PIPELINE STATUS ]", border_style="cyan"))
    layout["log"].update(Panel(Text("Waiting for logs..."), title="[ 📜 LIVE EXECUTION LOG ]", border_style="green"))
    layout["completed"].update(Panel(Text(""), title="[ 🏆 LATEST COMPLETED TRIPLES ]", border_style="yellow"))

    # Start background thread
    threading.Thread(target=run_pipelines_orchestrator, daemon=True).start()

    with open(log_file, "a", encoding="utf-8") as f_log:
        with Live(layout, refresh_per_second=4, screen=False):
            while True:
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
                        
                        ts = datetime.datetime.now().strftime("%H:%M:%S")
                        llm_pad = f"{llm:<10}"[:10]
                        tag_pad = f"[{tag}]"
                        
                        colored_msg = f"[{ts}] [{color}]{llm_pad}[/] [{color}]{tag_pad:<12}[/] {msg}"
                        log_messages.append(colored_msg)
                        layout["log"].update(Panel(Text.from_markup("\n".join(log_messages)), title="[ 📜 LIVE EXECUTION LOG ]", border_style="green"))
                        
                        # Write raw unformatted log
                        raw_str = raw_msg if raw_msg else f"[{ts}] [{llm_pad}] {tag_pad:<12} {msg}"
                        f_log.write(raw_str + "\n")
                        f_log.flush()
                        
                    elif etype == "PIPELINE_UPDATE":
                        _, llm, current, total, text = event
                        if llm in pipeline_tasks:
                            pipeline_progress.update(pipeline_tasks[llm], completed=current, status=text)
                            
                    elif etype == "TRIPLE_COMPLETE":
                        _, triple_id, total_iters, verdict, delta = event
                        icon = "✔" if verdict == "IMPROVEMENT" else "✖"
                        color = "green" if verdict == "IMPROVEMENT" else "red" if verdict == "ALL_TIMEOUT" else "yellow"
                        comp_msg = f"[{color}]{icon} ({triple_id}) | Total Iters: {total_iters} | Final Result: {verdict} (Best Delta: {delta:+.2f})[/]"
                        completed_messages.append(comp_msg)
                        layout["completed"].update(Panel(Text.from_markup("\n".join(completed_messages)), title="[ 🏆 LATEST COMPLETED TRIPLES ]", border_style="yellow"))
                        
                    elif etype == "OVERALL_PROGRESS":
                        _, current, total = event
                        overall_progress.update(overall_task, completed=current)
                        
                    elif etype == "FATAL_ERROR":
                        _, err_msg = event
                        log_messages.append(f"[bold red]FATAL ERROR: {err_msg}[/]")
                        layout["log"].update(Panel(Text.from_markup("\n".join(log_messages)), title="[ 📜 LIVE EXECUTION LOG ]", border_style="red"))
                        f_log.write(f"FATAL ERROR: {err_msg}\n")
                        break
                        
                    elif etype == "DONE":
                        log_messages.append("[bold bright_green]All pipelines completed successfully![/]")
                        layout["log"].update(Panel(Text.from_markup("\n".join(log_messages)), title="[ 📜 LIVE EXECUTION LOG ]", border_style="green"))
                        f_log.write("All pipelines completed successfully.\n")
                        break
                        
                except queue.Empty:
                    pass
                    
    print("\nOrchestrator Shutdown Complete.")

    # Generate final summary
    print("\nAll threads finished. Generating combined run summary...")
    try:
        generate_run_summary()
    except Exception as e:
        print(f"Failed to generate run summary: {e}")

if __name__ == "__main__":
    main()
