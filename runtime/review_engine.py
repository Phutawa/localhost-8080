# -*- coding: utf-8 -*-
"""
Review Engine Module.
Implements '/review' (fast local code review) and '/ultra-review'
(parallel multi-agent review targeting logic, security, performance, and edge cases).
"""
import os
import logging
import concurrent.futures
from runtime.llm_provider import LLMProvider
from runtime.agent_loader import AgentLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ReviewEngine")

class ReviewEngine:
    def __init__(self, agents_dir: str = "agents"):
        self.agent_loader = AgentLoader(agents_dir=agents_dir)

    def _read_target_files(self, workspace_dir: str, file_paths: list) -> str:
        """
        Reads and compiles file contents into a single text representation.
        """
        compiled_code = ""
        for relative_path in file_paths:
            abs_path = os.path.join(workspace_dir, relative_path)
            if os.path.exists(abs_path) and os.path.isfile(abs_path):
                try:
                    with open(abs_path, "r", encoding="utf-8") as f:
                        code = f.read()
                    compiled_code += f"\n--- FILE: {relative_path} ---\n{code}\n--- END OF FILE ---\n"
                except Exception as e:
                    logger.warning(f"Could not read {relative_path}: {e}")
        return compiled_code

    def run_local_review(self, workspace_dir: str, file_paths: list) -> str:
        """
        Fast local code review using standard code_reviewer profile.
        """
        logger.info("Starting local code review (/review)...")
        code_content = self._read_target_files(workspace_dir, file_paths)
        if not code_content:
            return "[Review Error] No files loaded for review."

        try:
            profile = self.agent_loader.load_agent_profile("validation", "code_reviewer")
            system_prompt = profile.get("raw_content", "You are an expert Code Reviewer.")
        except Exception:
            system_prompt = "You are a senior Code Reviewer. Inspect the code for bugs, style, and correctness."

        prompt = f"""
Code to review:
{code_content}

Conduct a fast, local code review. Identify:
1. Logic issues and potential bugs.
2. Code style and readability improvements.
3. Minor edge cases.
"""
        return LLMProvider.generate(prompt=prompt, system_prompt=system_prompt)

    def run_ultra_review(self, workspace_dir: str, file_paths: list) -> str:
        """
        Run multi-agent parallel review (/ultra-review).
        Each agent reviews code from a specific dimension.
        Reported issues MUST be reproduced or proved (no nitpicking).
        """
        logger.info("Starting parallel multi-agent ultra-review (/ultra-review)...")
        code_content = self._read_target_files(workspace_dir, file_paths)
        if not code_content:
            return "[Review Error] No files loaded for review."

        reviewers = [
            {"role": "Code Logic & Readability Reviewer", "profile_layer": "validation", "profile_name": "code_reviewer", 
             "focus": "Inspect code for logic flaws, incorrect branching, or buffer overflows. Every bug must be backed by a clear code path explanation."},
            {"role": "Security Auditor", "profile_layer": "architecture", "profile_name": "security_architect", 
             "focus": "Inspect code for security exploits, injection vulnerabilities, and credential leakage. Verify with a proof-of-concept description."},
            {"role": "Performance Auditor", "profile_layer": "validation", "profile_name": "performance_tester", 
             "focus": "Audit memory footprint, CPU bottlenecks, denormals, GC allocation in loops. Explain performance degradation scenarios."},
            {"role": "Edge Case & QA Specialist", "profile_layer": "validation", "profile_name": "qa_engineer", 
             "focus": "Inspect boundary limits (empty values, negative, extremely high signals, NaNs). Define a concrete unit-test simulation to prove each issue."}
        ]

        def run_single_reviewer(rev_info):
            logger.info(f"Launching parallel reviewer: {rev_info['role']}")
            try:
                profile = self.agent_loader.load_agent_profile(rev_info["profile_layer"], rev_info["profile_name"])
                sys_prompt = profile.get("raw_content", f"You are a {rev_info['role']}.")
            except Exception:
                sys_prompt = f"You are a specialized {rev_info['role']}."

            prompt = f"""
Code under review:
{code_content}

Focus Area:
{rev_info['focus']}

Guidelines:
1. Only list verified bugs or issues.
2. For each issue reported, you MUST write a 'Reproduction Proof / Proof of Concept' explaining the exact conditions or input data that triggers the failure.
3. If an issue cannot be verified or reproduced, do NOT report it. Avoid general nitpicks.
"""
            report = LLMProvider.generate(prompt=prompt, system_prompt=sys_prompt)
            return f"### Dimension: {rev_info['role']}\n\n{report}\n\n"

        # Execute reviews concurrently
        reports = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_reviewer = {executor.submit(run_single_reviewer, r): r for r in reviewers}
            for future in concurrent.futures.as_completed(future_to_reviewer):
                try:
                    reports.append(future.result())
                except Exception as e:
                    reviewer = future_to_reviewer[future]
                    logger.error(f"{reviewer['role']} failed: {e}")
                    reports.append(f"### Dimension: {reviewer['role']}\n\nFailed to run review: {e}\n\n")

        header = "# Multi-Agent Ultra-Review Report\n\nAll dimensions run concurrently. Only verified and reproducible issues are logged.\n\n---\n\n"
        return header + "\n".join(reports)
