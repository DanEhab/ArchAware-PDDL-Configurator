import sys
import time
import yaml
import threading
import concurrent.futures
import traceback
import os
from pathlib import Path
from datetime import datetime

# Add the general-prompt/llms path to sys.path so we can import llm_providers
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(PROJECT_ROOT / "experiments" / "general-prompt" / "llms"))
sys.path.append(str(PROJECT_ROOT / "experiments" / "arch-aware" / "utils"))

from llm_providers import (
    get_provider, AuthError, RateLimitError, ServerError, 
    NetworkTimeoutError, EmptyResponseError, TokenLimitError, LLMProviderError
)
from error_logging_stage2 import initialize_error_logging, log_error
from telemetry_tracker_stage2 import initialize_telemetry, log_llm_generation, generate_run_summary

CONFIG_PATH = PROJECT_ROOT / "config" / "experiment_config.yaml"
BENCHMARKS_DIR = PROJECT_ROOT / "benchmarks"
RESULTS_DIR = PROJECT_ROOT / "results" / "arch_aware" / "LLM Results"
PROMPTS_DIR = PROJECT_ROOT / "experiments" / "arch-aware" / "prompts"

PROMPT_ID_MAP = {
    "lama": 1,
    "decstar": 2,
    "bfws": 3,
    "madagascar": 4
}
# Define prompt file loading mapping based on actual files
PROMPT_FILES = {
    "lama": "1. Lama Architecture-Aware Prompt.txt",
    "decstar": "2. DecStar Architecture-Aware Prompt.txt",
    "bfws": "3. BFWS Architecture-Aware Prompt.txt",
    "madagascar": "4. Madagascar Architecture-Aware Prompt.txt"
}

# Global Stats Tracking
stats_lock = threading.Lock()
llm_stats = {}
pipeline_active = True
completed_runs = 0
total_runs = 0

