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
from runtime.event_bus import EventBus

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
        required=False,
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
    parser.add_argument(
        "--review",
        action="store_true",
        help="Run local code review on files"
    )
    parser.add_argument(
        "--ultra-review",
        action="store_true",
        help="Run parallel multi-agent ultra-review on files"
    )
    parser.add_argument(
        "--files",
        nargs="+",
        help="List of files to review"
    )

    args = parser.parse_args()

    workspace_dir = os.path.abspath(args.workspace)
    agents_dir = os.path.abspath(args.agents_dir)
    
    # Resolve memory directory
    if args.memory_dir:
        memory_dir = os.path.abspath(args.memory_dir)
    else:
        memory_dir = os.path.join(workspace_dir, "memory")

    # Handle Code Review requests directly
    if args.review or args.ultra_review:
        if not args.files:
            logger.error("Please specify files to review using the --files argument.")
            sys.exit(1)
        
        from runtime.review_engine import ReviewEngine
        from runtime.claude_mem import ClaudeMem
        
        review_engine = ReviewEngine(agents_dir=agents_dir)
        mem = ClaudeMem(memory_dir=memory_dir, workspace_dir=workspace_dir)
        
        if args.review:
            report = review_engine.run_local_review(workspace_dir, args.files)
            review_type = "local-review"
        else:
            report = review_engine.run_ultra_review(workspace_dir, args.files)
            review_type = "ultra-review"
            
        print("\n==========================================")
        print("📝 CODE REVIEW REPORT")
        print("==========================================")
        print(report)
        print("==========================================\n")
        
        # Log to memories
        mem.log_event("review", f"Ran {review_type} on files: {', '.join(args.files)}")
        sys.exit(0)

    # Locate workflow file (check local workspace, then package defaults)
    workflow_path = args.workflow
    if not workflow_path:
        logger.error("No workflow specified. Specify -w to run a workflow, or --review/--ultra-review with --files to run reviews.")
        sys.exit(1)

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
    event_bus = EventBus()

    # Claude Mem initialization and session logging
    from runtime.claude_mem import ClaudeMem
    mem = ClaudeMem(memory_dir=memory_dir, workspace_dir=workspace_dir)
    mem.log_event("session_start", f"Starting workflow engine for pipeline '{pipeline_name}'")
    
    # Retrieve and log relevant history memories
    history_memories = mem.retrieve_relevant_memories(pipeline_name)
    if history_memories:
        logger.info("Found relevant historical memories to inject.")

    # Register EventBus logging listeners
    def on_task_started(data):
        logger.info(f"[EventBus Alert] Agent '{data['agent']}' started executing task: '{data['task']}'")

    def on_task_completed(data):
        logger.info(f"[EventBus Alert] Agent '{data['agent']}' successfully completed task.")

    event_bus.subscribe("task_started", on_task_started)
    event_bus.subscribe("task_completed", on_task_completed)

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

        # 4. Check Inputs and Load Content
        input_data = {}
        for inp in inputs:
            # Find input in workspace root or memory folder
            inp_path = os.path.join(workspace_dir, inp)
            if not os.path.exists(inp_path):
                inp_path = os.path.join(memory_dir, inp)
            
            if os.path.exists(inp_path):
                logger.info(f"Agent '{agent_role}' successfully loaded input: {inp}")
                try:
                    with open(inp_path, "r", encoding="utf-8") as f:
                        input_data[inp] = f.read()
                except Exception as e:
                    logger.warning(f"Failed to read input file '{inp}': {e}")
            else:
                logger.warning(f"Agent '{agent_role}' input dependency '{inp}' not found in workspace.")

        # 5. Execute Task
        # Retrieve agent profile raw content for system prompt setup
        agent_system_context = profile.get("raw_content", f"You are {agent_role}, a specialized AI Agent inside the AIOS platform.")
        
        mem.log_event("task_start", f"Running stage '{stage_name}' assigned to agent '{agent_role}'")
        task_payload = {
            "Task": f"Run stage {stage_name}",
            "Assigned_Agent": agent_role,
            "Agent_Context": agent_system_context,
            "Inputs": inputs,
            "Input_Data": input_data,
            "Outputs": outputs
        }
        execution_engine.queue_task(task_payload)
        execution_engine.run(context_manager=context_manager, event_bus=event_bus)

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
            mem.log_event("file_write", f"Saved output artifact to {out}", file_path=out)

        # 7. Persist Decision Log
        decision_desc = f"Completed stage {stage_name} using agent {agent_role}"
        mem.log_event("decision", decision_desc)
        memory_manager.persist_decision(
            decision_id=f"stage_{stage_name}_run",
            decision_data={
                "Stage": stage_name,
                "Agent": agent_role,
                "Outputs": ", ".join(outputs)
            }
        )

    mem.log_event("session_end", f"Successfully completed workflow '{pipeline_name}'")
    print(f"\n🚀 AIOS Workflow '{pipeline_name}' completed successfully!")
    print(f"All generated files have been saved to workspace: {workspace_dir}\n")

if __name__ == "__main__":
    main()
