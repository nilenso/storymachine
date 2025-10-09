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
<repository_context>
{repo_context}
</repository_context>
</sources>

<breakdown>
- Read the product_requirements_document and the technical_specification_document, and break the problem down into smaller pieces.
- The smaller pieces should be simpler for a developer to deal with, and easy to understand.
- If the problem is CRUD like, create pieces for each command or query
- As much as possible, each piece should also be valuable to the business.
- One piece for one value.
- Each piece should be structured as a User Story, which mentions the <persona>, <capability>, and <benefit>.
- Look at all the stories, and then add relative estimates the stories to one of: [XS]/[S]/[M]/[L], and add that as a prefix.
- Sort the stories in the order that they should be implemented.
</breakdown>

<reflection>
Internally check before emitting:
1) Coverage: every user-facing capability and acceptance test from sources appears in exactly one story (or a clearly split pair) with no gaps.
2) Persona: each title uses a real end-user persona from sources.
3) Title: states capability and benefit.
4) Estimate: each story has a t-shirt size estimate prefixed
5) AC: behavioral, testable, grounded in sources; permissions included where specified.
6) No duplicates/overlaps; split or merge as needed to satisfy INVEST.
Do not output this reflection.
</reflection>
