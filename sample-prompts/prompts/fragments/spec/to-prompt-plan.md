---

---

Read the file **docs/spec.md** which is the specification for this project.

Read the **docs/implementation_sketch.py** which gives a positive guide on the most functional pieces of this project.

Draft a detailed, step-by-step blueprint for building this project. Then, once you have a solid plan, break it down into small, iterative chunks that build on each other. Look at these chunks and then go another round to break it into small steps. Review the results and make sure that the steps are small enough to be implemented safely with strong testing, but big enough to move the project forward. Iterate until you feel that the steps are right sized for this project.

From here you should have the foundation to provide a series of prompts for a code-generation LLM that will implement each step in a test-driven manner.

Prioritize best practices, clean architecture, incremental progress, and early testing, ensuring no big jumps in complexity at any stage. There should be steps to refactor to cleaner and less repetitive code in each section.

Make sure that each prompt builds on the previous prompts, and ends with wiring things together. There should be no hanging or orphaned code that isn't integrated into a previous step.

Make sure and separate each prompt section. Use markdown. Each prompt should be tagged as text using code tags. The goal is to output prompts, but context, etc is important as well.

For each prompt, also show a task list which can be checked off as it is completed. There should also be a final task for `PROMPT <number> COMPLETE`.
