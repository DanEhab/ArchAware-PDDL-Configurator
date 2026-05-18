import os
import sys

# Add repo root to python path to allow imports
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(repo_root)
sys.path.append(os.path.dirname(__file__))

from loop_engine import run_feedback_loop
from run_stage3 import resolve_seed_domain, get_test_instances

def main():
    print("Testing pipeline on visitall, lama, and gpt-5.4-2026-03-05...")
    
    domain = "visitall"
    planner = "lama"
    llm = "gpt-5.4-2026-03-05"
    output_dir = os.path.join(repo_root, "results", "feedback_loop")
    os.makedirs(output_dir, exist_ok=True)
    
    # We only take the first instance to avoid 5-minute timeouts during testing
    test_instances = get_test_instances(domain)[:1]
    
    seed_domain_path, stage0_baseline_path, init_hist, init_tel, stage2_ipc, is_valid_seed = resolve_seed_domain(domain, planner, llm)
    
    # Run the feedback loop for this triple
    try:
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
            max_iter=1 # Run just 1 iteration for testing
        )
        print("Pipeline test completed successfully.")
    except Exception as e:
        print(f"Pipeline test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
