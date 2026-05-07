import csv
import os
import threading
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
LLM_GEN_FILE_GLOBAL = RESULTS_DIR / "llm_generation_data.csv"
LLM_GEN_FILE_STAGE2 = RESULTS_DIR / "arch_aware" / "LLM Results" / "arch_aware_llm_generation_data.csv"
SUMMARIES_DIR = PROJECT_ROOT / "logs" / "stage2" / "LLM_run" / "run_summaries"

# Global lock for thread-safe CSV writing
telemetry_lock = threading.Lock()

LLM_GEN_HEADERS = [
    "ID", "Domain Name", "LLM Model", "Prompt ID", "LLM_Status", 
    "LLM API Time S", "Input Tokens Consumed", "Output Tokens Generated", 
    "Path to Raw LLM Response", "Passed Stage V1", "Path to Extracted PDDL", 
    "Passed VAL Syntactic Check (V2)", "VAL_error_string", "Passed V3", 
    "Passed V4", "Validation Status", "Timestamp"
]

def initialize_telemetry():
    with telemetry_lock:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        (RESULTS_DIR / "arch_aware" / "LLM Results").mkdir(parents=True, exist_ok=True)
        SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)
        
        if not LLM_GEN_FILE_GLOBAL.exists() or os.path.getsize(LLM_GEN_FILE_GLOBAL) == 0:
            with open(LLM_GEN_FILE_GLOBAL, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(LLM_GEN_HEADERS)
                
        if not LLM_GEN_FILE_STAGE2.exists() or os.path.getsize(LLM_GEN_FILE_STAGE2) == 0:
            with open(LLM_GEN_FILE_STAGE2, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(LLM_GEN_HEADERS)

def get_next_llm_gen_id() -> int:
    if not LLM_GEN_FILE_GLOBAL.exists() or os.path.getsize(LLM_GEN_FILE_GLOBAL) == 0:
        return 1
    with open(LLM_GEN_FILE_GLOBAL, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        lines = list(reader)
        if len(lines) <= 1:
            return 1
        last_id = lines[-1][0]
        try:
            return int(last_id) + 1
        except ValueError:
            return len(lines)

def log_llm_generation(
    domain_name: str, llm_model: str, prompt_id: int, llm_status: str, 
    api_time: float, input_tokens: int, output_tokens: int, raw_response_path: str
):
    with telemetry_lock:
        timestamp = datetime.utcnow().isoformat() + "Z"
        record_id = get_next_llm_gen_id()
        
        row = [
            record_id, domain_name, llm_model, prompt_id, llm_status,
            f"{api_time:.3f}" if api_time is not None else "",
            input_tokens if input_tokens is not None else "",
            output_tokens if output_tokens is not None else "",
            raw_response_path,
            "", "", "", "", "", "", "", timestamp
        ]
        
        for file_path in [LLM_GEN_FILE_GLOBAL, LLM_GEN_FILE_STAGE2]:
            with open(file_path, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(row)
        
def generate_run_summary(termination_reason: str, elapsed_time_s: float, llm_stats: dict):
    """
    Generates a markdown summary of the run in logs/stage2/LLM_run/run_summaries/
    """
    existing_summaries = list(SUMMARIES_DIR.glob("run_summary_*.md"))
    next_idx = len(existing_summaries) + 1
    summary_path = SUMMARIES_DIR / f"run_summary_{next_idx}.md"
    
    content = f"# Pipeline Execution Summary (Stage 2)\n\n"
    content += f"**Termination Reason:** {termination_reason}\n"
    content += f"**Elapsed Processing Time:** {elapsed_time_s:.2f} seconds\n"
    content += f"**Timestamp (UTC):** {datetime.utcnow().isoformat() + 'Z'}\n\n"
    
    content += "## LLM API Execution Stats\n"
    content += "| LLM Model | Attempts | Success | RateLimit | ServerError | AuthError | Timeout | Empty | Total Input Tokens | Total Output Tokens |\n"
    content += "|---|---|---|---|---|---|---|---|---|---|\n"
    
    for model, stats in llm_stats.items():
        content += f"| {model} | {stats.get('attempts', 0)} | {stats.get('success', 0)} | "
        content += f"{stats.get('rate_limit', 0)} | {stats.get('server_error', 0)} | "
        content += f"{stats.get('auth_error', 0)} | {stats.get('timeout', 0)} | "
        content += f"{stats.get('empty', 0)} | {stats.get('input_tokens', 0)} | "
        content += f"{stats.get('output_tokens', 0)} |\n"
        
    with open(summary_path, mode="w", encoding="utf-8") as f:
        f.write(content)
