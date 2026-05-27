# -*- coding: utf-8 -*-
"""
Task Router Module.
Determines optimal task distribution among available specialist teams.
"""
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TaskRouter")

class TaskRouter:
    def __init__(self):
        # Route mapping mapping task keywords to specialist layers
        self.routes = {
            "ui": "design",
            "mockup": "design",
            "frontend": "engineering",
            "backend": "engineering",
            "database": "architecture",
            "schema": "architecture",
            "security": "architecture",
            "test": "validation",
            "qa": "validation",
            "deploy": "infrastructure",
            "sre": "infrastructure",
            "prompt": "ai_systems",
            "rag": "ai_systems",
            "mcp": "ai_systems"
        }

    def route_task(self, task_name: str) -> str:
        """
        Examines task metadata to assign to correct agent layer.
        """
        task_lower = task_name.lower()
        for keyword, layer in self.routes.items():
            if keyword in task_lower:
                logger.info(f"Routing task '{task_name}' to layer '{layer}'")
                return layer
        logger.warning(f"No explicit route found for '{task_name}'. Defaulting to engineering.")
        return "engineering"
