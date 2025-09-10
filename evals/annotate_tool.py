import marimo

__generated_with = "0.15.2"
app = marimo.App(width="full", css_file="molabel-patch.css")


@app.cell(hide_code=True)
def _():
    from pathlib import Path
    import re
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
        Path,
        Story,
        StoryCardEvalItem,
        TechSpec,
        create_story_card_annotation_tool,
        mo,
        pl,
        re,
    )


@app.cell(hide_code=True)
def _(mo):
    form = mo.ui.dictionary(
        {
            "project_id": mo.ui.text(label="Project ID", placeholder="1"),
            "project_name": mo.ui.text(
                label="Project Name", placeholder="Project Alpha"
            ),
            "project_description": mo.ui.text(
                label="Project Description",
                placeholder="A brief description of the project.",
            ),
            "prd_id": mo.ui.text(label="PRD ID", placeholder="101"),
            "prd_path": mo.ui.text(label="PRD File Path", placeholder="docs/prd.md"),
            "tech_spec_id": mo.ui.text(label="Tech Spec ID", placeholder="201"),
            "tech_spec_path": mo.ui.text(
                label="Tech Spec File Path", placeholder="docs/tech_spec.md"
            ),
            "stories_dir": mo.ui.text(
                label="Stories Directory",
                placeholder="stories/",
            ),
        }
    ).form()
    form
    return (form,)


@app.cell(hide_code=True)
def _(Path, form, mo, pl, re):
    def build_backlog_df(
        stories_dir: str | Path,
        *,
        project_id: int | str,
        project_name: str,
        project_description: str,
        prd_id: int | str,
        prd_markdown: str,
        tech_spec_id: int | str,
        tech_spec_markdown: str,
    ) -> pl.DataFrame:
        """Return a Polars DataFrame with one row per story file."""
        stories_dir = Path(stories_dir)
        rows = []

        for fp in sorted(stories_dir.glob("*.md")):
            text = fp.read_text(encoding="utf-8")

            # story_id from filename prefix like "01-..." -> 1
            m_id = re.match(r"^(\d+)", fp.stem)
            story_id = int(m_id.group(1)) if m_id else fp.stem

            # Title: line or fallback to filename slug
            m_title = re.search(r"^Title:\s*(.+)$", text, flags=re.MULTILINE)
            if m_title:
                story_title = m_title.group(1).strip()
            else:
                story_title = fp.stem
                story_title = (
                    re.sub(r"^\d+\-?", "", story_title)
                    .replace("-", " ")
                    .strip()
                    .capitalize()
                )

            # Acceptance Criteria block -> collect criteria lines after the header
            ac_block = ""
            m_ac_start = re.search(
                r"^Acceptance Criteria:\s*$", text, flags=re.MULTILINE
            )
            if m_ac_start:
                start = m_ac_start.end()
                block = text[start:]
                criteria = []
                for line in block.splitlines():
                    if re.match(r"^\s*[-*]\s+", line):
                        # remove the bullet marker and leading whitespace
                        criteria.append(re.sub(r"^\s*[-*]\s+", "", line).strip())
                    elif criteria and line.strip() == "":
                        # allow blank lines, but don't add bullets
                        criteria.append("")
                    elif criteria:
                        break
                cleaned = [c for c in criteria if c.strip() != ""]
                ac_block = "\n".join(cleaned)
            else:
                ac_block = ""

            rows.append(
                {
                    "project_id": project_id,
                    "project_name": project_name,
                    "project_description": project_description,
                    "prd_id": prd_id,
                    "prd_content": prd_markdown,
                    "tech_spec_id": tech_spec_id,
                    "tech_spec_content": tech_spec_markdown,
                    "story_id": story_id,
                    "story_title": story_title,
                    "story_acceptance_criteria": ac_block,
                }
            )

        return pl.DataFrame(rows)

    mo.stop(form.value is None, mo.md("**Fill the form to continue**"))

    _v = form.value

    eval_df = build_backlog_df(
        _v["stories_dir"],
        project_id=_v["project_id"],
        project_name=_v["project_name"],
        project_description=_v["project_description"],
        prd_id=_v["prd_id"],
        prd_markdown=Path(_v["prd_path"]).expanduser().read_text(encoding="utf-8"),
        tech_spec_id=_v["tech_spec_id"],
        tech_spec_markdown=Path(_v["tech_spec_path"])
        .expanduser()
        .read_text(encoding="utf-8"),
    )

    eval_df
    return


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


@app.cell
def _(labeled_df, pl):
    _filtered_df = (
        labeled_df.filter(pl.col("notes") != "")
        .select(["story_title", "story_acceptance_criteria", "label", "notes"])
        .sort(
            [pl.col("label").eq("no").cast(pl.Int8), pl.col("label")],
            descending=[True, False],
        )
    )
    _filtered_df
    return


if __name__ == "__main__":
    app.run()
