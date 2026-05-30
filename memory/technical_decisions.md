---
tags:
  - aios/memory
  - aios/category/decisions
---
# Technical Decisions Log (Shared Memory)

## Architectural & Engineering Decisions
- *To be updated dynamically by the CTO and Architects.*\n
### Decision: stage_triage_bug_run
- **Stage**: triage_bug
- **Agent**: qa_engineer
- **Outputs**: triaged_bug

### Decision: stage_debug_code_run
- **Stage**: debug_code
- **Agent**: fullstack_engineer
- **Outputs**: bug_fix_patch

### Decision: stage_validation_run
- **Stage**: validation
- **Agent**: qa_engineer
- **Outputs**: test_verdict

### Decision: stage_define_skill_run
- **Stage**: define_skill
- **Agent**: skill_creator
- **Outputs**: skills/new_skill.md

### Decision: stage_review_skill_run
- **Stage**: review_skill
- **Agent**: prompt_engineer
- **Outputs**: skills/reviewed_skill.md

### Decision: stage_define_skill_run
- **Stage**: define_skill
- **Agent**: skill_creator
- **Outputs**: skills/new_skill.md

### Decision: stage_review_skill_run
- **Stage**: review_skill
- **Agent**: prompt_engineer
- **Outputs**: skills/reviewed_skill.md

### Decision: stage_define_requirements_run
- **Stage**: define_requirements
- **Agent**: product_owner
- **Outputs**: dsp_requirements.md

### Decision: stage_design_dsp_filter_run
- **Stage**: design_dsp_filter
- **Agent**: dsp_engineer
- **Outputs**: dsp_filter_design.md

### Decision: stage_document_filter_api_run
- **Stage**: document_filter_api
- **Agent**: technical_writer
- **Outputs**: dsp_api_documentation.md
