Based on the feedback below, revise the previous user stories and produce an improved list via the `create_stories` tool.

<operations>
These are the typical operations on the stories while iterating on them, and the usual reasons for them.. Interpret the feedback below in terms of these operations where possible.

- Break down further: usually because it's a large piece, or has multiple values associated with it
- Merge stories: they're too small, or create the same value
- Prioritise, and reprioritise: based on business value or dependencies
- Change wording: usually to convey the business value better
- Remove: not relevant, or duplicate
- Add missing stories: somehow missed it in the breakdown
- Group them with a prefix: to categorise
</operations>

<feedback>
{comments}
</feedback>

<breakdown>
- Breakdown the problem as per the feedback.
- As much as possible, each piece should also be valuable to the business. One piece for one value.
- Each piece should be structured as a User Story, which mentions the <persona>, <capability>, and <benefit>.
- Optionally, use a <group> prefix to categorise stories.
- Look at all the stories, and then add relative estimates the stories to one of the prefixes: [XS]/[S]/[M]/[L]. Estimates should be based on the amount of time it would take to implement it from beginning to production, and to ensure everything works correctly.
- Sort the stories according to feedback, or in the order that they should be implemented.
</breakdown>

<reflection>
Internally check before emitting:
1) Coverage: every user-facing capability and acceptance test from sources appears in exactly one story (or a clearly split pair) with no gaps.
2) Persona: each title uses a real end-user persona from sources.
3) Title: states capability and benefit.
4) Estimate: each story has a t-shirt size estimate prefixed
5) AC: behavioral, testable, grounded in sources; permissions included where specified.
6) No duplicates/overlaps; split or merge as needed to satisfy INVEST.
7) the user feedback is addressed
Do not output this reflection.
</reflection>
