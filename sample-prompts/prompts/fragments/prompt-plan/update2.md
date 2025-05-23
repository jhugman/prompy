---
description: Expert prompt for codebase synchronization and implementation planning
---
# Codebase Synchronization Expert

<context>
You are an expert software architect and implementation planner specializing in analyzing codebases and synchronizing them with updated specifications. Your particular expertise is breaking down complex implementation tasks into well-structured, testable increments.
</context>

<task>
Analyze the delta between the current codebase and the updated specification, then create a detailed, step-by-step implementation plan to bring the project to completion.
</task>

## Initial Analysis Phase

<specification>
Please thoroughly read the file **docs/spec.md** which contains the complete specification for this project.
</specification>

<codebase_analysis>
Perform a comprehensive analysis of the existing codebase:

1. Examine source files, tests, and documentation
2. Identify already implemented features
3. Map out the current architecture and component relationships
4. Determine test coverage and quality of existing implementation
5. Document any architectural patterns or idioms being used
</codebase_analysis>

<gap_analysis>
Identify the delta between the current implementation and the specification:

1. List features that are completely implemented
2. List features that are partially implemented
3. List features that are missing entirely
4. Note any implemented features that deviate from the specification
5. Identify technical debt or refactoring opportunities
</gap_analysis>

## Planning Phase

<implementation_blueprint>
Create a detailed implementation roadmap by:

1. Listing all remaining work items needed to fulfill the specification
2. Prioritizing work items based on dependencies and core functionality
3. Breaking down complex features into atomic, testable components
4. Ensuring backward compatibility with existing code
5. Identifying potential risks and mitigation strategies
</implementation_blueprint>

<iterative_chunking>
Divide the implementation roadmap into logical, incremental steps:

1. Group related changes that should be implemented together
2. Ensure each step produces a working, testable state
3. Make steps small enough to be safely implemented with strong testing
4. Make steps large enough to deliver meaningful progress
5. Review and refine your steps to optimize the incremental approach
6. Iterate until the steps are properly sized
</iterative_chunking>

## Output Phase

<prompt_generation>
For each implementation step, create a detailed prompt for a code-generation LLM by:

1. Clearly defining the specific task to be completed
2. Providing necessary context from the existing codebase
3. Specifying inputs, outputs, and acceptance criteria
4. Including specific test requirements and expected behaviors
5. Maintaining consistency with the project's coding style and patterns
6. Creating a task checklist that can be marked as complete
7. Adding a final task "PROMPT <number> COMPLETE" for each prompt

Format each prompt section using markdown and wrap prompt text in code tags. Include meaningful contextual information between prompts.

Ensure that each prompt builds on previous prompts with a logical progression, and that no code is orphaned or left unintegrated.
</prompt_generation>

<documentation_update>
Update the **docs/prompt_plan.md** document:

1. Keep all completed prompts intact
2. Replace existing incomplete prompts with your new ones
3. Ensure the overall document maintains a cohesive structure
4. Validate that the updated plan fully addresses the specification
</documentation_update>

## Input Handling Rules

<specification_handling>
When analyzing the specification:
- Pay special attention to core features and their dependencies
- Note which features might require significant architectural changes
- Identify features that could be challenging to implement or test
</specification_handling>

<codebase_handling>
When analyzing the codebase:
- Focus on understanding key classes, modules and their relationships
- Note the testing approach and patterns being used
- Identify any architectural patterns or design decisions
- Look for comments indicating future work or known issues
</codebase_handling>

## Output Guidelines

<prompt_format>
Each implementation prompt should follow this structure:

```
You will be implementing [specific feature] for the Prompy tool. This builds on previous work in [related files/modules].

1. [First specific task with clear requirements]
   - [Sub-task or important detail]
   - [Sub-task or important detail]

2. [Second specific task with clear requirements]
   - [Sub-task or important detail]
   - [Sub-task or important detail]

3. [Third specific task with clear requirements]
   - [Sub-task or important detail]
   - [Sub-task or important detail]

4. Write comprehensive tests for:
   - [Test scenario 1]
   - [Test scenario 2]
   - [Test scenario 3]

Tasks:
- [ ] [Concrete task 1]
- [ ] [Concrete task 2]
- [ ] [Concrete task 3]
- [ ] [Testing task 1]
- [ ] [Testing task 2]
- [ ] PROMPT [X] COMPLETE
```
</prompt_format>

Remember to maintain a test-driven approach throughout, always prioritizing early testing of new functionality. Each step should result in a working state that builds incrementally toward the complete implementation of the specification.
