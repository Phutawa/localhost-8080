# -*- coding: utf-8 -*-
"""
Execution Engine Module.
Coordinates agent workflows, parallel execution, and task queue processing.
"""

import logging
from queue import Queue

from runtime.llm_provider import LLMProvider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ExecutionEngine")


class ExecutionEngine:

    def __init__(self):
        self.task_queue = Queue()
        self.completed_tasks = []

    def queue_task(self, task: dict) -> None:
        """
        Enqueues task to the execution pipeline.
        """
        logger.info(f"Enqueuing task: {task.get('Task')}")
        self.task_queue.put(task)

    def run(self) -> None:
        """
        Processes tasks in the execution queue.
        """

        logger.info("Starting execution engine...")

        while not self.task_queue.empty():

            task = self.task_queue.get()

            logger.info(
                f"Running task: {task.get('Task')} "
                f"assigned to {task.get('Assigned_Agent')}"
            )

            # Build Prompt
            task_desc = task.get(
                "Task",
                "Execute task requirements."
            )

            agent_name = task.get(
                "Assigned_Agent",
                "Specialist Agent"
            )

            system_prompt = f"""
You are {agent_name}, a specialized AI agent.
Complete tasks professionally and clearly.
"""

            user_prompt = f"""
Assigned Task:
{task_desc}

Execute this task and provide the output/result.
"""

            logger.info(
                f"Generating LLM response for {agent_name}..."
            )

            # Generate Response
            result = LLMProvider.generate(
                prompt=user_prompt,
                system_prompt=system_prompt
            )

            task["Result"] = result
            task["Status"] = "Completed"

            self.completed_tasks.append(task)

            logger.info(
                f"Task completed with result: "
                f"{result[:100]}..."
            )
