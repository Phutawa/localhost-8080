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
        # Locate package root to load configs
        package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_path = os.path.join(package_root, "configs", "orchestrator_config.json")
        self.skills_dir = os.path.join(package_root, "skills")
        self.config = {}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config file: {e}")

    def load_agent_profile(self, layer: str, agent_name: str) -> dict:
        """
        Loads an agent markdown profile and extracts core properties.
        Also dynamically injects Superpowers and GSD frameworks if enabled.
        """
        profile_path = os.path.join(self.agents_dir, layer, f"{agent_name}.md")
        if not os.path.exists(profile_path):
            raise FileNotFoundError(f"Agent profile not found at {profile_path}")
        
        logger.info(f"Loading agent profile: {layer}/{agent_name}")
        with open(profile_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Inject Superpowers Guidelines if enabled in config
        capabilities = self.config.get("developer_capabilities", {})
        if capabilities.get("enable_superpowers", False):
            superpowers_path = os.path.join(self.skills_dir, "superpowers_skill.md")
            if os.path.exists(superpowers_path):
                logger.info(f"Injecting Superpowers guidelines into system prompt for {agent_name}")
                try:
                    with open(superpowers_path, "r", encoding="utf-8") as sf:
                        superpowers_content = sf.read()
                    content = content + "\n\n=== INJECTED FRAMEWORK: SUPERPOWERS ===\n" + superpowers_content
                except Exception as e:
                    logger.error(f"Failed to read superpowers skill file: {e}")

        # Skeleton parser for markdown headers
        profile = {
            "name": agent_name,
            "layer": layer,
            "raw_content": content
        }
        return profile
