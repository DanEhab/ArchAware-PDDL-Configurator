import os
import csv
from datetime import datetime
from pathlib import Path

# Directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
LOGS_DIR = PROJECT_ROOT / "logs" / "stage1" / "LLM_run"
ERROR_DUMPS_DIR = LOGS_DIR / "error_dumps"
ERROR_REGISTER_FILE = LOGS_DIR / "error_register.csv"

ERROR_REGISTER_HEADERS = [
    "Timestamp",
    "Component",
    "Affected_Parameters",
    "Error_Classification",
    "Message"
]

def initialize_error_logging():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    ERROR_DUMPS_DIR.mkdir(parents=True, exist_ok=True)

    if not ERROR_REGISTER_FILE.exists():
        with open(ERROR_REGISTER_FILE, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(ERROR_REGISTER_HEADERS)

def log_error(component: str, affected_parameters: str, classification: str, message: str, raw_dump: str = None, run_id: str = None):
    """
    Logs an error to the central error_register.csv and optionally dumps a raw traceback or output.
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    # Write to register
    with open(ERROR_REGISTER_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, component, affected_parameters, classification, message])
    
    # Write raw dump if provided
    if raw_dump and run_id:
        dump_filename = f"{run_id}_{classification.replace(' ', '_')}.txt"
        dump_path = ERROR_DUMPS_DIR / dump_filename
        with open(dump_path, mode="w", encoding="utf-8") as f:
            f.write(raw_dump)
