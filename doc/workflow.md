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
