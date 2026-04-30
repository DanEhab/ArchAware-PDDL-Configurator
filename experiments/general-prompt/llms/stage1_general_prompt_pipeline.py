import sys
import time
import yaml
import threading
import concurrent.futures
import traceback
from pathlib import Path
from datetime import datetime

# Local modules
from llm_providers import (
    get_provider, AuthError, RateLimitError, ServerError, 
    NetworkTimeoutError, EmptyResponseError, TokenLimitError, LLMProviderError
)
from error_logging import initialize_error_logging, log_error
from telemetry_tracker import initialize_telemetry, log_llm_generation, generate_run_summary

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "experiment_config.yaml"
BENCHMARKS_DIR = PROJECT_ROOT / "benchmarks"
RESULTS_DIR = PROJECT_ROOT / "results" / "general_prompt" / "LLM Results"

# Global Stats Tracking
stats_lock = threading.Lock()
llm_stats = {}
pipeline_active = True
completed_runs = 0
total_runs = 0

def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def generate_prompt(domain_str: str) -> str:
    return f"""You are a PDDL domain expert.
Your task is to reorder the following PDDL domain file to improve AI planner
efficiency (coverage , time, quality) via
reordering actions , preconditions , and effects. You may not change the
semantics of the domain in any way.
Follow best practices from planning literature.
IMPORTANT:
- Do NOT rename , remove , or semantically change any predicates , parameters , or
actions.
- Do NOT add comments , explanations , or formatting.
- Return ONLY a valid reordered PDDL domain file.
DOMAIN TO REORDER:
{domain_str}
"""

def heartbeat_loop(interval_seconds: int):
    log_file = PROJECT_ROOT / "logs" / "stage1" / "LLM_run" / "pipeline_heartbeat.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    while pipeline_active:
        with stats_lock:
            percent = (completed_runs / total_runs * 100) if total_runs > 0 else 0
            msg = f"[{datetime.utcnow().isoformat() + 'Z'}] Completion: {completed_runs}/{total_runs} ({percent:.1f}%)\n"
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(msg)
            
        # Wait in small increments so we can exit quickly
        for _ in range(interval_seconds):
            if not pipeline_active: break
            time.sleep(1)

