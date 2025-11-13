# Spec-Kit Implementation Strategy for ELAAOMS

## Overview

This document provides a **step-by-step strategy** for implementing [GitHub's spec-kit](https://github.com/github/spec-kit) in the ELAAOMS project. The goal is to create structured specifications that help AI coding assistants (like Claude) stay focused and maintain context without "going crazy."

## Why Spec-Kit?

Spec-kit implements **spec-driven development**, which means:
- ✅ Define "what" and "why" before "how"
- ✅ Create executable specifications instead of vague requirements
- ✅ Keep AI agents focused with clear boundaries
- ✅ Enable consistent quality across implementations
- ✅ Prevent scope creep and context drift

## Current Project Status

- **Project Type**: Full-stack AI integration platform (FastAPI backend + React/HTML frontends)
- **Documentation**: 8,919 lines across 15 files (comprehensive but has alignment issues)
- **Known Issue**: 45 code-documentation misalignments identified in `CODE_DOCUMENTATION_ALIGNMENT.md`
- **AI Challenge**: Complex multi-component architecture can cause context drift

---

## Implementation Phases

### Phase 1: Foundation Setup (Day 1)
### Phase 2: Create Core Specifications (Days 2-3)
### Phase 3: Integration & Refinement (Day 4)
### Phase 4: Team Adoption (Day 5+)

---

# Phase 1: Foundation Setup

## Step 1.1: Install Spec-Kit CLI

**What to do:**
```bash
# Install spec-kit CLI using uv (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or install persistently
pip install spec-kit
```

**Expected outcome:** CLI available for running spec-kit commands

---

## Step 1.2: Initialize Spec-Kit Structure

**What to do:** Create the spec-kit directory structure in your project.

**Prompt to use with Claude:**
```
Create a spec-kit directory structure in this project with the following layout:

.claude/
├── commands/
│   ├── speckit.constitution.md
│   ├── speckit.specify.md
│   ├── speckit.plan.md
│   ├── speckit.tasks.md
│   └── speckit.implement.md
└── specs/
    ├── constitution.md
    ├── features/
    ├── plans/
    └── tasks/

Keep it simple. Just create the directories and placeholder files.
Do NOT add any content yet - we'll populate these in the next steps.
```

**Why this works:**
- Clear scope: "create structure only"
- Explicit instruction: "do NOT add content"
- Prevents AI from overengineering

**Expected outcome:** Directory structure created, ready for content

---

## Step 1.3: Create Project Constitution

**What to do:** Define your project's governance principles.

**Prompt to use with Claude:**
```
I need to create a constitution.md file in .claude/specs/ that defines
the core principles for ELAAOMS development. Base this on our existing
documentation in docs/CONTRIBUTING.md and docs/SECURITY.md.

The constitution should include ONLY these sections:
1. Project Purpose (2-3 sentences from README.md)
2. Core Principles (extract from CONTRIBUTING.md)
3. Development Standards (coding patterns we follow)
4. Security Requirements (reference SECURITY.md)
5. Documentation Rules (must maintain code-docs alignment)

Keep it to 150 lines maximum. Be concise. Use bullet points.

Do NOT create examples, tutorials, or implementation details.
Focus ONLY on governance principles.
```

**Why this works:**
- Bounded scope: "150 lines maximum"
- Clear source references: "from README.md", "extract from CONTRIBUTING.md"
- Explicit exclusions: "do NOT create examples"
- Specific sections listed

**Expected outcome:** `.claude/specs/constitution.md` with clear project principles

---

## Step 1.4: Create Slash Commands

**What to do:** Set up Claude Code slash commands for spec-kit workflow.

**Prompt to use with Claude:**
```
Create 5 slash command files in .claude/commands/ for the spec-kit workflow.
Use this exact content for each file:

File: .claude/commands/speckit.constitution.md
Content:
---
description: Review and enforce project constitution
---
You are in CONSTITUTION MODE. Your job is to:
1. Read .claude/specs/constitution.md
2. Verify the current task aligns with project principles
3. Flag any violations before proceeding
4. Keep responses under 200 words

Do NOT implement anything. Only review and approve/reject.

---

File: .claude/commands/speckit.specify.md
Content:
---
description: Write feature specifications
---
You are in SPECIFICATION MODE. Your job is to:
1. Define WHAT the feature does (not HOW)
2. List user-facing behavior
3. Define success criteria
4. Identify edge cases
5. Save spec to .claude/specs/features/[feature-name].md

Use this template:
# Feature: [Name]
## Purpose: [1-2 sentences]
## User Stories: [3-5 bullet points]
## Acceptance Criteria: [Numbered list]
## Edge Cases: [What could go wrong?]
## Dependencies: [What existing code does this touch?]

Do NOT write implementation details or code.

---

File: .claude/commands/speckit.plan.md
Content:
---
description: Create technical implementation plan
---
You are in PLANNING MODE. Your job is to:
1. Read the spec from .claude/specs/features/
2. Create a technical plan (HOW to build it)
3. List files to modify
4. Define architecture changes
5. Estimate complexity
6. Save to .claude/specs/plans/[feature-name]-plan.md

Use this template:
# Implementation Plan: [Feature Name]
## Spec Reference: [Link to feature spec]
## Files to Modify: [Numbered list with file paths]
## New Files Needed: [If any]
## Architecture Changes: [Describe impacts]
## Testing Strategy: [What tests to write]
## Risks: [What could go wrong?]
## Estimated Effort: [S/M/L]

Do NOT write code yet. Planning only.

---

File: .claude/commands/speckit.tasks.md
Content:
---
description: Break plan into actionable tasks
---
You are in TASK BREAKDOWN MODE. Your job is to:
1. Read the plan from .claude/specs/plans/
2. Create a numbered task list
3. Each task should take 15-30 minutes
4. Order tasks by dependency
5. Save to .claude/specs/tasks/[feature-name]-tasks.md

Use this template:
# Tasks: [Feature Name]
## Plan Reference: [Link to plan]

### Task 1: [Concise name]
- **File**: [path/to/file.py]
- **Action**: [What to do in 1 sentence]
- **Validation**: [How to verify it worked]

[Repeat for each task]

Do NOT implement. Only create the task list.

---

File: .claude/commands/speckit.implement.md
Content:
---
description: Execute implementation from tasks
---
You are in IMPLEMENTATION MODE. Your job is to:
1. Read tasks from .claude/specs/tasks/[feature-name]-tasks.md
2. Execute each task sequentially
3. Use TodoWrite tool to track progress
4. Run tests after each task
5. Stop if anything fails and report

Rules:
- ONE task at a time
- Mark task as in_progress before starting
- Mark completed only after tests pass
- If a task fails, STOP and ask for guidance
- Do NOT skip ahead or combine tasks

Begin with: "Starting implementation of [feature]. Loading tasks..."

---

Copy these EXACTLY as written. Do NOT modify the content.
Create all 5 files.
```

**Why this works:**
- Provides exact content (no interpretation needed)
- Each command has a clear mode/role
- Explicit boundaries for each phase
- "Do NOT" statements prevent scope creep

**Expected outcome:** 5 slash commands ready to use in Claude Code

---

# Phase 2: Create Core Specifications

## Step 2.1: Document Existing Features

**What to do:** Create specifications for existing features to establish patterns.

**Prompt to use with Claude (example for memory system):**
```
I want to create a specification for our existing memory extraction feature.
Use the /speckit.specify command.

Feature to document: Post-call memory extraction webhook
Source documentation: docs/MEMORY_SYSTEM_GUIDE.md (lines 200-350)
Source code: backend/app/routes.py (the /webhook/post-call endpoint)

Follow the specification template exactly. Focus on WHAT it does, not HOW.
Keep it under 100 lines.

Do NOT rewrite the code or suggest improvements yet.
```

**Why this works:**
- Uses the slash command workflow
- Provides specific line numbers (bounded context)
- Explicit length limit
- Clear instruction: document, don't improve

**Expected outcome:** `.claude/specs/features/memory-extraction.md` created

---

## Step 2.2: Create Specification for Known Issue

**What to do:** Pick one of the 45 code-documentation misalignments and spec a fix.

**Prompt to use with Claude:**
```
Read docs/CODE_DOCUMENTATION_ALIGNMENT.md and find the highest priority
misalignment issue (look for "Critical" severity).

Use /speckit.specify to create a specification for fixing that issue.

Scope: ONE issue only (pick the first Critical one you find)
Output: .claude/specs/features/fix-[issue-name].md

Do NOT fix the issue yet. Only write the specification.
After creating the spec, tell me which issue you documented.
```

**Why this works:**
- AI picks from existing list (no inventing problems)
- Scoped to ONE issue
- Separates specification from implementation
- Requires AI to report what it chose (transparency)

**Expected outcome:** Spec for fixing one critical documentation issue

---

## Step 2.3: Create Implementation Plan

**What to do:** Plan how to fix the documented issue.

**Prompt to use with Claude:**
```
Use /speckit.plan to create an implementation plan for the specification
you just created: .claude/specs/features/fix-[issue-name].md

Read the spec carefully.
List ALL files that need changes (be exhaustive).
Identify testing requirements.
Note any risks to existing functionality.

Output: .claude/specs/plans/fix-[issue-name]-plan.md

Do NOT implement yet. Planning phase only.
```

**Why this works:**
- Sequential workflow (spec → plan → tasks → implement)
- References previous step's output
- Explicit requirements (files, tests, risks)
- Reinforces boundary: "planning phase only"

**Expected outcome:** Detailed implementation plan

---

## Step 2.4: Break Down Into Tasks

**What to do:** Create actionable task list.

**Prompt to use with Claude:**
```
Use /speckit.tasks to break down the plan into tasks.

Source: .claude/specs/plans/fix-[issue-name]-plan.md
Target: .claude/specs/tasks/fix-[issue-name]-tasks.md

Requirements:
- Each task should be testable independently
- Order by dependency (what must happen first?)
- Estimate: 15-30 minutes per task
- If a task seems longer, split it into subtasks

Do NOT implement. Create the task list only.
After creating tasks, count how many tasks you made and tell me.
```

**Why this works:**
- Clear time boxing (15-30 min per task)
- Forces granularity (splits large tasks)
- Requires counting (validates AI understood)

**Expected outcome:** Task list with 3-8 granular tasks

---

# Phase 3: Integration & Refinement

## Step 3.1: Test the Implementation Workflow

**What to do:** Use /speckit.implement to execute ONE task.

**Prompt to use with Claude:**
```
Use /speckit.implement to execute ONLY the first task from:
.claude/specs/tasks/fix-[issue-name]-tasks.md

Rules:
1. Read the task file
2. Execute Task 1 ONLY
3. Use TodoWrite to track progress
4. Run any relevant tests
5. If it passes, mark task complete and STOP
6. If it fails, report the failure and STOP

Do NOT continue to Task 2. Execute one task only.
```

**Why this works:**
- Incremental execution (prevents runaway AI)
- Explicit stop conditions
- Tests validate each step
- Easy to review progress

**Expected outcome:** First task completed and tested

---

## Step 3.2: Validate Alignment

**What to do:** Verify the change aligns with constitution.

**Prompt to use with Claude:**
```
Use /speckit.constitution to validate the change you just made.

Check:
1. Does it follow our coding standards?
2. Does it maintain documentation alignment?
3. Did it introduce security risks?
4. Does it need documentation updates?

Refer to .claude/specs/constitution.md for principles.

Report: Pass/Fail with reasoning (under 150 words)
```

**Why this works:**
- Built-in quality gate
- References constitution (governance)
- Word limit prevents over-explanation
- Pass/fail decision (clear outcome)

**Expected outcome:** Validation report confirming alignment

---

## Step 3.3: Complete Remaining Tasks

**What to do:** Continue task-by-task implementation.

**Prompt to use with Claude:**
```
Continue /speckit.implement workflow for the remaining tasks in:
.claude/specs/tasks/fix-[issue-name]-tasks.md

Execute tasks 2 through N sequentially.
After EACH task:
- Run tests
- Validate with /speckit.constitution
- Mark complete in TodoWrite
- Wait for my approval before proceeding to next task

If ANY task fails, STOP and report the issue.
Do NOT skip tasks or combine them.
```

**Why this works:**
- Human-in-the-loop after each task (safety net)
- Continuous validation
- Prevents compounding errors
- Maintains focus through repetition

**Expected outcome:** All tasks completed incrementally

---

## Step 3.4: Update Documentation

**What to do:** Ensure docs reflect code changes.

**Prompt to use with Claude:**
```
Now that the implementation is complete, update documentation to match.

Source: The changes you just made to fix [issue-name]
Target docs to update: [Reference the relevant docs/*.md files]

Requirements:
1. Update ONLY the sections affected by your changes
2. Verify code examples still work
3. Update API endpoint docs if needed
4. Add entry to docs/CHANGELOG.md
5. Do NOT rewrite entire documents

Use Edit tool for surgical changes only.
List each file you update.
```

**Why this works:**
- Scoped to affected sections ("ONLY")
- Prevents doc rewrites (surgical changes)
- Requires listing changes (accountability)
- Maintains code-docs alignment

**Expected outcome:** Documentation updated to match code

---

# Phase 4: Team Adoption

## Step 4.1: Create Spec-Kit Usage Guide

**What to do:** Document the workflow for your team.

**Prompt to use with Claude:**
```
Create a usage guide for the spec-kit workflow in:
docs/SPEC_KIT_USAGE_GUIDE.md

Include:
1. Quick start (3 steps to use spec-kit)
2. When to use each slash command
3. Example workflow (end-to-end)
4. Common pitfalls and how to avoid them
5. Integration with existing PR process

Keep it under 300 lines. Use examples from our recent implementation.
Target audience: developers familiar with Claude Code.

Do NOT duplicate content from CONTRIBUTING.md.
Cross-reference existing docs where appropriate.
```

**Expected outcome:** Team-friendly usage guide

---

## Step 4.2: Update Contributing Guidelines

**What to do:** Integrate spec-kit into development process.

**Prompt to use with Claude:**
```
Update docs/CONTRIBUTING.md to include spec-kit workflow.

Add a new section: "## Using Spec-Kit for Feature Development"

Content should:
- Reference docs/SPEC_KIT_USAGE_GUIDE.md
- Show when spec-kit is required (new features, complex bugs)
- Show when it's optional (minor fixes, typos)
- Add spec-kit checklist to PR requirements

Make surgical edits only. Do NOT rewrite the entire document.
Show me the section you're adding before making changes.
```

**Why this works:**
- Review before execution ("show me first")
- Surgical edits (bounded scope)
- Clear applicability rules (when to use)

**Expected outcome:** Updated contributing guidelines

---

## Step 4.3: Update PR Template

**What to do:** Add spec-kit checklist to PR template.

**Prompt to use with Claude:**
```
Update .github/PULL_REQUEST_TEMPLATE.md to include spec-kit checks.

Add under the ## Checklist section:

### Spec-Kit (if applicable)
- [ ] Feature specification created (.claude/specs/features/)
- [ ] Implementation plan documented (.claude/specs/plans/)
- [ ] Tasks breakdown completed (.claude/specs/tasks/)
- [ ] Constitution validation passed
- [ ] Documentation updated to match implementation

Add "(if applicable)" note explaining when this is required.

Use Edit tool. Show me the change before applying it.
```

**Expected outcome:** PR template includes spec-kit workflow

---

# Maintenance & Best Practices

## Using Spec-Kit in Daily Development

### For New Features

**Step-by-step prompt sequence:**

1. **Specification Phase:**
   ```
   /speckit.specify
   Feature: [Your feature name]
   Reference: [Relevant existing docs]
   Keep under 100 lines. Focus on user behavior, not implementation.
   ```

2. **Planning Phase:**
   ```
   /speckit.plan
   Spec: .claude/specs/features/[feature-name].md
   List all file changes. Identify risks. Estimate effort.
   ```

3. **Task Breakdown:**
   ```
   /speckit.tasks
   Plan: .claude/specs/plans/[feature-name]-plan.md
   15-30 min tasks. Order by dependency.
   ```

4. **Implementation:**
   ```
   /speckit.implement
   Tasks: .claude/specs/tasks/[feature-name]-tasks.md
   One task at a time. Stop on failures. Use TodoWrite.
   ```

5. **Validation:**
   ```
   /speckit.constitution
   Validate the completed implementation against our principles.
   ```

### For Bug Fixes

**When to use spec-kit:**
- ✅ Bug affects multiple components
- ✅ Root cause unclear
- ✅ Fix requires architecture changes
- ❌ Simple typo or one-line fix (overkill)

**Prompt for complex bugs:**
```
/speckit.specify
Document the bug: Current behavior vs Expected behavior
List affected components
Define success criteria for the fix
Keep under 75 lines
```

### For Refactoring

**Prompt template:**
```
/speckit.specify
Refactoring target: [Component/module name]
Current issues: [Performance/maintainability/etc]
Desired outcome: [What should improve?]
Constraints: [What must NOT break?]
Reference: [Existing architecture docs]
```

---

## Preventing "AI Going Crazy" - Key Principles

### ✅ DO: Keep AI Focused

1. **Use Bounded Scopes**
   ```
   ❌ BAD: "Improve the authentication system"
   ✅ GOOD: "Add rate limiting to the /webhook/post-call endpoint.
            Modify ONLY backend/app/routes.py lines 250-275.
            Use existing RateLimiter class from auth.py."
   ```

2. **Reference Existing Patterns**
   ```
   ❌ BAD: "Create a new API endpoint"
   ✅ GOOD: "Create a new API endpoint following the pattern in
            routes.py lines 100-150 (the /webhook/client-data endpoint).
            Use the same auth, logging, and error handling approach."
   ```

3. **Use Line Numbers**
   ```
   ❌ BAD: "Update the memory extraction function"
   ✅ GOOD: "Update backend/app/background_jobs.py lines 45-67
            (extract_memories_from_transcript function)"
   ```

4. **Set Length Limits**
   ```
   ❌ BAD: "Write comprehensive documentation"
   ✅ GOOD: "Write a usage guide under 200 lines with 3 examples"
   ```

5. **One Task at a Time**
   ```
   ❌ BAD: "Fix all the critical issues in CODE_DOCUMENTATION_ALIGNMENT.md"
   ✅ GOOD: "Fix issue #1 only (audio format mismatch).
            We'll handle others separately."
   ```

### ❌ DON'T: Let AI Lose Focus

1. **Avoid Vague Requests**
   - "Make it better" → Specify what "better" means
   - "Add features" → List exact features
   - "Optimize" → Define metrics (latency? memory? readability?)

2. **Don't Skip Validation Steps**
   - Always run tests after changes
   - Always use /speckit.constitution to validate
   - Always update docs immediately

3. **Don't Batch Too Many Changes**
   - Max 3-5 related changes per PR
   - Split large features into multiple specs

4. **Don't Let AI Invent Requirements**
   - Provide source documents
   - Reference existing code patterns
   - Specify what NOT to change

---

## Troubleshooting

### Issue: AI Creates Overly Detailed Specs

**Solution:**
```
"Stop. The spec is too detailed. Rewrite it in 50 lines or less.
Remove all implementation details. Focus only on user-facing behavior."
```

### Issue: AI Skips Ahead to Implementation

**Solution:**
```
"Stop. We're still in planning phase. Do NOT write code yet.
Finish the plan in .claude/specs/plans/ first.
Focus only on: What files to change and why."
```

### Issue: AI Combines Multiple Tasks

**Solution:**
```
"Stop. You combined Tasks 2 and 3. Undo that change.
Execute Task 2 ONLY. It should take 15-30 minutes.
After Task 2 is complete and tested, stop and wait for my approval."
```

### Issue: AI Rewrites Entire Files

**Solution:**
```
"Stop. You rewrote the entire file. That's too risky.
Use Edit tool to make surgical changes only.
Show me the exact old_string and new_string before applying."
```

### Issue: AI Generates Code Without Tests

**Solution:**
```
"Stop. You didn't write tests. Before marking this task complete:
1. Write a test for the change in tests/
2. Run the test to verify it passes
3. Then mark complete in TodoWrite"
```

---

## Metrics & Success Criteria

### How to Measure Spec-Kit Success

**Track these metrics:**

1. **Code-Documentation Alignment**
   - Current: 2.5/5 stars (45 misalignments)
   - Target: 4.5/5 stars (< 5 misalignments)
   - Measure: Run comparison quarterly

2. **AI Context Drift**
   - Track: How often you need to say "Stop, that's out of scope"
   - Target: < 1 intervention per 10 tasks
   - Measure: Log interventions

3. **Implementation Accuracy**
   - Track: Tests passing on first try after implementation
   - Target: > 80% pass rate
   - Measure: CI/CD test results

4. **Development Velocity**
   - Track: Time from spec to deployed feature
   - Target: Reduce by 25% after 3 months
   - Measure: GitHub metrics (PR open to merge time)

5. **Documentation Freshness**
   - Track: Time between code change and doc update
   - Target: Same PR (0 delay)
   - Measure: PR review checklist

---

## Quick Reference: Prompt Templates

### Template 1: New Feature (Full Workflow)
```
STEP 1: /speckit.specify
Feature: [Name]
Purpose: [2 sentences]
Source: [Reference existing docs]
Keep under 100 lines.

STEP 2: /speckit.plan
Spec: .claude/specs/features/[name].md
List files, risks, tests.

STEP 3: /speckit.tasks
Break into 15-30 min tasks.

STEP 4: /speckit.implement
One task at a time. Use TodoWrite. Stop on failures.

STEP 5: /speckit.constitution
Validate against project principles.
```

### Template 2: Bug Fix (Complex)
```
/speckit.specify
Bug: [Description]
Affected: [Components]
Current behavior: [What happens]
Expected behavior: [What should happen]
Success criteria: [How to verify fix]
Reference: [Relevant docs/code]
Under 75 lines.
```

### Template 3: Documentation Update
```
Update [specific doc file] to match recent changes in [code file].

Changes:
- [List specific changes]

Requirements:
- Use Edit tool (surgical changes only)
- Update ONLY affected sections (lines X-Y)
- Verify code examples still work
- Add changelog entry

Do NOT rewrite entire document.
```

### Template 4: Validation Check
```
/speckit.constitution

Validate [recent change/PR/feature] against:
1. Coding standards (constitution.md section 3)
2. Security requirements (constitution.md section 4)
3. Documentation rules (constitution.md section 5)

Report: Pass/Fail with reasoning (under 150 words)
```

---

## Integration with Existing Workflow

### Current PR Process (from CONTRIBUTING.md)
1. Create feature branch
2. Make changes
3. Write tests
4. Update docs
5. Open PR with template
6. Pass CI checks
7. Code review
8. Merge

### New PR Process (with Spec-Kit)
1. **Create specification** (`/speckit.specify`)
2. **Plan implementation** (`/speckit.plan`)
3. **Break into tasks** (`/speckit.tasks`)
4. Create feature branch
5. **Implement task-by-task** (`/speckit.implement`)
6. Write tests (per task)
7. Update docs (per task)
8. **Validate** (`/speckit.constitution`)
9. Open PR with template (include spec references)
10. Pass CI checks
11. Code review (reviewers read spec first)
12. Merge

**Added time:** ~30-60 minutes for spec/plan/tasks
**Saved time:** Fewer revisions, better context, aligned docs

---

## Conclusion

### What You've Accomplished

After completing this strategy, you'll have:

✅ Spec-kit integrated into project structure
✅ 5 slash commands for structured development workflow
✅ Constitution defining project governance
✅ Example specs/plans/tasks for reference
✅ Team documentation for adoption
✅ PR process updated to include spec-kit
✅ Tools to keep AI focused and prevent scope creep

### Next Steps

1. **Week 1**: Complete Phases 1-3 (foundation, core specs, test implementation)
2. **Week 2**: Complete Phase 4 (team documentation, process updates)
3. **Week 3**: Use spec-kit for next 2-3 features/bugs (build habit)
4. **Month 1 Review**: Measure metrics (alignment score, test pass rate)
5. **Quarter 1**: Refine based on team feedback

### Questions?

Reference these docs:
- **Spec-kit basics**: https://github.com/github/spec-kit
- **Claude Code docs**: https://docs.claude.com/en/docs/claude-code
- **Project contributing**: docs/CONTRIBUTING.md
- **This guide**: docs/SPEC_KIT_IMPLEMENTATION_STRATEGY.md

---

## Appendix: Example Prompts in Action

### Example: Fixing Critical Documentation Issue

**User:** "Fix the audio webhook format mismatch (Critical Issue #1)"

**Step 1 - AI Response:**
```
I'll use the spec-kit workflow to fix this issue.

/speckit.specify
Feature: Fix audio webhook format documentation mismatch
Purpose: Align documentation with actual audio_content_base64 format
Source: docs/CODE_DOCUMENTATION_ALIGNMENT.md (Issue #1)
Reference code: backend/app/routes.py (lines 180-200)

Creating spec in .claude/specs/features/fix-audio-format-docs.md...
```

**Step 2 - User:**
```
Good. Now create the implementation plan.
```

**Step 2 - AI Response:**
```
/speckit.plan
Spec: .claude/specs/features/fix-audio-format-docs.md

Files to modify:
1. docs/MEMORY_SYSTEM_GUIDE.md (lines 275-290)
2. README.md (lines 120-135)
3. backend/app/models.py (docstrings for AudioData model)

Creating plan in .claude/specs/plans/fix-audio-format-docs-plan.md...
```

**Step 3 - User:**
```
Break it into tasks.
```

**Step 3 - AI Response:**
```
/speckit.tasks

Created 3 tasks:
1. Update MEMORY_SYSTEM_GUIDE.md audio format examples (15 min)
2. Update README.md webhook payload examples (15 min)
3. Add docstrings to AudioData model class (20 min)

Saved to .claude/specs/tasks/fix-audio-format-docs-tasks.md
```

**Step 4 - User:**
```
Implement task 1 only.
```

**Step 4 - AI Response:**
```
/speckit.implement
Loading tasks from .claude/specs/tasks/fix-audio-format-docs-tasks.md

[TodoWrite: Task 1 - in_progress]

Updating docs/MEMORY_SYSTEM_GUIDE.md lines 275-290...
[Shows Edit tool usage]

Running validation...
[Tests pass]

[TodoWrite: Task 1 - completed]

Task 1 complete. Ready for Task 2 when you approve.
```

**Step 5 - User:**
```
Validate it with constitution.
```

**Step 5 - AI Response:**
```
/speckit.constitution

Validation Results:
✅ Coding Standards: N/A (documentation only)
✅ Documentation Rules: Aligns code with docs (PRIMARY GOAL)
✅ Security: No security impact
✅ Testing: No code changes, no tests needed

Verdict: PASS - Change aligns with constitution principle #5
(maintain code-documentation alignment)
```

---

*This strategy document is a living guide. Update it as you refine your spec-kit workflow.*

**Version**: 1.0
**Last Updated**: 2025-11-13
**Maintained By**: Development Team