class TeeLogger:
    def __init__(self, log_path: Path):
        log_path.parent.mkdir(parents=True, exist_ok=True)
        self.terminal = sys.stdout
        self.log = open(log_path, "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()

    def flush(self):
        self.terminal.flush()
        self.log.flush()

def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_prompt(planner: str, domain_str: str) -> str:
    prompt_file = PROMPTS_DIR / PROMPT_FILES[planner]
    if not prompt_file.exists():
        raise FileNotFoundError(f"Missing prompt template for planner {planner} at {prompt_file}")
    template = prompt_file.read_text(encoding="utf-8")
    return template.replace("{domain_str}", domain_str)

def heartbeat_loop(interval_seconds: int):
    log_file = PROJECT_ROOT / "logs" / "stage2" / "LLM_run" / "pipeline_heartbeat.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    while pipeline_active:
        with stats_lock:
            percent = (completed_runs / total_runs * 100) if total_runs > 0 else 0
            msg = f"[{datetime.utcnow().isoformat() + 'Z'}] Completion: {completed_runs}/{total_runs} ({percent:.1f}%)\n"
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(msg)
            
        for _ in range(interval_seconds):
            if not pipeline_active: break
            time.sleep(1)

def process_domain_for_llm(llm_config: dict, domain_name: str, planner: str, retry_policy: dict, llms_metadata: list):
    global completed_runs, pipeline_active
    
    llm_name = llm_config["name"]
    # Get standard "id" to use for folder structure (llm_short) if different from name, although usually name works
    llm_short = llm_name
    for l in llms_metadata:
        if l["name"] == llm_name:
            llm_short = l.get("id", llm_name)
            break
            
    prompt_id = PROMPT_ID_MAP[planner]

    domain_results_dir = RESULTS_DIR / domain_name
    raw_resp_path = domain_results_dir / f"{domain_name}_{llm_short}_Arch_Aware_{planner}.txt"

    # --- CHECKPOINT LOGIC: SKIP IF ALREADY EXISTS ---
    if raw_resp_path.exists():
        print(f"[{llm_name} | {domain_name} | {planner}] Output file already exists. Skipping (Checkpoint)...")
        with stats_lock:
            completed_runs += 1
        return
    # ------------------------------------------------

    with stats_lock:
        if llm_name not in llm_stats:
            llm_stats[llm_name] = {
                "attempts": 0, "success": 0, "rate_limit": 0, "server_error": 0,
                "auth_error": 0, "timeout": 0, "empty": 0, "input_tokens": 0, "output_tokens": 0
            }
        llm_stats[llm_name]["attempts"] += 1

    try:
        domain_file = BENCHMARKS_DIR / domain_name / "domain.pddl"
        if not domain_file.exists():
            raise FileNotFoundError(f"Missing {domain_file}")
            
        domain_str = domain_file.read_text(encoding="utf-8")
        prompt = load_prompt(planner, domain_str)
        
        config = load_config()
        hyperparams = config.get("llm_hyperparameters", {})
        temp = hyperparams.get("temperature", 0.0)
        top_p = hyperparams.get("top_p", 1.0)
        max_tokens = hyperparams.get("max_completion_tokens", 4096)
        
        print(f"[{llm_name} | {domain_name} | {planner}] Instantiating provider...")
        provider = get_provider(
            provider_name=llm_config["provider"],
            model_id=llm_config["model_id"],
            temp=temp,
            top_p=top_p,
            max_tokens=max_tokens
        )
        print(f"[{llm_name} | {domain_name} | {planner}] Provider instantiated. Starting generation...")
        
        # Retry loop setup
        max_rl_retries = retry_policy.get("rate_limit_429", {}).get("max_retries", 5)
        rl_wait = retry_policy.get("rate_limit_429", {}).get("backoff_base_seconds", 2)
        max_sv_retries = retry_policy.get("server_error_5xx", {}).get("max_retries", 3)
        sv_wait = retry_policy.get("server_error_5xx", {}).get("wait_seconds", 30)
        max_to_retries = retry_policy.get("network_timeout", {}).get("max_retries", 2)
        
        rl_attempts, sv_attempts, to_attempts = 0, 0, 0
        content, api_time, in_tokens, out_tokens = None, 0.0, 0, 0
        
        while True:
            if not pipeline_active:
                return

            try:
                content, api_time, in_tokens, out_tokens = provider.generate(prompt)
                break
                
            except RateLimitError as e:
                rl_attempts += 1
                if rl_attempts > max_rl_retries:
                    log_error("LLM", f"{domain_name} | {llm_name} | {planner}", "RateLimit", str(e), raw_dump=str(e)+"\n"+traceback.format_exc(), run_id=f"stg2_{domain_name}_{llm_name}_{planner}")
                    log_llm_generation(domain_name, llm_config["model_id"], prompt_id, "RateLimit", 0, 0, 0, "")
                    with stats_lock: llm_stats[llm_name]["rate_limit"] += 1
                    return
                time.sleep(rl_wait ** rl_attempts)
                
            except ServerError as e:
                sv_attempts += 1
                if sv_attempts > max_sv_retries:
                    log_error("LLM", f"{domain_name} | {llm_name} | {planner}", "ServerError", str(e), raw_dump=str(e)+"\n"+traceback.format_exc(), run_id=f"stg2_{domain_name}_{llm_name}_{planner}")
                    log_llm_generation(domain_name, llm_config["model_id"], prompt_id, "ServerError", 0, 0, 0, "")
                    with stats_lock: llm_stats[llm_name]["server_error"] += 1
                    return
                time.sleep(sv_wait)
                
            except NetworkTimeoutError as e:
                to_attempts += 1
                if to_attempts > max_to_retries:
                    log_error("LLM", f"{domain_name} | {llm_name} | {planner}", "NetworkTimeout", str(e), raw_dump=str(e)+"\n"+traceback.format_exc(), run_id=f"stg2_{domain_name}_{llm_name}_{planner}")
                    pipeline_active = False # HALT PIPELINE
                    with stats_lock: llm_stats[llm_name]["timeout"] += 1
                    raise Exception("NETWORK_TIMEOUT_HALT")
                time.sleep(5)
                
            except AuthError as e:
                log_error("LLM", f"{domain_name} | {llm_name} | {planner}", "AuthError", str(e), raw_dump=str(e)+"\n"+traceback.format_exc(), run_id=f"stg2_{domain_name}_{llm_name}_{planner}")
                with stats_lock: llm_stats[llm_name]["auth_error"] += 1
                pipeline_active = False # HALT
                raise Exception("AUTH_FAILURE")
                
            except EmptyResponseError as e:
                sv_attempts += 1 
                if sv_attempts > max_sv_retries:
                    log_error("LLM", f"{domain_name} | {llm_name} | {planner}", "Empty", str(e), raw_dump=str(e)+"\n"+traceback.format_exc(), run_id=f"stg2_{domain_name}_{llm_name}_{planner}")
                    log_llm_generation(domain_name, llm_config["model_id"], prompt_id, "extraction_failed", 0, 0, 0, "")
                    with stats_lock: llm_stats[llm_name]["empty"] += 1
                    return
                time.sleep(sv_wait)
                
            except TokenLimitError as e:
                log_error("LLM", f"{domain_name} | {llm_name} | {planner}", "TokenLimitExceeded", str(e), raw_dump=str(e)+"\n"+traceback.format_exc(), run_id=f"stg2_{domain_name}_{llm_name}_{planner}")
                log_llm_generation(domain_name, llm_config["model_id"], prompt_id, "token_limit", 0, 0, 0, "")
                return
                
            except LLMProviderError as e:
                dump_str = traceback.format_exc()
                log_error("LLM", f"{domain_name} | {llm_name} | {planner}", "OtherLLMError", str(e), raw_dump=dump_str, run_id=f"stg2_{domain_name}_{llm_name}_{planner}")
                # Content Filter can be lumped into OtherLLMError here, log status correspondingly
                err_lower = str(e).lower()
                status_str = "content_filtered" if "content filter" in err_lower or "safety" in err_lower else "OtherLLMError"
                log_llm_generation(domain_name, llm_config["model_id"], prompt_id, status_str, 0, 0, 0, "")
                return
                
        # Success path
        domain_results_dir = RESULTS_DIR / domain_name
        domain_results_dir.mkdir(parents=True, exist_ok=True)
        raw_resp_path = domain_results_dir / f"{domain_name}_{llm_short}_Arch_Aware_{planner}.txt"
        
        path_str = str(raw_resp_path.absolute())
        if os.name == 'nt' and not path_str.startswith('\\\\?\\'):
            path_str = '\\\\?\\' + path_str
            
        with open(path_str, "w", encoding="utf-8") as f:
            f.write(content)
            
        log_llm_generation(domain_name, llm_config["model_id"], prompt_id, "Passed", api_time, in_tokens, out_tokens, str(raw_resp_path))
        
        with stats_lock:
            llm_stats[llm_name]["success"] += 1
            llm_stats[llm_name]["input_tokens"] += in_tokens
            llm_stats[llm_name]["output_tokens"] += out_tokens
            
    except SystemExit:
        raise
    except Exception as e:
        dump_str = traceback.format_exc()
        log_error("System", f"{domain_name} | {llm_name} | {planner}", "Crash", str(e), raw_dump=dump_str, run_id=f"crash_{domain_name}_{llm_name}_{planner}")
    finally:
        with stats_lock:
            completed_runs += 1

def run_llm_docker_like(llm_config: dict, domains: list, planners: list, retry_policy: dict, all_llms: list):
    """
    Simulates a dedicated docker container for a single LLM processing 20 items.
    """
    for domain_config in domains:
        domain_name = domain_config["name"]
        for planner in planners:
            if not pipeline_active:
                break
            process_domain_for_llm(llm_config, domain_name, planner, retry_policy, all_llms)

def main():
    global pipeline_active, total_runs
    
    # Initialize TeeLogger
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    log_path = PROJECT_ROOT / "logs" / "stage2" / "LLM_run" / "terminal_output" / f"run_{timestamp}.log"
    sys.stdout = TeeLogger(log_path)
    
    print("Starting Stage 2 Arch-Aware Execution Pipeline...")
    start_time = time.time()
    
    initialize_error_logging()
    initialize_telemetry()
    
    config = load_config()
    domains = config["domains"]
    llms = config["llms"]
    planners = ["lama", "decstar", "bfws", "madagascar"]
    retry_policy = config.get("retry_policy", {})
    hb_interval = config.get("heartbeat", {}).get("interval_seconds", 60)
    
    total_runs = len(llms) * len(domains) * len(planners)
    termination_reason = "CLEAN_EXIT"
    
    hb_thread = threading.Thread(target=heartbeat_loop, args=(hb_interval,), daemon=True)
    hb_thread.start()
    
    try:
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=len(llms))
        futures = []
        for llm in llms:
            futures.append(
                executor.submit(run_llm_docker_like, llm, domains, planners, retry_policy, llms)
            )
        
        for future in concurrent.futures.as_completed(futures):
            if not pipeline_active:
                break
            try:
                future.result()
            except Exception as e:
                msg = str(e)
                if msg in ["AUTH_FAILURE", "NETWORK_TIMEOUT_HALT"]:
                    termination_reason = msg
                    pipeline_active = False
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

    except KeyboardInterrupt:
        print("\nPipeline interrupted by user.")
        termination_reason = "SIGINT"
        pipeline_active = False
    finally:
        pipeline_active = False
        hb_thread.join(timeout=2)
        elapsed = time.time() - start_time
        
        has_crashes = False
        with stats_lock:
            if completed_runs < total_runs and termination_reason == "CLEAN_EXIT":
                has_crashes = True
                termination_reason = "PARTIAL_FAIL_OR_CRASH"

        generate_run_summary(termination_reason, elapsed, llm_stats)
        print(f"Pipeline finished. Reason: {termination_reason}. See logs/stage2/LLM_run/run_summaries/ for details.")
        if termination_reason != "CLEAN_EXIT":
            os._exit(1)

if __name__ == "__main__":
    main()
