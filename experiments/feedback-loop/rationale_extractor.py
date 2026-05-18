def extract_rationale(llm_response_text):
    """
    Extracts the 2-sentence rationale from the LLM response before the PDDL code block.
    """
    text_lower = llm_response_text.lower()
    idx_pddl = llm_response_text.find("```lisp")
    if idx_pddl == -1: idx_pddl = llm_response_text.find("```pddl")
    if idx_pddl == -1: idx_pddl = llm_response_text.find("(define (domain")
    if idx_pddl == -1: idx_pddl = llm_response_text.find("(define(domain")
    
    if idx_pddl > 0:
        rationale = llm_response_text[:idx_pddl].strip()
        rationale = rationale.replace("```", "").strip()
        return rationale
    return "No clear rationale provided before PDDL block."
