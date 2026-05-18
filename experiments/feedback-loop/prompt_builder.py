import os

def get_planner_prompt_path(planner_name, prompt_dir):
    pname = planner_name.lower()
    for f in os.listdir(prompt_dir):
        if pname in f.lower() and f.endswith(".txt"):
            return os.path.join(prompt_dir, f)
    raise ValueError(f"Could not find Architecture-Aware prompt for {planner_name}")

def build_feedback_prompt(planner_name, prompt_dir, current_domain_str, history_buffer_str, telemetry_feedback):
    prompt_path = get_planner_prompt_path(planner_name, prompt_dir)
    with open(prompt_path, "r", encoding="utf-8") as f:
        static_prompt_template = f.read()
        
    old_constraint = "- Return ONLY the complete, valid, reordered PDDL domain file."
    new_constraint = "- Before outputting the reordered PDDL, write exactly 2 sentences explaining your reordering strategy and why you expect it to improve performance. Then output the complete reordered PDDL domain file."
    if old_constraint in static_prompt_template:
        static_prompt_template = static_prompt_template.replace(old_constraint, new_constraint)
    else:
        static_prompt_template = static_prompt_template.replace("STRICT CONSTRAINTS:", "STRICT CONSTRAINTS:\n" + new_constraint)

    if "DOMAIN TO REORDER:" in static_prompt_template:
        static_prompt_template = static_prompt_template.split("DOMAIN TO REORDER:")[0].strip()

    prompt_parts = [
        static_prompt_template,
        history_buffer_str,
        telemetry_feedback,
        "DOMAIN TO REORDER:\n" + current_domain_str
    ]
    
    prompt_text = "\n\n---\n\n".join(prompt_parts)
    return prompt_text
