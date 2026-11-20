# SPEC NAME

*Explain the specs to the AI, add in reference code, details, etc. Feel free to have a conversation with Kiro in the prompt and have Kiro fill out this SPEC. "Let's fill out SPEC.md. I want to build x, start by asking me questions and giving me recommendations. We'll fill out the SPECs before starting a workflow."*

*This project is scaffoled with code, steering documents, and skills to help guide new development using a Spec-Driven Workflow.*

*Kiro already uses the `requirements.md -> design.md -> tasks.md` process for requirements definition.*

*However, Atlantis aims to move pre-planning even further left with `ISSUE.md/SPEC.md/FINDINGS.md -> PLAN.md -> requirements.md -> design.md -> tasks.md` to ask clarifying questions, find gaps, and iterate over decisions for the feature/bug before spending time generating EARS-style requirements.md.*

*Rather than iterating over requirements.md, the user defines what they want to build and uses a `plan-from-issue` or `plan-from-spec` skill to review the code base, past decisions, and what the developer/team is requesting in the SPECS, ISSUE, FINDINGS or other supporting documentation. It then iterates over a PLAN.md, asking questions, identifying gaps, and recommending solutions before locking them in.*

*This pre-planning, iterative approach has given developers the ability to work through how changes will affect the end result and produce a sound requirements.md before it gets expensive to make changes.*

---

Write your specs in this file, such as findings, ideas, features, etc. It doesn't have to be perfect. An ISSUE.md can be used for importing approved and reviewed bugs or feature requests from your GitHub or Jira repository.

Prompt engineering, examples, and basic requirements are all helpful. A throuough review of the code is not necessary at this stage. That will come during `plan-from-spec` (or `plan-from-issue` which does a deeper dive into vetting the issue, identifying it can be reproduced, and planning a solution).

After specs are done, run `/plan-from-spec` (or `/plan-from-issue`) against it.