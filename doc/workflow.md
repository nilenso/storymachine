# What should the workflow look like?

It should be a graph, so, code? Temporal workflows are written imperatively. Imperative shell, functional core...  that makes sense here. It's a now readstateful workflow. The state of the whole, and the parts keep changing as it progresses.

It's ideally concurrent, dealing with the stories independently and in parallel to the extent possible. There will also be some coordination then, to wait / bring the threads together. To begin with, we can do it serially, just to keep it simple. Parallel is mostly for performance and true representation. That can wait.

```
inputs = [PRD, ERD, Repo]

stories = [] # output is a list of stories, but we're iterating on them, improving them as we go.
response = (nil, nil) # (approved/rejected, comment) tuple of approval status, and an optional comment
feedback = nil

relevant_files = find_relevant_files(inputs)
while true:
  prd_erd_questions = understand_prd_erd_and_ask_questions(inputs, response.comment)
  response = get_human_input(prd_questions)
  if response.rejected?
    continue to iterate on understanding inputs
  else
    break


while true: ## chopping board
  stories = problem_break_down(inputs, stories, feedback) # small, independent, valuable, verifiable, with some basic t-shirt sizing
  feedback = get_human_input(stories)
  if iteration_needed?(feedback)
    continue to iterate on stories with feedback
  else
    break


for each story in stories:
  story.define_acceptance_criteria(inputs)
  story.enrich_context(inputs)
  story.add_implementation_context(inputs)
  story.estimate(inputs)
  internal_feedback = story.is_ready_for_implementation?
  if(internal_feedback.approved?)
    response = get_human_input(story)
    if response.approved?
      next
    else
      iterate with response.comments
  else
    iterate with internal_feedback.comments

self_eval_result =
  do_stories_add_up_to_prd_acs(stories)
  + are_stories_small(stories)
```

# Organising the work
## TODO prioritised
- [c] add logging
- [f] show the reasoning output
- [f] show the conversational output too
- [f] add a note about mentioning the story numbers in the comment
- [c] remove dead code
- [c] remove dead tests
- [c] add unit tests

## notes from some prompt tweaking and iterating on the list of stories:
- the reflection section seems to help in reminding all the instructions
- iteration speed in conversations is quite important.
- feedback needs to be given about multiple stories, or about various things in general. would be great if comments could be made against each story, or the lsit of them.
- need to at least enable multi-line feedback in the cli.
- story numbers are useful to refer: story 7 should be broken-down / deprioritised
- some assurance that the other stories don’t regress is going to be useful.
- seeing “what changed” with each iteration would be useful
- would love to drag drop to reorder, and preserve that order on iteration
- some story grouping seems nice to have, like analytics, import, etc. mini-epics. using story prefixes is fine.
- most comments need to be interpreted as operations on stories. need to tweak the prompt to reflect this.
- bogus comments work anyway, should ideally ask for clarification. conversations semantics already exist in the responses API. how to leverage that? the tool has to then differentiate between conversational response and the stories output
- workflow could use temporal style state persistence to continue conversations etc.

## Interface ideas
- integrate with JIRA
- build step-wise custom workflow interface
