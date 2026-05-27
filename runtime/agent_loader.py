# -*- coding: utf-8 -*-
"""
Agent Loader Module.
Responsible for loading specialist templates and injecting scoped system prompts.
"""
import os
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AgentLoader")

class AgentLoader:
    def __init__(self, agents_dir: str = "../agents"):
        self.agents_dir = agents_dir

    def load_agent_profile(self, layer: str, agent_name: str) -> dict:
        """
        Loads an agent markdown profile and extracts core properties.
        """
        profile_path = os.path.join(self.agents_dir, layer, f"{agent_name}.md")
        if not os.path.exists(profile_path):
            raise FileNotFoundError(f"Agent profile not found at {profile_path}")
        
        logger.info(f"Loading agent profile: {layer}/{agent_name}")
        with open(profile_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Skeleton parser for markdown headers
        profile = {
            "name": agent_name,
            "layer": layer,
            "raw_content": content
        }
        return profile
