import marimo

__generated_with = "0.15.2"
app = marimo.App(width="full", css_file="molabel-patch.css")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import polars as pl
    from eval import (
        StoryCardEvalItem,
        StorySetEvalItem,
        Story,
        PRD,
        TechSpec,
    )
    from molabel import SimpleLabel

    def render_story_card_example(example: StoryCardEvalItem):
        """Render a StoryCardEvalItem example for annotation."""
        return example["item"]._repr_html_()

    def render_story_set_example(example: StorySetEvalItem):
        """Render a StorySetEvalItem example for annotation."""
        return example["item"]._repr_html_()

    def create_story_card_annotation_tool(examples: list[StoryCardEvalItem]):
        """Create an annotation tool for StoryCardEvalItem examples."""
        widget = mo.ui.anywidget(
            SimpleLabel(
                examples=[{"item": _} for _ in examples],
                render=render_story_card_example,
                notes=True,
            )
        )
        return widget

    def create_story_set_annotation_tool(examples: list[StorySetEvalItem]):
        """Create an annotation tool for StorySetEvalItem examples."""
        widget = mo.ui.anywidget(
            SimpleLabel(
                examples=[{"item": _} for _ in examples],
                render=render_story_set_example,
                notes=True,
            )
        )
        return widget

    return (
        PRD,
        Story,
        StoryCardEvalItem,
        TechSpec,
        create_story_card_annotation_tool,
        mo,
        pl,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## Expected Eval Format

    |project_id|project_name|project_description|prd_id|prd_content|tech_spec_id|tech_spec_content|story_id|story_title|story_acceptance_criteria|
    |---|---|---|---|---|---|---|---|---|---|
    |1|Project Alpha|A Project Description.|101|This PRD describes the alpha features of Project Alpha.|201|The tech spec for Project Alpha includes system architecture and API details.|1001|As a [user persona], I want to [perform an action], so that [achieve a goal/reason]|- Given [action], when [condition], then [outcome]<br>-  Given [another action], when [condition], then [outcome]|
    |2|Project Beta|B Project Description.|102|This PRD outlines the beta features of Project Beta.|202|The tech spec for Project Beta covers database schema and security protocols.|1002|As an [admin persona], I want to [manage user roles], so that [ensure proper access control]|- Given [admin action], when [condition], then [outcome]<br>-  Given [another admin action], when [condition], then [outcome]|
    """
    )
    return


@app.cell
def _(mo):
    eval_file = mo.ui.file(filetypes=[".csv"], kind="area", label="Upload Labeled CSV")
    eval_file
    return (eval_file,)


@app.cell
def _(eval_file, mo, pl):
    mo.stop(eval_file.name() is None, mo.md("**Upload an eval dataset to continue**"))

    df = pl.read_csv(eval_file.name())
    return (df,)


@app.cell
def _(
    PRD,
    Story,
    StoryCardEvalItem,
    TechSpec,
    create_story_card_annotation_tool,
    df,
):
    # Parse examples from df
    examples = []
    for _row in df.iter_rows(named=True):
        _prd_doc = PRD(
            id=_row["prd_id"],
            project_id=_row["project_id"],
            content=_row["prd_content"],
        )
        _tech_doc = TechSpec(
            id=_row["tech_spec_id"],
            project_id=_row["project_id"],
            content=_row["tech_spec_content"],
        )
        _story = Story(
            id=_row["story_id"],
            project_id=_row["project_id"],
            title=_row["story_title"],
            acceptance_criteria=_row["story_acceptance_criteria"].split("\n"),
        )
        examples.append(
            StoryCardEvalItem(
                eval_criteria="Is this a good User Story?",
                project_id=_row["project_id"],
                prd=_prd_doc,
                tech_spec=_tech_doc,
                story=_story,
            )
        )

    widget = create_story_card_annotation_tool(examples=examples)
    widget
    return (widget,)


@app.cell
def _(df, pl, widget):
    annotations = widget.get_annotations()

    labeled_examples = []

    for annotation in annotations:
        index = annotation["index"]
        label = annotation.get("_label")
        notes = annotation.get("_notes", "")

        # Get the corresponding row from original dataframe
        row = df.row(index, named=True)

        # Create new row with label information
        labeled_row = {
            **row,  # Include all original columns
            "label": label,
            "notes": notes,
            "annotation_timestamp": annotation.get("_timestamp", ""),
        }
        labeled_examples.append(labeled_row)

    # Create new dataframe with labels
    labeled_df = pl.DataFrame(labeled_examples)
    return (labeled_df,)


@app.cell
def _(labeled_df):
    labeled_df
    return


if __name__ == "__main__":
    app.run()
