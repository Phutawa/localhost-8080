# -*- coding: utf-8 -*-
"""
AIOS Command Line Interface (CLI) Runner.
Allows running multi-agent workflows from any directory using dynamic path resolution.
"""
import os
import sys
import argparse
import yaml
import logging

from runtime.agent_loader import AgentLoader
from runtime.context_manager import ContextManager
from runtime.memory_manager import MemoryManager
from runtime.task_router import TaskRouter
from runtime.execution_engine import ExecutionEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("AIOS")

def main():
    # Resolve package root and default paths relative to this file
    package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_agents_dir = os.path.join(package_root, "agents")
    default_workflows_dir = os.path.join(package_root, "workflows")

    parser = argparse.ArgumentParser(description="AI Agentic Operating System (AIOS) CLI Runner")
    parser.add_argument(
        "-w", "--workflow",
        required=True,
        help="Path to the workflow YAML file (e.g. bug_fix_pipeline.yaml)"
    )
    parser.add_argument(
        "-s", "--workspace",
        default=".",
        help="Path to target workspace directory where outputs are saved (default: current directory)"
    )
    parser.add_argument(
        "--agents-dir",
        default=default_agents_dir,
        help=f"Path to agents profile directory (default: {default_agents_dir})"
    )
    parser.add_argument(
        "--memory-dir",
        default=None,
        help="Path to shared memory directory (default: <workspace>/memory)"
    )

    args = parser.parse_args()

    workspace_dir = os.path.abspath(args.workspace)
    agents_dir = os.path.abspath(args.agents_dir)
    
    # Resolve memory directory
    if args.memory_dir:
        memory_dir = os.path.abspath(args.memory_dir)
    else:
        memory_dir = os.path.join(workspace_dir, "memory")

    # Locate workflow file (check local workspace, then package defaults)
    workflow_path = args.workflow
    if not os.path.exists(workflow_path):
        fallback_path = os.path.join(default_workflows_dir, workflow_path)
        if os.path.exists(fallback_path):
            workflow_path = fallback_path
        else:
            logger.error(f"Workflow file '{args.workflow}' not found.")
            sys.exit(1)

    logger.info("Initializing AIOS Runtime Engine...")
    logger.info(f"  Workflow: {workflow_path}")
    logger.info(f"  Workspace: {workspace_dir}")
    logger.info(f"  Agents Dir: {agents_dir}")
    logger.info(f"  Memory Dir: {memory_dir}")

    # Load workflow YAML
    try:
        with open(workflow_path, "r", encoding="utf-8") as f:
            workflow_data = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to parse workflow YAML file: {e}")
        sys.exit(1)

    pipeline_name = workflow_data.get("name", "unnamed_pipeline")
    stages = workflow_data.get("pipeline", [])

    # Ensure workspace structure exists
    os.makedirs(workspace_dir, exist_ok=True)
    os.makedirs(memory_dir, exist_ok=True)
    os.makedirs(os.path.join(workspace_dir, "artifacts"), exist_ok=True)

    # Initialize modules
    agent_loader = AgentLoader(agents_dir=agents_dir)
    context_manager = ContextManager()
    memory_manager = MemoryManager(memory_dir=memory_dir)
    task_router = TaskRouter()
    execution_engine = ExecutionEngine()

    # Process pipeline stages
    for idx, stage in enumerate(stages):
        stage_name = stage.get("stage", f"stage_{idx}")
        agent_role = stage.get("agent")
        inputs = stage.get("inputs", [])
        outputs = stage.get("outputs", [])

        print(f"\n==========================================")
        print(f"🚩 Stage {idx + 1}: {stage_name.upper()} ({agent_role})")
        print(f"==========================================")

        # 1. Route task to appropriate layer
        layer = task_router.route_task(agent_role)
        if layer == "engineering" and stage_name:
            layer = task_router.route_task(stage_name)

        # 2. Load agent profile
        try:
            profile = agent_loader.load_agent_profile(layer, agent_role)
            logger.info(f"Loaded Agent Profile: '{profile.get('name')}' from layer directory '{layer}'")
        except FileNotFoundError:
            # Fallback search across all layer folders
            found = False
            for test_layer in ["executive", "architecture", "design", "engineering", "infrastructure", "validation", "ai_systems"]:
                try:
                    profile = agent_loader.load_agent_profile(test_layer, agent_role)
                    layer = test_layer
                    logger.info(f"Loaded Agent Profile (fallback): '{profile.get('name')}' from layer directory '{layer}'")
                    found = True
                    break
                except FileNotFoundError:
                    continue
            if not found:
                logger.error(f"Could not load agent profile for '{agent_role}' in any layer directory under '{agents_dir}'")
                continue

        # 3. Initialize Context
        context_manager.init_context(agent_role)

        # 4. Check Inputs
        for inp in inputs:
            # Find input in workspace root or memory folder
            inp_path = os.path.join(workspace_dir, inp)
            if not os.path.exists(inp_path):
                inp_path = os.path.join(memory_dir, inp)
            
            if os.path.exists(inp_path):
                logger.info(f"Agent '{agent_role}' successfully loaded input: {inp}")
            else:
                logger.warning(f"Agent '{agent_role}' input dependency '{inp}' not found in workspace.")

        # 5. Execute Task
        # Retrieve agent profile raw content for system prompt setup
        agent_system_context = profile.get("raw_content", f"You are {agent_role}, a specialized AI Agent inside the AIOS platform.")
        
        task_payload = {
            "Task": f"Run stage {stage_name}",
            "Assigned_Agent": agent_role,
            "Agent_Context": agent_system_context,
            "Inputs": inputs,
            "Outputs": outputs
        }
        execution_engine.queue_task(task_payload)
        execution_engine.run()

        # 6. Write Outputs to Workspace
        # Retrieve generated result from the execution engine for this task
        latest_task = execution_engine.completed_tasks[-1] if execution_engine.completed_tasks else {}
        llm_result = latest_task.get("Result", "No output generated.")

        for out in outputs:
            out_path = os.path.join(workspace_dir, out)
            # Ensure folder structure for output exists (e.g. artifacts/)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            
            with open(out_path, "w", encoding="utf-8") as f:
                if llm_result.startswith("[Simulation Fallback]") or llm_result.startswith("[Error Fallback]"):
                    f.write(f"# Generated Artifact: {os.path.basename(out)}\n\n")
                    f.write(f"Generated by: AI Agent '{agent_role}' ({layer} layer)\n")
                    f.write(f"Pipeline Stage: {stage_name}\n")
                    f.write(f"Workspace: {workspace_dir}\n\n")
                    f.write(f"Details:\n{llm_result}\n")
                else:
                    # Write real generated output content directly
                    f.write(llm_result)
            
            logger.info(f"Saved output artifact to: {out_path}")

        # 7. Persist Decision Log
        memory_manager.persist_decision(
            decision_id=f"stage_{stage_name}_run",
            decision_data={
                "Stage": stage_name,
                "Agent": agent_role,
                "Outputs": ", ".join(outputs)
            }
        )

    print(f"\n🚀 AIOS Workflow '{pipeline_name}' completed successfully!")
    print(f"All generated files have been saved to workspace: {workspace_dir}\n")

if __name__ == "__main__":
    main()
