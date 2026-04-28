"""
Execution Tester for LAMA Planner (baseline-lama-first)
=======================================================
Tests the LAMA Docker container against the tiny-test snake domain.

Usage:
  1. Ensure Docker Desktop is running
  2. docker build -f planners/lama/Dockerfile -t lama_planner .
  3. python test_planner_lama.py
"""

import sys
import subprocess
import os
import platform
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent
DOMAIN_FILE = PROJECT_ROOT / "benchmarks" / "snake" / "domain.pddl"
PROBLEM_FILE = PROJECT_ROOT / "benchmarks" / "snake" / "instances" / "instance-08.pddl"

def run_lama(domain_path: Path, problem_path: Path):
    benchmark_dir = domain_path.parent.parent.resolve()
    
    # Calculate relative paths within the docker container volume mount
    d_rel = domain_path.relative_to(benchmark_dir).as_posix()
    p_rel = problem_path.relative_to(benchmark_dir).as_posix()
    
    mount_str = str(benchmark_dir)
    # Modern Docker Desktop accepts native Windows paths (e.g., D:\...) directly.
        
    docker_cmd = [
        "docker", "run", "--rm",
        "--cpus=1.0",           
        "--memory=8g",      
        "--memory-swap=8g",            
        "--oom-kill-disable=false",            
        "-v", f"{mount_str}:/pddl",
        "lama_planner",
        f"/pddl/{d_rel}",
        f"/pddl/{p_rel}"
    ]
    
    print("Executing command:", " ".join(docker_cmd))
    
    try:
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=315 
        )
        print("\n--- STDOUT ---")
        print(result.stdout)
        
        if result.stderr:
            print("\n--- STDERR ---")
            print(result.stderr)
            
    except Exception as e:
        print(f"Error running Docker: {e}")

if __name__ == "__main__":
    if not DOMAIN_FILE.exists() or not PROBLEM_FILE.exists():
        print("Domain or Problem file not found.")
        sys.exit(1)
        
    # Check if docker daemon is running
    chk = subprocess.run(["docker", "info"], capture_output=True)
    if chk.returncode != 0:
        print("ERROR: Docker daemon is not running. Please start Docker Desktop first.")
        sys.exit(1)
        
    # Check if image exists
    # img_chk = subprocess.run(["docker", "image", "inspect", "lama_planner"], capture_output=True)
    # if img_chk.returncode != 0:
    #     print("ERROR: Docker image 'lama_planner' not found.")
    #     print("DEBUG OUTPUT FROM DOCKER:")
    #     print(f"STDOUT: {img_chk.stdout.decode('utf-8', errors='ignore')}")
    #     print(f"STDERR: {img_chk.stderr.decode('utf-8', errors='ignore')}")
    #     print("Please build it first running this command in the project root:")
    #     print("docker build -f planners/lama/Dockerfile -t lama_planner .")
    #     sys.exit(1)
        
    print(f"Running LAMA (lama-first) against:")
    print(f"  Domain: {DOMAIN_FILE}")
    print(f"  Problem: {PROBLEM_FILE}\n")
    
    run_lama(DOMAIN_FILE, PROBLEM_FILE)