def process_domain_for_llm(llm_config: dict, domain_config: dict, retry_policy: dict):
    global completed_runs, pipeline_active
    
    llm_name = llm_config["name"]
    domain_name = domain_config["name"]
    
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
        prompt = generate_prompt(domain_str)
        
        config = load_config()
        hyperparams = config.get("llm_hyperparameters", {})
        temp = hyperparams.get("temperature", 0.0)
        top_p = hyperparams.get("top_p", 1.0)
        max_tokens = hyperparams.get("max_completion_tokens", 4096)
        
        print(f"[{llm_name}] Instantiating provider...")
        provider = get_provider(
            provider_name=llm_config["provider"],
            model_id=llm_config["model_id"],
            temp=temp,
            top_p=top_p,
            max_tokens=max_tokens
        )
        print(f"[{llm_name}] Provider instantiated. Starting generation for {domain_name}...")
        
        # Retry loop setup
        max_rl_retries = retry_policy.get("rate_limit_429", {}).get("max_retries", 5)
        rl_wait = retry_policy.get("rate_limit_429", {}).get("backoff_base_seconds", 2)
        
        max_sv_retries = retry_policy.get("server_error_5xx", {}).get("max_retries", 3)
        sv_wait = retry_policy.get("server_error_5xx", {}).get("wait_seconds", 30)
        
        max_to_retries = retry_policy.get("network_timeout", {}).get("max_retries", 2)
        
        rl_attempts = 0
        sv_attempts = 0
        to_attempts = 0
        
        content = None
        api_time = 0.0
        in_tokens = 0
        out_tokens = 0
        
        while True:
            if not pipeline_active:
                return # Abort if halted globally

            try:
                content, api_time, in_tokens, out_tokens = provider.generate(prompt)
                break # Success
                
            except RateLimitError as e:
                rl_attempts += 1
                if rl_attempts > max_rl_retries:
                    log_error("LLM", f"{domain_name} | {llm_name}", "RateLimit", str(e), raw_dump=str(e) + "\n" + traceback.format_exc(), run_id=f"stg1_{domain_name}_{llm_name}")
                    log_llm_generation(domain_name, llm_config["model_id"], 1, "RateLimit", 0, 0, 0, "")
                    with stats_lock: llm_stats[llm_name]["rate_limit"] += 1
                    return
                time.sleep(rl_wait ** rl_attempts) # Exponential backoff
                
            except ServerError as e:
                sv_attempts += 1
                if sv_attempts > max_sv_retries:
                    log_error("LLM", f"{domain_name} | {llm_name}", "ServerError", str(e), raw_dump=str(e) + "\n" + traceback.format_exc(), run_id=f"stg1_{domain_name}_{llm_name}")
                    log_llm_generation(domain_name, llm_config["model_id"], 1, "ServerError", 0, 0, 0, "")
                    with stats_lock: llm_stats[llm_name]["server_error"] += 1
                    return
                time.sleep(sv_wait)
                
            except NetworkTimeoutError as e:
                to_attempts += 1
                if to_attempts > max_to_retries:
                    log_error("LLM", f"{domain_name} | {llm_name}", "NetworkTimeout", str(e), raw_dump=str(e) + "\n" + traceback.format_exc(), run_id=f"stg1_{domain_name}_{llm_name}")
                    pipeline_active = False # HALT PIPELINE
                    with stats_lock: llm_stats[llm_name]["timeout"] += 1
                    raise Exception("NETWORK_TIMEOUT_HALT")
                time.sleep(5)
                
            except AuthError as e:
                log_error("LLM", f"{domain_name} | {llm_name}", "AuthError", str(e), raw_dump=str(e) + "\n" + traceback.format_exc(), run_id=f"stg1_{domain_name}_{llm_name}")
                with stats_lock: llm_stats[llm_name]["auth_error"] += 1
                pipeline_active = False # IMMEDIATE HALT
                raise Exception("AUTH_FAILURE")
                
            except EmptyResponseError as e:
                sv_attempts += 1 # Treat empty as server error/safety trip
                if sv_attempts > max_sv_retries:
                    log_error("LLM", f"{domain_name} | {llm_name}", "Empty", str(e), raw_dump=str(e) + "\n" + traceback.format_exc(), run_id=f"stg1_{domain_name}_{llm_name}")
                    log_llm_generation(domain_name, llm_config["model_id"], 1, "Empty", 0, 0, 0, "")
                    with stats_lock: llm_stats[llm_name]["empty"] += 1
                    return
                time.sleep(sv_wait)
                
            except TokenLimitError as e:
                log_error("LLM", f"{domain_name} | {llm_name}", "TokenLimitExceeded", str(e), raw_dump=str(e) + "\n" + traceback.format_exc(), run_id=f"stg1_{domain_name}_{llm_name}")
                log_llm_generation(domain_name, llm_config["model_id"], 1, "TokenLimitExceeded", 0, 0, 0, "")
                return
                
            except LLMProviderError as e:
                # Other errors
                dump_str = traceback.format_exc()
                log_error("LLM", f"{domain_name} | {llm_name}", "OtherLLMError", str(e), raw_dump=dump_str, run_id=f"stg1_{domain_name}_{llm_name}")
                return
                
        # If we reach here, we succeeded!
        domain_results_dir = RESULTS_DIR / domain_name
        domain_results_dir.mkdir(parents=True, exist_ok=True)
        raw_resp_path = domain_results_dir / f"{domain_name}_{llm_name}_General.txt"
        
        path_str = str(raw_resp_path.absolute())
        import os
        if os.name == 'nt' and not path_str.startswith('\\\\?\\'):
            path_str = '\\\\?\\' + path_str
            
        with open(path_str, "w", encoding="utf-8") as f:
            f.write(content)
            
        log_llm_generation(domain_name, llm_config["model_id"], 1, "Passed", api_time, in_tokens, out_tokens, str(raw_resp_path))
        
        with stats_lock:
            llm_stats[llm_name]["success"] += 1
            llm_stats[llm_name]["input_tokens"] += in_tokens
            llm_stats[llm_name]["output_tokens"] += out_tokens
            
    except SystemExit:
        raise
    except Exception as e:
        dump_str = traceback.format_exc()
        log_error("System", f"{domain_name} | {llm_name}", "Crash", str(e), raw_dump=dump_str, run_id=f"crash_{domain_name}_{llm_name}")
    finally:
        with stats_lock:
            completed_runs += 1

def run_llm_docker_like(llm_config: dict, domains: list, retry_policy: dict):
    """
    Simulates a dedicated docker container for a single LLM,
    sequentially processing its assigned domains.
    """
    for domain in domains:
        if not pipeline_active:
            break
        process_domain_for_llm(llm_config, domain, retry_policy)

def main():
    global pipeline_active, total_runs
    
    print("Starting Stage 1 Execution Pipeline...")
    start_time = time.time()
    
    initialize_error_logging()
    initialize_telemetry()
    
    config = load_config()
    domains = config["domains"]
    llms = config["llms"]
    retry_policy = config.get("retry_policy", {})
    hb_interval = config.get("heartbeat", {}).get("interval_seconds", 60)
    
    total_runs = len(llms) * len(domains)
    termination_reason = "CLEAN_EXIT"
    
    hb_thread = threading.Thread(target=heartbeat_loop, args=(hb_interval,), daemon=True)
    hb_thread.start()
    
    try:
        # Launch exactly 1 worker thread per LLM (Docker-like parallelism)
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=len(llms))
        futures = []
        for llm in llms:
            futures.append(
                executor.submit(run_llm_docker_like, llm, domains, retry_policy)
            )
        
        for future in concurrent.futures.as_completed(futures):
            if not pipeline_active:
                break
            try:
                future.result() # Will raise if AuthError/SystemExit triggered inside
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
        
        # Check if any crashes occurred
        has_crashes = False
        with stats_lock:
            if completed_runs < total_runs and termination_reason == "CLEAN_EXIT":
                has_crashes = True
                termination_reason = "PARTIAL_FAIL_OR_CRASH"

        generate_run_summary(termination_reason, elapsed, llm_stats)
        print(f"Pipeline finished. Reason: {termination_reason}. See logs/stage1/LLM_run/run_summaries/ for details.")
        if termination_reason != "CLEAN_EXIT":
            import os
            os._exit(1)

if __name__ == "__main__":
    main()
