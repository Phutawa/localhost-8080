import os
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ContextManager")

class ContextManager:
    def __init__(self, max_tokens: int = 32768):
        self.max_tokens = max_tokens
        self.active_contexts = {}
        # Resolve package root and load configuration
        package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_path = os.path.join(package_root, "configs", "orchestrator_config.json")
        self.config = {}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config file: {e}")

    def init_context(self, agent_id: str) -> dict:
        """
        Allocates isolated context memory state for a new agent.
        """
        logger.info(f"Initializing isolated context for agent: {agent_id}")
        self.active_contexts[agent_id] = {
            "tokens_used": 0,
            "messages": [],
            "variables": {}
        }
        return self.active_contexts[agent_id]

    def prune_context(self, agent_id: str) -> None:
        """
        Prunes redundant trace logs or compresses conversation when nearing token limit.
        If GSD (Get Shit Done) mode is enabled, aggressively prunes intermediate discussion
        while preserving initial requirements and latest turns to prevent context bloat.
        """
        if agent_id not in self.active_contexts:
            return
        
        ctx = self.active_contexts[agent_id]
        
        # Check if GSD is enabled
        capabilities = self.config.get("developer_capabilities", {})
        enable_gsd = capabilities.get("enable_gsd", False)
        
        if enable_gsd:
            # GSD Pruning strategy:
            # Keep initial instruction/requirement prompt (index 0)
            # Keep only the last 2 turns (last 4 messages: user, model, user, model)
            # Remove everything in between to keep the context window completely clean and fast.
            num_messages = len(ctx["messages"])
            if num_messages > 5:
                logger.info(f"[GSD Alert] Pruning intermediate context for {agent_id} to keep context window clean.")
                preserved_first = ctx["messages"][0:1] # Keep the very first prompt/context
                preserved_last = ctx["messages"][-4:]  # Keep the last 2 complete turns
                ctx["messages"] = preserved_first + preserved_last
                
                # Re-estimate tokens
                total_len = sum(len(m.get("content", "")) for m in ctx["messages"])
                ctx["tokens_used"] = total_len // 4
                logger.info(f"[GSD Alert] Context pruned successfully. New token usage estimate: {ctx['tokens_used']}")
                return

        # Fallback to standard pruning if threshold breached
        if ctx["tokens_used"] > self.max_tokens * 0.8:
            logger.info(f"Context threshold breached for {agent_id}. Compressing conversation...")
            if len(ctx["messages"]) > 2:
                # Keep first message and last message
                ctx["messages"] = [ctx["messages"][0], ctx["messages"][-1]]
            else:
                ctx["messages"] = [{"role": "system", "content": "Compressed context placeholder"}]
            ctx["tokens_used"] = sum(len(m.get("content", "")) for m in ctx["messages"]) // 4
