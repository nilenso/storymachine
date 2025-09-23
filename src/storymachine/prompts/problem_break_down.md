<task>
From the sources below, produce a list of user stories via the `create_stories` tool.
</task>

<sources>
<project_requirements_document>
{prd_content}
</project_requirements_document>
<technical_specification_document>
{tech_spec_content}
</technical_specification_document>
</sources>

<coverage_plan>
- Extract personas that appear in sources.
- Extract all user-facing functional requirements and acceptance tests from sources into a capability list.
- Remove items marked Non-goals or clearly NFR-only.
- Produce one minimal, independent story per capability until all are covered. Split list vs detail, view vs edit, read vs write.
- Include role/permission behaviors where specified (e.g., Admin vs Viewer) inside AC of relevant stories.
- Treat PRD "Acceptance tests" as must-cover behaviors in stories or AC.
- If tech spec adds user-visible behavior not in PRD, include it only if corroborated; otherwise exclude.
</coverage_plan>

<quality_bar>
- Follow Mike Cohn's user story principles and the INVEST heuristic.
- Use real end-user personas that appear in the sources. No system/app/stakeholder actors.
- Scope each story to one user-facing capability with clear business value.
- Do not invent requirements. If something is not supported by the sources, omit it.
- Keep stories independent and non-duplicative. Prefer vertical slices.
</quality_bar>

<acceptance_criteria_rules>
- Use Given/When/Then. Behavior-focused only. No implementation details.
- Metrics only if explicitly in sources. No arbitrary thresholds.
- Cover primary flow and the key edge cases stated in sources.
</acceptance_criteria_rules>

<format>
Return only a `create_stories` tool call with:
- `title`: "As a <persona>, I want <capability> so that <benefit>."
- `acceptance_criteria`: 3–6 items, each a single Given/When/Then line.
No extra commentary or prose outside the tool call.
</format>

<controls>
- Reason strictly from sources; use their terms.
- Prefer smaller vertical slices. Avoid duplicates and overlaps.
- For every story you include, be able to point to the exact source clause internally (do not output references).
- Do not create stories for pure NFRs or release criteria; if an NFR shapes behavior, reflect it as observable behavior only.
- Do not stop generating until every user-facing capability from the coverage_plan is represented by at least one story.
</controls>

<self_reflection>
Internally check before emitting:
1) Coverage: every user-facing capability and acceptance test from sources appears in exactly one story (or a clearly split pair) with no gaps.
2) Persona: each title uses a real end-user persona from sources.
3) Title: states capability and benefit.
4) AC: behavioral, testable, grounded in sources; permissions included where specified.
5) No duplicates/overlaps; split or merge as needed to satisfy INVEST.
Do not output this reflection.
</self_reflection>