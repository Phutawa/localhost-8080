# -*- coding: utf-8 -*-
"""
Execution Engine Module.
Coordinates agent workflows, parallel execution, and task queue processing.
"""

import logging
from queue import Queue
import concurrent.futures

from runtime.llm_provider import LLMProvider
from runtime.retry_handler import RetryHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ExecutionEngine")


class ExecutionEngine:

    def __init__(self):
        self.task_queue = Queue()
        self.completed_tasks = []
        self.retry_handler = RetryHandler(max_retries=3)

    def queue_task(self, task: dict) -> None:
        """
        Enqueues task to the execution pipeline.
        """
        logger.info(f"Enqueuing task: {task.get('Task')}")
        self.task_queue.put(task)

    def run(self, context_manager=None, event_bus=None) -> None:
        """
        Processes tasks in the execution queue.
        Supports optional ContextManager and EventBus integration.
        """
        logger.info("Starting execution engine...")
        tasks = []
        while not self.task_queue.empty():
            tasks.append(self.task_queue.get())

        if not tasks:
            return

        # Execute tasks in parallel using a ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(tasks), 4)) as executor:
            futures = {
                executor.submit(self._execute_single_task, task, context_manager, event_bus): task
                for task in tasks
            }
            for future in concurrent.futures.as_completed(futures):
                task = futures[future]
                try:
                    future.result()
                except Exception as exc:
                    logger.error(f"Task '{task.get('Task')}' generated an exception: {exc}")

    def _execute_single_task(self, task: dict, context_manager, event_bus) -> None:
        """
        Executes a single task, injecting context/input, wrapping with retries,
        updating context managers and broadcasting states.
        """
        task_desc = task.get("Task", "Execute task requirements.")
        agent_name = task.get("Assigned_Agent", "Specialist Agent")
        
        # 1. Restore agent profile context
        system_prompt = task.get(
            "Agent_Context",
            f"You are {agent_name}, a specialized AI agent. Complete tasks professionally and clearly."
        )

        # 2. Ingest input file content
        input_data = task.get("Input_Data", {})
        input_text = ""
        if input_data:
            input_text = "\nHere is the content of the input files for this task:\n"
            for filename, content in input_data.items():
                input_text += f"--- START OF FILE: {filename} ---\n{content}\n--- END OF FILE: {filename} ---\n\n"

        user_prompt = f"""
Assigned Task:
{task_desc}
{input_text}
Execute this task and provide the output/result.
"""

        logger.info(f"Running task: {task_desc} assigned to {agent_name}")
        
        # 3. Publish task started event
        if event_bus:
            event_bus.publish("task_started", {"task": task_desc, "agent": agent_name})

        # 4. Generate Response using the 4-stage RetryHandler
        try:
            result = self.retry_handler.execute_with_retry(
                LLMProvider.generate,
                prompt=user_prompt,
                system_prompt=system_prompt
            )
        except Exception as e:
            logger.error(f"Task execution failed permanently: {e}")
            result = f"[Error Fallback] Execution failed permanently: {e}"

        task["Result"] = result
        task["Status"] = "Completed"
        self.completed_tasks.append(task)

        # 5. Update and prune context history in ContextManager
        if context_manager and agent_name in context_manager.active_contexts:
            ctx = context_manager.active_contexts[agent_name]
            ctx["messages"].append({"role": "user", "content": user_prompt})
            ctx["messages"].append({"role": "model", "content": result})
            
            # Simple token estimation
            estimated_tokens = (len(user_prompt) + len(system_prompt) + len(result)) // 4
            ctx["tokens_used"] += estimated_tokens
            context_manager.prune_context(agent_name)

        # 6. Publish task completed event
        if event_bus:
            event_bus.publish("task_completed", {"task": task_desc, "agent": agent_name, "result": result})

        logger.info(f"Task completed with result: {result[:100]}...")
