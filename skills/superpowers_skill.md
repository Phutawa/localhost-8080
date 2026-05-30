# Superpowers Skill Framework

## Purpose
Forces the agent to work like a Senior Software Engineer instead of a Junior Developer. It guarantees structured planning, sandbox development (isolation), Test-Driven Development (TDD), and a two-round self-review verification process before submitting any deliverables.

## Core Behavioral Flow

### Step 1: Implementation Planning
Before writing any code or modifying files, you MUST generate and present a detailed step-by-step implementation plan. 
- Break down the task into smaller sub-tasks.
- Identify potential edge cases, architectural patterns, and dependencies.
- Outline the files that will be created or modified.

### Step 2: Isolated Sandbox Development
- Ensure your changes are localized and do not interfere with unrelated services or configurations.
- Use clean, modular interfaces to integrate with existing code.

### Step 3: Test-Driven Development (TDD)
- Define validation criteria and write unit tests or automated test scripts *before* writing the final implementation.
- Tests should cover typical success scenarios, invalid inputs, sudden drops/transients, and empty boundaries.

### Step 4: Two-Round Self-Review
Before finalizing and outputting the work, perform two distinct self-review cycles:
- **Round 1 (Specification Alignment):** Verify that every single requirement in the prompt and specification is fully satisfied. Ensure no features or constraints were missed.
- **Round 2 (Code Quality & Correctness):** Review the code for styling, robustness (NaN protection, division guards, resource leaks), optimization (garbage collection, memory footprint), and security.
