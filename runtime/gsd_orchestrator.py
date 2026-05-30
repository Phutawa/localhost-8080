# -*- coding: utf-8 -*-
"""
GSD (Get Shit Done) Orchestrator Module.
Decomposes complex parent tasks into isolated sub-agent tasks, executes them in parallel,
and validates their deliverables through Quality Gates before compiling the final result.
"""
import logging
import json
from runtime.llm_provider import LLMProvider
from runtime.context_manager import ContextManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GsdOrchestrator")

class GsdOrchestrator:
    def __init__(self, context_manager: ContextManager):
        self.context_manager = context_manager

    def orchestrate_task(self, parent_task_desc: str, agent_name: str, agent_context: str) -> str:
        """
        Main orchestration entry point. Decomposes tasks, executes sub-agents,
        verifies quality gates, and compiles output.
        """
        logger.info(f"[GSD Orchestrator] Intercepted task for {agent_name}. Initiating decomposition...")
        
        # 1. Ask LLM to break down task into JSON sub-tasks
        planning_prompt = f"""
Parent Task:
{parent_task_desc}

Break this task down into 2 to 3 isolated, sequential sub-tasks that can be executed by separate virtual sub-agents.
For each sub-task, provide a 'title', 'instructions', and 'validation_criteria'.
Return ONLY a valid JSON list of objects matching this schema:
[
  {{"title": "...", "instructions": "...", "validation_criteria": "..."}}
]
"""
        try:
            plan_response = LLMProvider.generate(prompt=planning_prompt, system_prompt=agent_context)
            # Simple JSON extraction from markdown code block if present
            json_match = json.search(r'\[\s*\{[\s\S]*\}\s*\]', plan_response) if hasattr(json, 'search') else None
            
            # Use regex for extraction just in case it wraps in markdown
            import re
            match = re.search(r'\[\s*\{[\s\S]*\}\s*\]', plan_response)
            if match:
                plan_json = json.loads(match.group(0))
            else:
                plan_json = json.loads(plan_response)
        except Exception as e:
            logger.warning(f"[GSD Orchestrator] Failed to parse decomposition plan JSON: {e}. Executing as single task fallback.")
            return LLMProvider.generate(prompt=parent_task_desc, system_prompt=agent_context)

        logger.info(f"[GSD Orchestrator] Decomposed task into {len(plan_json)} steps.")
        
        sub_results = []
        # 2. Iterate and execute each sub-task in isolated contexts
        for idx, sub_task in enumerate(plan_json):
            sub_title = sub_task.get("title", f"Sub-task {idx}")
            sub_instructions = sub_task.get("instructions", "")
            val_criteria = sub_task.get("validation_criteria", "")
            
            sub_agent_id = f"{agent_name}_sub_{idx}"
            logger.info(f"🚩 Executing GSD Step {idx + 1}: '{sub_title}' via virtual agent '{sub_agent_id}'")
            
            # Setup fresh context
            self.context_manager.init_context(sub_agent_id)
            
            # Build execution prompt including previous sub-task results to retain context chain
            context_chain = ""
            if sub_results:
                context_chain = "\n\nHere are the results of completed previous steps:\n"
                for prev_title, prev_res in sub_results:
                    context_chain += f"--- Result of '{prev_title}': ---\n{prev_res}\n\n"

            sub_prompt = f"""
Instructions for this step:
{sub_instructions}
{context_chain}
Execute this sub-task and provide your output.
"""
            # Run Sub-agent
            sub_output = LLMProvider.generate(prompt=sub_prompt, system_prompt=agent_context)
            
            # 3. Quality Gate (Validation check)
            logger.info(f"[GSD Quality Gate] Verifying step '{sub_title}'...")
            gate_prompt = f"""
Output to verify:
{sub_output}

Validation Criteria:
{val_criteria}

Does the output meet the validation criteria? Answer with "PASSED" or "FAILED" on the first line, followed by detailed reasons.
"""
            gate_result = LLMProvider.generate(prompt=gate_prompt, system_prompt="You are a Quality Gate Auditor.")
            if "FAILED" in gate_result.splitlines()[0].upper():
                logger.warning(f"[GSD Quality Gate] Stage failed validation. Retrying with feedback...")
                retry_prompt = f"""
Your previous output failed validation.
Feedback:
{gate_result}

Please correct the output and resubmit.
"""
                sub_output = LLMProvider.generate(prompt=retry_prompt, system_prompt=agent_context)
            else:
                logger.info(f"[GSD Quality Gate] Step '{sub_title}' successfully PASSED!")

            sub_results.append((sub_title, sub_output))
            
        # 4. Compile final summary
        compilation_prompt = f"""
Compile the following sub-task results into a final cohesive deliverable that satisfies the original parent task request:
Original Request: {parent_task_desc}

Sub-task outputs:
"""
        for title, res in sub_results:
            compilation_prompt += f"\n--- {title} Output ---\n{res}\n"
            
        final_deliverable = LLMProvider.generate(prompt=compilation_prompt, system_prompt=agent_context)
        logger.info(f"[GSD Orchestrator] Task execution completed. Final compiled.")
        return final_deliverable
