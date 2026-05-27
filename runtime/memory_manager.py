# -*- coding: utf-8 -*-
"""
Memory Manager Module.
Coordinates read/write operations across Global, Project, and Agent memory layers.
"""
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MemoryManager")

class MemoryManager:
    def __init__(self, memory_dir: str = "../memory"):
        self.memory_dir = memory_dir

    def persist_decision(self, decision_id: str, decision_data: dict) -> None:
        """
        Writes critical technical decisions to shared memory file.
        """
        decisions_file = os.path.join(self.memory_dir, "technical_decisions.md")
        logger.info(f"Persisting technical decision: {decision_id}")
        
        # Append decision to file
        with open(decisions_file, "a", encoding="utf-8") as f:
            f.write(f"\n### Decision: {decision_id}\n")
            for k, v in decision_data.items():
                f.write(f"- **{k}**: {v}\n")
